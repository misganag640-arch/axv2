from datetime import date
from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
# ============================================================
# PERSON
# ============================================================
def get_available_balance():

    total_paid = Payment.objects.filter(
        status="paid"
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    total_expenses = Expense.objects.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    total_borrowed = Borrow.objects.aggregate(
        total=Sum("principal_amount")
    )["total"] or Decimal("0.00")

    total_repaid = BorrowRepayment.objects.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    total_money_in = FinancialAdjustment.objects.filter(
        adjustment_type="money_in"
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    total_money_out = FinancialAdjustment.objects.filter(
        adjustment_type="money_out"
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    return (
        total_paid
        + total_money_in
        + total_repaid
        - total_expenses
        - total_borrowed
        - total_money_out
    )
class Person(models.Model):

    person_id = models.CharField(
        max_length=10,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=30,
        blank=False
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.CharField(
        max_length=255,
        blank=True
    )

    gender = models.CharField(
        max_length=20,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        blank=False
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    employment_status = models.CharField(
        max_length=30,
        choices=[
            ("employed", "Employed"),
            ("self_employed", "Self-employed"),
            ("student", "Student"),
            ("unemployed", "Unemployed"),
            ("other", "Other"),
        ],
        blank=False
    )

    marital_status = models.CharField(
        max_length=20,
        choices=[
            ("single", "Single"),
            ("married", "Married"),
            ("divorced", "Divorced"),
        ],
        default="single"
    )

    spouse_full_name = models.CharField(
        max_length=200,
        blank=True
    )

    spouse_phone = models.CharField(
        max_length=30,
        blank=True
    )

    registration_date = models.DateField(
        default=date.today
    )

    national_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True
    )

    # --------------------------------------------------------
    # MEMBER PHOTOS
    # --------------------------------------------------------

    photo = models.ImageField(
        upload_to="people/photos/",
        blank=True
    )

    national_id_photo = models.ImageField(
        upload_to="people/national_ids/",
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
        ],
        default="active"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.person_id} - {self.full_name}"

    def get_personal_balance(self):
        from django.db.models import Sum

        personal_payment_total = (
            self.payments
            .filter(
                status="paid",
                plan__plan_type="personal",
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.000000")
        )

        transactions = self.member_transactions.all()

        deposits = (
            transactions
            .filter(transaction_type="deposit")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.000000")
        )

        savings = (
            transactions
            .filter(transaction_type="saving")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.000000")
        )

        interest = (
            transactions
            .filter(transaction_type="interest")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.000000")
        )

        withdrawals = (
            transactions
            .filter(transaction_type="withdrawal")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.000000")
        )

        return (
            personal_payment_total
            + deposits
            + savings
            + interest
            - withdrawals
        )
    # ============================================================
# MEMBER DOCUMENTS
# ============================================================

class PersonDocument(models.Model):

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    title = models.CharField(
        max_length=150,
        blank=True
    )

    image = models.ImageField(
        upload_to="people/documents/",
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        if self.title:
            return f"{self.person.full_name} - {self.title}"

        return f"{self.person.full_name} - Document"
  # ============================================================
# MEMBER TRANSACTIONS
# ============================================================

class MemberTransaction(models.Model):

    TRANSACTION_TYPES = [
    ("deposit", "Deposit"),
    ("withdrawal", "Withdrawal"),
    ("saving", "Saving"),
      ]

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="member_transactions"
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )

    amount = models.DecimalField(
    max_digits=14,
    decimal_places=6,
     )

    transaction_date = models.DateField(
        default=date.today
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-transaction_date",
            "-created_at"
        ]
        constraints = [
    models.UniqueConstraint(
        fields=["person", "transaction_type", "transaction_date"],
        condition=models.Q(transaction_type="interest"),
        name="unique_daily_interest_per_person",
    ),
  ]

    def clean(self):
        super().clean()

        if self.amount <= Decimal("0.00"):
            raise ValidationError({
                "amount": "Amount must be greater than zero."
            })

                # ----------------------------------------------------
        # WITHDRAWAL BALANCE CHECK
        # ----------------------------------------------------
        # A member can never withdraw more than their
        # actual personal balance.
        #
        # Personal balance =
        # confirmed personal payments
        # + deposits
        # + savings
        # + earned interest
        # - previous withdrawals
        #
        # Wabii payments and company Financial Adjustments
        # are NOT part of the member's withdrawal balance.
        # ----------------------------------------------------

        if self.transaction_type == "withdrawal":

            personal_payments = (
                Payment.objects
                .filter(
                    person=self.person,
                    status="paid",
                    plan__plan_type="personal",
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            transactions = (
                MemberTransaction.objects
                .filter(
                    person=self.person
                )
            )

            # When editing a withdrawal, don't count
            # the withdrawal being edited.
            if self.pk:
                transactions = transactions.exclude(
                    pk=self.pk
                )

            deposits = (
                transactions
                .filter(
                    transaction_type="deposit"
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            savings = (
                transactions
                .filter(
                    transaction_type="saving"
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            interest = (
                transactions
                .filter(
                    transaction_type="interest"
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            previous_withdrawals = (
                transactions
                .filter(
                    transaction_type="withdrawal"
                )
                .aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            )

            available_balance = (
                personal_payments
                + deposits
                + savings
                + interest
                - previous_withdrawals
            )

            # Never allow a negative balance.
            if available_balance < Decimal("0.00"):
                available_balance = Decimal("0.00")

            if self.amount > available_balance:
                raise ValidationError({
                    "amount": (
                        f"Insufficient member balance. "
                        f"Available balance is "
                        f"{available_balance:.2f}. "
                        f"You cannot withdraw "
                        f"{self.amount:.2f}."
                    )
                })

    def __str__(self):
        return (
            f"{self.person.full_name} - "
            f"{self.get_transaction_type_display()} - "
            f"{self.amount}"
        )
# ============================================================
# PAYMENT PLAN
# ============================================================

# ============================================================
# PAYMENT PLAN
# ============================================================

class PaymentPlan(models.Model):

    PLAN_TYPES = [
        ("personal", "Personal Payment Plan"),
        ("wabii", "Wabii Payment Plan"),
    ]

    FREQUENCIES = [
        (
            "monthly",
            "Monthly"
        ),
        (
            "2months",
            "Every 2 Months"
        ),
        (
            "3months",
            "Every 3 Months"
        ),
        (
            "deposit",
            "Deposit / On-Demand (No Schedule)"
        ),
    ]

    name = models.CharField(
        max_length=100
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        default="personal"
    )

    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCIES
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.name} - {self.amount}"
# ============================================================
# PERSON PAYMENT PLAN
# ============================================================

class PersonPlan(models.Model):

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="assigned_plans"
    )

    plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.PROTECT
    )

    start_date = models.DateField(
        default=date.today
    )

    active = models.BooleanField(
        default=True
    )

    class Meta:

        unique_together = [
            (
                "person",
                "plan",
                "start_date"
            )
        ]


# ============================================================
# PAYMENT
# ============================================================

class Payment(models.Model):

    STATUS = [

        (
            "unpaid",
            "Unpaid"
        ),

        (
            "paid",
            "Paid"
        ),

        (
            "overdue",
            "Overdue"
        ),

        (
            "rejected",
            "Rejected"
        ),
    ]

    METHOD = [

        (
            "cash",
            "Cash"
        ),

        (
            "bank",
            "Bank"
        ),

        (
            "telebirr",
            "Telebirr"
        ),

        (
            "other",
            "Other"
        ),
    ]

    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.PROTECT
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    due_date = models.DateField()

    payment_date = models.DateField(
        null=True,
        blank=True
    )

    payment_method = models.CharField(
        max_length=20,
        choices=METHOD,
        default="bank"
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="unpaid"
    )

    notes = models.TextField(
        blank=True
    )

    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "due_date",
            "person__full_name"
        ]

        unique_together = [
            (
                "person",
                "plan",
                "due_date"
            )
        ]

    def __str__(self):

        return (
            f"{self.person} - "
            f"{self.amount} - "
            f"{self.status}"
        )
    # ============================================================
# DELETED SCHEDULED PAYMENT
# ============================================================

class DeletedScheduledPayment(models.Model):

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="deleted_scheduled_payments"
    )

    plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.CASCADE,
        related_name="deleted_scheduled_payments"
    )

    due_date = models.DateField()

    deleted_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["person", "plan", "due_date"],
                name="unique_deleted_scheduled_payment"
            )
        ]

    def __str__(self):
        return (
            f"{self.person} - "
            f"{self.plan} - "
            f"{self.due_date}"
        )


# ============================================================
# NOTIFICATIONS
# ============================================================

class Notification(models.Model):

    TYPE = [

        (
            "due",
            "Payment Due"
        ),

        (
            "overdue",
            "Overdue"
        ),

        (
            "paid",
            "Payment Confirmed"
        ),

        (
            "system",
            "System"
        ),
    ]

    CHANNEL = [

        (
            "in_app",
            "In App"
        ),

        (
            "sms",
            "SMS"
        ),

        (
            "email",
            "Email"
        ),
    ]

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE,
        default="system"
    )

    channel = models.CharField(
        max_length=20,
        choices=CHANNEL,
        default="in_app"
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField()

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]


# ============================================================
# ACTIVITY HISTORY
# ============================================================

class ActivityHistory(models.Model):

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="history"
    )

    action = models.CharField(
        max_length=100
    )

    description = models.TextField(
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]
        # ============================================================
# EXPENSE MANAGEMENT
# ============================================================

# ============================================================
# EXPENSE MANAGEMENT
# ============================================================

from django.core.exceptions import ValidationError
from django.db.models import Sum

# ============================================================
# EXPENSE MANAGEMENT
# ============================================================
class Expense(models.Model):

    EXPENSE_TYPES = [
        ("purchase", "Goods Purchase"),
        ("other", "Other Expense"),
    ]

    name = models.CharField(
        max_length=150
    )

    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPES,
        default="other"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    expense_date = models.DateField()

    reason = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-expense_date",
            "-created_at"
        ]

    def clean(self):
        super().clean()

        if self.amount <= Decimal("0.00"):
            raise ValidationError({
                "amount": "Expense amount must be greater than zero."
            })

        # Money already received from paid deposits
        total_paid = (
            Payment.objects
            .filter(status="paid")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Money returned from borrowers
        total_repaid = (
            BorrowRepayment.objects
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Money In adjustments
        total_money_in = (
            FinancialAdjustment.objects
            .filter(adjustment_type="money_in")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Money Out adjustments
        total_money_out = (
            FinancialAdjustment.objects
            .filter(adjustment_type="money_out")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Existing expenses, excluding this one when editing
        expenses = Expense.objects.all()

        if self.pk:
            expenses = expenses.exclude(pk=self.pk)

        total_expenses = (
            expenses
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Money currently given to borrowers
        total_borrowed = (
            Borrow.objects
            .aggregate(total=Sum("principal_amount"))["total"]
            or Decimal("0.00")
        )

        # Calculate the SAME balance shown on dashboard
        available_balance = (
            total_paid
            + total_money_in
            + total_repaid
            - total_expenses
            - total_borrowed
            - total_money_out
        )

        # Do not allow expense to make balance negative
        if self.amount > available_balance:
            raise ValidationError({
                "amount": (
                    f"Insufficient balance. "
                    f"Available balance is {available_balance}. "
                    f"You cannot record an expense of {self.amount}."
                )
            })

    def __str__(self):
        return f"{self.name} - {self.amount} - {self.expense_type}"
# ============================================================
# BORROW MANAGEMENT
# ============================================================

# ============================================================
# BORROW MANAGEMENT
# ============================================================

class Borrow(models.Model):

    STATUS = [
        ("active", "Active"),
        ("paid", "Fully Paid"),
        ("overdue", "Overdue"),
    ]

    DURATION_TYPES = [
        ("months", "Months"),
        ("years", "Years"),
    ]

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank", "Bank"),
        ("telebirr", "Telebirr"),
        ("other", "Other"),
    ]

    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="borrows"
    )

    principal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Example: 17 means 17% per year"
    )

    duration_type = models.CharField(
        max_length=10,
        choices=DURATION_TYPES,
        default="months"
    )

    duration = models.PositiveIntegerField()

    borrow_date = models.DateField(
        default=date.today
    )

    due_date = models.DateField(
        editable=False
    )

    interest_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    total_repayment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # Remaining money the borrower still owes
    remaining_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False
    )

    # Payment method used when giving the borrowed money
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="bank"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    notes = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-borrow_date"
        ]
    # ========================================================
    # VALIDATION
    # ========================================================

    def clean(self):

        super().clean()

        if not self.person_id:
            return

        # One person cannot have more than one active borrow
        active_borrows = Borrow.objects.filter(
            person=self.person,
            status="active"
        )

        if self.pk:
            active_borrows = active_borrows.exclude(
                pk=self.pk
            )

        if active_borrows.exists():
            raise ValidationError({
                "person": (
                    f"{self.person.full_name} already has "
                    "an active borrow. They must finish "
                    "the current borrow first."
                )
            })

        # Check available money
                # --------------------------------------------------------
        # CHECK AVAILABLE MONEY
        # USE THE SAME TOTAL BALANCE AS THE DASHBOARD
        # --------------------------------------------------------

                # --------------------------------------------------------
        # CHECK AVAILABLE MONEY
        # USE THE SAME BALANCE AS THE MAIN DASHBOARD
        # --------------------------------------------------------

        total_paid = (
            Payment.objects
            .filter(status="paid")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_member_deposits = (
            MemberTransaction.objects
            .filter(transaction_type="deposit")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_member_savings = (
            MemberTransaction.objects
            .filter(transaction_type="saving")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_member_withdrawals = (
            MemberTransaction.objects
            .filter(transaction_type="withdrawal")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_expenses = (
            Expense.objects
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        total_repaid = (
            BorrowRepayment.objects
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # Existing borrows, excluding this borrow when editing
        borrows = Borrow.objects.all()

        if self.pk:
            borrows = borrows.exclude(pk=self.pk)

        total_borrowed = (
            borrows
            .aggregate(total=Sum("principal_amount"))["total"]
            or Decimal("0.00")
        )

        # SAME calculation used by dashboard
        available_balance = (
            total_paid
            + total_member_deposits
            + total_member_savings
            + total_repaid
            - total_member_withdrawals
            - total_expenses
            - total_borrowed
        )

        if self.principal_amount > available_balance:
            raise ValidationError({
                "principal_amount": (
                    f"Insufficient balance. "
                    f"Available money is {available_balance}. "
                    f"You cannot borrow "
                    f"{self.principal_amount}."
                )
            })

        # Duration validation
        if self.duration_type == "months":

            if self.duration < 1 or self.duration > 10:
                raise ValidationError({
                    "duration": (
                        "For months, duration must "
                        "be between 1 and 10."
                    )
                })

        elif self.duration_type == "years":

            if self.duration < 1 or self.duration > 4:
                raise ValidationError({
                    "duration": (
                        "For years, duration must "
                        "be between 1 and 4."
                    )
                })


    # ========================================================
    # SAVE AND CALCULATE
    # ========================================================

    def save(self, *args, **kwargs):

        from dateutil.relativedelta import relativedelta

        # Calculate due date FIRST
        if self.duration_type == "months":

            self.due_date = (
                self.borrow_date
                + relativedelta(
                    months=int(self.duration)
                )
            )

            duration_in_years = (
                Decimal(str(self.duration))
                / Decimal("12")
            )

        elif self.duration_type == "years":

            self.due_date = (
                self.borrow_date
                + relativedelta(
                    years=int(self.duration)
                )
            )

            duration_in_years = Decimal(
                str(self.duration)
            )

        else:
            duration_in_years = Decimal("0")

        # Convert values to Decimal
        principal = Decimal(
            str(self.principal_amount)
        )

        rate = Decimal(
            str(self.interest_rate)
        )

        # Calculate interest
        self.interest_amount = (
            principal
            * rate
            * duration_in_years
            / Decimal("100")
        ).quantize(
            Decimal("0.01")
        )

        # Calculate total repayment
        self.total_repayment = (
            principal
            + self.interest_amount
        ).quantize(
            Decimal("0.01")
        )

        # Set remaining balance only for new borrow
        if not self.pk:
            self.remaining_balance = (
                self.total_repayment
            )

        # Save
        super().save(
            *args,
            **kwargs
        )


    def __str__(self):

        return (
            f"{self.person.full_name} - "
            f"Borrowed {self.principal_amount}"
        )
    
class BorrowRepayment(models.Model):

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank", "Bank"),
        ("telebirr", "Telebirr"),
        ("other", "Other"),
    ]

    borrow = models.ForeignKey(
        Borrow,
        on_delete=models.CASCADE,
        related_name="repayments"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_date = models.DateField(
        default=date.today
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="bank"
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    received_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-payment_date"
        ]

    # ========================================================
    # CHECK PAYMENT
    # ========================================================

    def clean(self):

        super().clean()

        if not self.borrow_id:
            return

        if self.borrow.status == "paid":

            raise ValidationError({
                "borrow": (
                    "This borrow is already fully paid."
                )
            })

        if self.amount <= Decimal("0.00"):

            raise ValidationError({
                "amount": (
                    "Payment amount must be greater than zero."
                )
            })

        if self.amount > self.borrow.remaining_balance:

            raise ValidationError({
                "amount": (
                    f"Payment cannot be greater than "
                    f"the remaining balance "
                    f"{self.borrow.remaining_balance}."
                )
            })

    # ========================================================
    # SAVE REPAYMENT
    # ========================================================

    def save(self, *args, **kwargs):

        self.full_clean()

        # Prevent duplicate subtraction when editing
        if not self.pk:

            self.borrow.remaining_balance -= self.amount

            # Fully paid
            if self.borrow.remaining_balance <= Decimal("0.00"):

                self.borrow.remaining_balance = Decimal(
                    "0.00"
                )

                self.borrow.status = "paid"

            self.borrow.save(
                update_fields=[
                    "remaining_balance",
                    "status",
                ]
            )

        super().save(
            *args,
            **kwargs
        )

    def __str__(self):

        return (
            f"{self.borrow.person.full_name} - "
            f"Paid {self.amount}"
        ) # ============================================================
# LOAN MANAGEMENT
# ============================================================

class Loan(models.Model):

    STATUS = [
        ("active", "Active"),
        ("paid", "Fully Paid"),
        ("overdue", "Overdue"),
    ]

    DURATION_TYPES = [
        ("months", "Months"),
        ("years", "Years"),
    ]

    person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="loans",
        help_text="Borrower must be a fully registered person"
    )

    principal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount of money given to the borrower"
    )

    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual interest rate. Example: 17 means 17%"
    )

    duration_type = models.CharField(
        max_length=10,
        choices=DURATION_TYPES,
        default="months"
    )

    duration = models.PositiveIntegerField(
        help_text="Months: 1-10. Years: 1-4."
    )

    loan_date = models.DateField(
        default=date.today
    )

    due_date = models.DateField(
        editable=False
    )

    interest_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )

    total_repayment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="active"
    )

    notes = models.TextField(
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-loan_date"
        ]

    def clean(self):
        super().clean()

        # --------------------------------------------------------
        # BORROWER MUST BE FULLY REGISTERED
        # --------------------------------------------------------

        if not self.person:
            raise ValidationError({
                "person": "A registered person must be selected."
            })

        if (
            not self.person.person_id
            or not self.person.phone
            or not self.person.email
        ):
            raise ValidationError({
                "person": (
                    f"The borrower ({self.person.full_name}) must have "
                    "a valid ID, phone number, and email registered "
                    "before taking a loan."
                )
            })

        # --------------------------------------------------------
        # PRINCIPAL AMOUNT
        # --------------------------------------------------------

        if self.principal_amount <= 0:
            raise ValidationError({
                "principal_amount": (
                    "Borrowed amount must be greater than zero."
                )
            })

        # --------------------------------------------------------
        # INTEREST RATE
        # --------------------------------------------------------

        if self.interest_rate < 0:
            raise ValidationError({
                "interest_rate": (
                    "Interest rate cannot be negative."
                )
            })

        # --------------------------------------------------------
        # DURATION
        # --------------------------------------------------------

        if self.duration_type == "months":

            if self.duration < 1 or self.duration > 10:
                raise ValidationError({
                    "duration": (
                        "For Months, duration must be between 1 and 10."
                    )
                })

        elif self.duration_type == "years":

            if self.duration < 1 or self.duration > 4:
                raise ValidationError({
                    "duration": (
                        "For Years, duration must be between 1 and 4."
                    )
                })

    def save(self, *args, **kwargs):

        self.full_clean()

        # --------------------------------------------------------
        # CALCULATE DURATION IN YEARS
        # --------------------------------------------------------

        if self.duration_type == "months":
            duration_in_years = (
                Decimal(self.duration) / Decimal("12")
            )
        else:
            duration_in_years = Decimal(self.duration)

        # --------------------------------------------------------
        # ANNUAL SIMPLE INTEREST
        #
        # Example:
        # 100,000 × 17% × 1 year
        # = 17,000 interest
        #
        # Total = 117,000
        # --------------------------------------------------------

        self.interest_amount = (
            self.principal_amount
            * self.interest_rate
            / Decimal("100")
            * duration_in_years
        ).quantize(Decimal("0.01"))

        self.total_repayment = (
            self.principal_amount
            + self.interest_amount
        ).quantize(Decimal("0.01"))

        # --------------------------------------------------------
        # CALCULATE DUE DATE
        # --------------------------------------------------------

        from dateutil.relativedelta import relativedelta

        if self.duration_type == "months":

            self.due_date = (
                self.loan_date
                + relativedelta(
                    months=self.duration
                )
            )

        else:

            self.due_date = (
                self.loan_date
                + relativedelta(
                    years=self.duration
                )
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.person.full_name} - "
            f"Loan {self.principal_amount}"
        )

# ============================================================
# LOAN REPAYMENT MANAGEMENT
# ============================================================

class LoanRepayment(models.Model):

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank", "Bank"),
        ("telebirr", "Telebirr"),
        ("other", "Other"),
    ]

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name="repayments"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    payment_date = models.DateField(
        default=date.today
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default="cash"
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-payment_date",
            "-created_at"
        ]

    def clean(self):
        super().clean()

        if self.amount <= 0:
            raise ValidationError({
                "amount": "Repayment amount must be greater than zero."
            })

        already_paid = (
            self.loan.repayments
            .exclude(pk=self.pk)
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        remaining_balance = (
            self.loan.total_repayment
            - already_paid
        )

        if self.amount > remaining_balance:
            raise ValidationError({
                "amount": (
                    f"Payment cannot be more than the "
                    f"remaining balance: {remaining_balance}"
                )
            })

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

        total_paid = (
            self.loan.repayments
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        if total_paid >= self.loan.total_repayment:

            self.loan.status = "paid"

        else:

            self.loan.status = "active"

        self.loan.save(
            update_fields=["status"]
        )

    def __str__(self):
        return (
            f"{self.loan.person.full_name} - "
            f"Paid {self.amount}"
        )
# ============================================================
# GENERAL FINANCIAL MANAGEMENT
# ============================================================

class FinancialAdjustment(models.Model):

    TYPE_CHOICES = [
        ("money_in", "Money In"),
        ("money_out", "Money Out"),
    ]

    CATEGORY_CHOICES = [
        ("company_loan", "Company Loan"),
        ("other_income", "Other Income"),
        ("other_expense", "Other Expense"),
        ("capital", "Capital"),
        ("correction", "Balance Correction"),
        ("other", "Other"),
    ]

    adjustment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    transaction_date = models.DateField(
        default=date.today
    )

    name = models.CharField(
        max_length=200,
        help_text="Company, organization, person, or source name"
    )

    reason = models.TextField(
        help_text="Explain why this financial transaction was recorded."
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True
    )

    recorded_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-transaction_date",
            "-created_at"
        ]
        verbose_name = "Financial Adjustment"
        verbose_name_plural = "Financial Adjustments"

    def clean(self):
        super().clean()

        if self.amount <= Decimal("0.00"):
            raise ValidationError({
                "amount": "Amount must be greater than zero."
            })

        if not self.name.strip():
            raise ValidationError({
                "name": "Name or organization is required."
            })

        if not self.reason.strip():
            raise ValidationError({
                "reason": "A reason is required."
            })

        # Only Money Out needs a balance check.
        # Money In should not be blocked by the current balance.
        if self.adjustment_type == "money_out":

            total_paid = (
                Payment.objects
                .filter(status="paid")
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            total_repaid = (
                BorrowRepayment.objects
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            total_money_in = (
                FinancialAdjustment.objects
                .filter(adjustment_type="money_in")
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            money_out = FinancialAdjustment.objects.filter(
                adjustment_type="money_out"
            )

            # When editing an existing Money Out,
            # don't count the current transaction twice.
            if self.pk:
                money_out = money_out.exclude(pk=self.pk)

            total_money_out = (
                money_out
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            total_expenses = (
                Expense.objects
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            total_borrowed = (
                Borrow.objects
                .aggregate(total=Sum("principal_amount"))["total"]
                or Decimal("0.00")
            )

            available_balance = (
                total_paid
                + total_money_in
                + total_repaid
                - total_expenses
                - total_borrowed
                - total_money_out
            )

            if self.amount > available_balance:
                raise ValidationError({
                    "amount": (
                        f"Insufficient balance. "
                        f"Available balance is {available_balance}. "
                        f"You cannot record money out of {self.amount}."
                    )
                })

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.get_adjustment_type_display()} - "
            f"{self.amount}"
        )
class InterestRate(models.Model):

    rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=0,
        help_text="Annual interest rate. Example: 5 means 5% per year."
    )

    active = models.BooleanField(
        default=True
    )

    effective_date = models.DateField(
        default=date.today,
        help_text="Date from which this rate starts applying."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):
        super().clean()

        if self.rate < Decimal("0.00"):
            raise ValidationError({
                "rate": "Interest rate cannot be negative."
            })

        # Only one active general interest rate is allowed.
        active_rates = InterestRate.objects.filter(
            active=True
        )

        if self.pk:
            active_rates = active_rates.exclude(
                pk=self.pk
            )

        if active_rates.exists() and self.active:
            raise ValidationError({
                "active": (
                    "Only one general interest rate can be active "
                    "at the same time."
                )
            })

    def __str__(self):
        return (
            f"General Interest - "
            f"{self.rate}% per year "
            f"(from {self.effective_date})"
        )

    class Meta:
        ordering = [
            "-effective_date",
            "-id",
        ]