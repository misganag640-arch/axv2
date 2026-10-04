from datetime import date

from dateutil.relativedelta import relativedelta

from .models import (
    PersonPlan,
    Payment,
    Notification,
    DeletedScheduledPayment,
)

# ============================================================
# PAYMENT FREQUENCY
# ============================================================

def months(freq):
    frequencies = {
        "monthly": 1,
        "2months": 2,
        "3months": 3,
    }

    return frequencies.get(freq)


# ============================================================
# REFRESH PAYMENTS
# ============================================================

def refresh_payments():

    today = date.today()

    # --------------------------------------------------------
    # Change normal unpaid payments to overdue
    # --------------------------------------------------------

    Payment.objects.filter(
        status="unpaid",
        due_date__lt=today
    ).exclude(
        plan__frequency="deposit"
    ).update(
        status="overdue"
    )

    # --------------------------------------------------------
    # Check active payment plans
    # --------------------------------------------------------

    person_plans = PersonPlan.objects.select_related(
        "person",
        "plan"
    ).filter(
        active=True,
        person__status="active"
    )

    for pp in person_plans:

        # Deposit / on-demand plans do not have a schedule.
        if pp.plan.frequency == "deposit":
            continue

        step = months(pp.plan.frequency)

        if step is None:
            continue

        # ----------------------------------------------------
        # Find the latest existing payment for this plan.
        #
        # We do NOT go back to pp.start_date every time.
        # This prevents deliberately deleted old payments
        # from being recreated.
        # ----------------------------------------------------

        latest_payment = (
            Payment.objects
            .filter(
                person=pp.person,
                plan=pp.plan,
            )
            .order_by("-due_date")
            .first()
        )

        if latest_payment is None:
            # The first payment should normally have been
            # created when the plan was assigned.
            # This is only a safety fallback.
            d = pp.start_date
        else:
            d = latest_payment.due_date + relativedelta(
                months=step
            )

        # ----------------------------------------------------
        # Generate only NEW future/current payments.
        # ----------------------------------------------------

        while d <= today:

            # Do not recreate a payment that was intentionally deleted.
            if DeletedScheduledPayment.objects.filter(
                person=pp.person,
                plan=pp.plan,
                due_date=d,
            ).exists():
                d = d + relativedelta(months=step)
                continue

            payment, created = Payment.objects.get_or_create(
                person=pp.person,
                plan=pp.plan,
                due_date=d,
                defaults={
                    "amount": pp.plan.amount,
                    "status": "unpaid",
                }
            )

            # ------------------------------------------------
            # Mark newly created old payment as overdue
            # ------------------------------------------------

            if created and d < today:

                payment.status = "overdue"

                payment.save(
                    update_fields=["status"]
                )

            # ------------------------------------------------
            # Create overdue notification
            # ------------------------------------------------

            if (
                payment.status in ("unpaid", "overdue")
                and d < today
                and not Notification.objects.filter(
                    payment=payment,
                    notification_type="overdue"
                ).exists()
            ):

                Notification.objects.create(
                    person=pp.person,
                    payment=payment,
                    notification_type="overdue",
                    title="Payment overdue",
                    message=(
                        f"{pp.person.full_name} "
                        f"should have paid "
                        f"{payment.amount} "
                        f"by {d} but has not paid."
                    )
                )

            d = d + relativedelta(
                months=step
            )
def calculate_daily_interest():
    from decimal import Decimal
    from django.db.models import Sum
    from .models import (
        Person,
        Payment,
        MemberTransaction,
        InterestRate,
    )

    today = date.today()

    # Get the latest active interest rate that is already effective.
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
        return

    annual_rate = Decimal(str(interest_rate.rate))

    for person in Person.objects.all():

        # Only PERSONAL paid payment plans count toward
        # the member's personal balance.
        personal_payments = (
            Payment.objects
            .filter(
                person=person,
                status="paid",
                plan__plan_type="personal",
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Deposits + savings
        deposits_and_savings = (
            MemberTransaction.objects
            .filter(
                person=person,
                transaction_type__in=["deposit", "saving"],
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Previously earned interest
        previous_interest = (
            MemberTransaction.objects
            .filter(
                person=person,
                transaction_type="interest",
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Withdrawals
        withdrawals = (
            MemberTransaction.objects
            .filter(
                person=person,
                transaction_type="withdrawal",
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Current personal balance before today's interest
        balance = (
            personal_payments
            + deposits_and_savings
            + previous_interest
            - withdrawals
        )

        # No interest when the balance is zero or negative.
        if balance <= Decimal("0.00"):
            continue

        # Annual rate -> daily rate
        daily_interest = (
            balance
            * annual_rate
            / Decimal("100")
            / Decimal("365")
        )

        daily_interest = daily_interest.quantize(
            Decimal("0.000001")
        )

        if daily_interest <= Decimal("0.000000"):
            continue

        # Prevent duplicate interest for the same member/day.
        MemberTransaction.objects.get_or_create(
            person=person,
            transaction_type="interest",
            transaction_date=today,
            defaults={
                "amount": daily_interest,
                "reference_number": f"INTEREST-{today}",
                "notes": (
                    f"Automatic daily interest at "
                    f"{annual_rate}% annual rate."
                ),
            },
        )