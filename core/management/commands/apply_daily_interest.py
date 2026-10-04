from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from core.models import (
    Person,
    Payment,
    MemberTransaction,
    InterestRate,
)


class Command(BaseCommand):
    help = "Apply daily interest to members' positive personal balances."

    def handle(self, *args, **options):
        today = date.today()

        interest_rate = (
            InterestRate.objects
            .filter(
                active=True,
                effective_date__lte=today,
            )
            .order_by("-effective_date", "-id")
            .first()
        )

        if not interest_rate:
            self.stdout.write(
                self.style.WARNING(
                    "No active interest rate has been configured."
                )
            )
            return

        annual_rate = Decimal(interest_rate.rate)

        if annual_rate <= Decimal("0"):
            self.stdout.write(
                self.style.WARNING(
                    f"Interest rate is {annual_rate}%. No interest applied."
                )
            )
            return

        daily_rate = (
            annual_rate
            / Decimal("100")
            / Decimal("365")
        )

        processed = 0
        skipped = 0
        total_interest = Decimal("0.000000")

        for person in Person.objects.all():

            # Prevent duplicate interest for the same person and date.
            already_exists = MemberTransaction.objects.filter(
                person=person,
                transaction_type="interest",
                transaction_date=today,
            ).exists()

            if already_exists:
                skipped += 1
                continue

            with transaction.atomic():

                # Personal payments only.
                personal_payments = (
                    Payment.objects
                    .filter(
                        person=person,
                        status="paid",
                        plan__plan_type="personal",
                        payment_date__lte=today,
                    )
                    .aggregate(total=Sum("amount"))["total"]
                    or Decimal("0.000000")
                )

                member_transactions = MemberTransaction.objects.filter(
                    person=person,
                    transaction_date__lte=today,
                )

                deposits = (
                    member_transactions
                    .filter(transaction_type="deposit")
                    .aggregate(total=Sum("amount"))["total"]
                    or Decimal("0.000000")
                )

                savings = (
                    member_transactions
                    .filter(transaction_type="saving")
                    .aggregate(total=Sum("amount"))["total"]
                    or Decimal("0.000000")
                )

                interest_already_earned = (
                    member_transactions
                    .filter(transaction_type="interest")
                    .aggregate(total=Sum("amount"))["total"]
                    or Decimal("0.000000")
                )

                withdrawals = (
                    member_transactions
                    .filter(transaction_type="withdrawal")
                    .aggregate(total=Sum("amount"))["total"]
                    or Decimal("0.000000")
                )

                balance = (
                    personal_payments
                    + deposits
                    + savings
                    + interest_already_earned
                    - withdrawals
                )

                # No interest on zero or negative balance.
                if balance <= Decimal("0"):
                    skipped += 1
                    continue

                daily_interest = balance * daily_rate

                # Keep six decimal places internally.
                daily_interest = daily_interest.quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_DOWN,
                )

                # Very tiny amounts should not create meaningless records.
                if daily_interest <= Decimal("0"):
                    skipped += 1
                    continue

                MemberTransaction.objects.create(
                    person=person,
                    transaction_type="interest",
                    amount=daily_interest,
                    transaction_date=today,
                    reference_number=f"INTEREST-{today.isoformat()}",
                    notes=(
                        f"Daily interest at {annual_rate}% per year. "
                        f"Calculated on personal balance of "
                        f"{balance:.6f}."
                    ),
                )

                processed += 1
                total_interest += daily_interest

        self.stdout.write(
            self.style.SUCCESS(
                f"Daily interest completed. "
                f"Members credited: {processed}. "
                f"Skipped: {skipped}. "
                f"Total interest: {total_interest:.6f}"
            )
        )