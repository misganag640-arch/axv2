from datetime import date

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal
from .forms import (
    PersonForm,
    PaymentForm,
    PaymentPlanForm,
    AssignPlanForm,
    MemberTransactionForm,
)
from django.contrib.auth.decorators import (
    login_required,
    user_passes_test,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .models import (
    Person,
    Payment,
    Notification,
    ActivityHistory,
    PaymentPlan,
    PersonPlan,
    Expense,
    Borrow,
    BorrowRepayment,
    MemberTransaction,
    FinancialAdjustment,
    PersonDocument,
)
from .services import refresh_payments

# ============================================================
# ADMIN CHECK
# ============================================================
def admin_only(user):
    return (
        user.is_superuser
        or user.groups.filter(
            name="Administrators"
        ).exists()
    )
def logout_view(request):
    logout(request)
    return redirect("login")
# ============================================================
# DASHBOARD
# ============================================================

# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard(request):

    refresh_payments()

    # =====================================================
    # MONEY CALCULATIONS
    # =====================================================

    # Normal member payments
    total_paid = (
        Payment.objects
        .filter(status="paid")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Member deposits
    total_member_deposits = (
        MemberTransaction.objects
        .filter(transaction_type="deposit")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Member savings
    total_member_savings = (
        MemberTransaction.objects
        .filter(transaction_type="saving")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Member withdrawals
    total_member_withdrawals = (
        MemberTransaction.objects
        .filter(transaction_type="withdrawal")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Expenses
    total_expenses = (
        Expense.objects
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Borrowed money
    total_borrowed = (
        Borrow.objects
        .aggregate(total=Sum("principal_amount"))["total"]
        or Decimal("0.00")
    )

    # Loan repayments
    total_repaid = (
        BorrowRepayment.objects
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # =====================================================
    # TOTAL MONEY RECEIVED
    # =====================================================

    total_money_received = (
        total_paid
        + total_member_deposits
        + total_member_savings
    )

    # =====================================================
    # MAIN SYSTEM BALANCE
    # =====================================================

    net_balance = (
        total_paid
        + total_member_deposits
        + total_member_savings
        + total_repaid
        - total_member_withdrawals
        - total_expenses
        - total_borrowed
    )

    # =====================================================
    # DASHBOARD
    # =====================================================

    # -------------------------------------------------
    # MARK BORROWS AS OVERDUE
    # -------------------------------------------------

    today = date.today()

    Borrow.objects.filter(
        status="active",
        due_date__lt=today,
    ).update(
        status="overdue"
    )

    context = {

        # -------------------------------------------------
        # PEOPLE
        # -------------------------------------------------

        "people_count": Person.objects.filter(
            status="active"
        ).count(),

        

        # -------------------------------------------------
        # PAYMENT COUNTS
        # -------------------------------------------------

        "unpaid_count": Payment.objects.filter(
            status="unpaid"
        ).count(),

        "overdue_count": Payment.objects.filter(
            status="overdue"
        ).count(),

        "paid_count": Payment.objects.filter(
            status="paid"
        ).count(),

         "recent_deposits_count": MemberTransaction.objects.filter(
           transaction_type="deposit"
        ).count(),

         "recent_withdrawals_count": MemberTransaction.objects.filter(
             transaction_type="withdrawal"
        ).count(),

        # -------------------------------------------------
        # TOTAL MONEY RECEIVED
        # -------------------------------------------------

        "total_money_received": total_money_received,

        # -------------------------------------------------
        # MAIN MONEY TOTALS
        # -------------------------------------------------

        "paid_total": total_paid,

        "member_deposits_total": total_member_deposits,

        "member_savings_total": total_member_savings,

        "member_withdrawals_total": total_member_withdrawals,

        "expense_total": total_expenses,

        "borrowed_total": total_borrowed,

        "repaid_total": total_repaid,

        # -------------------------------------------------
        # MAIN SYSTEM BALANCE
        # -------------------------------------------------

        "net_balance": net_balance,

        # -------------------------------------------------
        # LATEST PAYMENTS
        # -------------------------------------------------

        "recent_payments": (
            Payment.objects
            .select_related(
                "person",
                "plan"
            )
            .order_by(
                "-created_at"
            )[:10]
        ),
        

        # -------------------------------------------------
        # OVERDUE PEOPLE
        # -------------------------------------------------

        "overdue_people": (
            Payment.objects
            .filter(status="overdue")
            .select_related(
                "person",
                "plan"
            )
            .order_by(
                "due_date"
            )[:10]
        ),
          "overdue_borrows": (
            Borrow.objects
            .filter(status="overdue")
            .select_related("person")
            .order_by("due_date")[:10]
        ),
    }

    return render(
        request,
        "dashboard.html",
        context
    )


# ============================================================
# PEOPLE LIST AND SEARCH
# ============================================================
@login_required
def people_list(request):

    # Search text
    q = request.GET.get(
        "q",
        ""
    ).strip()

    # Selected payment plan filter
    plan_filter = request.GET.get(
        "plan",
        ""
    ).strip()

    # Start with all people
    people = Person.objects.all()

    # ---------------------------------------------
    # SEARCH BY ID / NAME / PHONE
    # ---------------------------------------------

    if q:

        people = people.filter(

            Q(
                person_id__icontains=q
            )
            | Q(
                full_name__icontains=q
            )
            | Q(
                phone__icontains=q
            )

        )

    # ---------------------------------------------
    # NO PAYMENT PLAN
    # ---------------------------------------------

    if plan_filter == "no_plan":

        people = people.filter(
            assigned_plans__isnull=True
        )

    # ---------------------------------------------
    # FILTER BY PAYMENT PLAN
    # ---------------------------------------------

    elif plan_filter:

        people = people.filter(

            assigned_plans__active=True,

            assigned_plans__plan__frequency=plan_filter

        )

    # Remove duplicate people
    people = people.distinct()

    return render(

        request,

        "people.html",

        {

            "people": people,

            "q": q,

            "plan_filter": plan_filter,

        }

    )

    # ---------------------------------------------
    # FILTER BY ASSIGNED PAYMENT PLAN
    # ---------------------------------------------
# ============================================================
# PEOPLE LIST AND SEARCH
# ============================================================

@login_required
def people_list(request):

    q = request.GET.get(
        "q",
        ""
    ).strip()

    plan_filter = request.GET.get(
        "plan",
        ""
    ).strip()

    people = Person.objects.all()

    # Search by ID, name, or phone
    if q:
        people = people.filter(
            Q(person_id__icontains=q)
            | Q(full_name__icontains=q)
            | Q(phone__icontains=q)
        )

    # People without a payment plan
    if plan_filter == "no_plan":

        people = people.filter(
            assigned_plans__isnull=True
        )

    # Filter by payment plan
    elif plan_filter:

        people = people.filter(
            assigned_plans__active=True,
            assigned_plans__plan__frequency=plan_filter
        )

    people = people.distinct()

    return render(
        request,
        "people.html",
        {
            "people": people,
            "q": q,
            "plan_filter": plan_filter,
        }
    )


# ============================================================
# REGISTER PERSON
# ============================================================
# ============================================================
# REGISTER PERSON
# ============================================================

@login_required
def person_create(request):
    form = PersonForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():
        person = form.save()
                # Save additional document photos
        for field_name, title in [
            ("document_1", "Document 1"),
            ("document_2", "Document 2"),
            ("document_3", "Document 3"),
        ]:
            document = form.cleaned_data.get(field_name)

            if document:
                PersonDocument.objects.create(
                    person=person,
                    title=title,
                    image=document,
                )

        # Save registration history
        ActivityHistory.objects.create(
            person=person,
            action="Registered",
            description=(
                f"Person {person.full_name} "
                f"was registered."
            ),
            created_by=request.user,
        )

        messages.success(
            request,
            "Person registered successfully."
        )

        return redirect(
            "person_detail",
            person_id=person.pk
        )

    return render(
        request,
        "person_form.html",
        {
            "form": form
        },
    )

# ============================================================
# PERSON DETAILS
# ============================================================

# ============================================================
# PERSON DETAILS
# ============================================================

@login_required
def person_detail(request, person_id):

    refresh_payments()

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    # --------------------------------------------------------
    # PAYMENT SCHEDULE
    # --------------------------------------------------------

    payments = (
        person.payments
        .select_related("plan")
        .order_by("-due_date")
    )

    # --------------------------------------------------------
    # ASSIGNED PLANS
    # --------------------------------------------------------

    assigned_plans = (
        person.assigned_plans
        .select_related("plan")
        .filter(active=True)
    )

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    notifications = (
        person.notifications
        .all()
        .order_by("-created_at")[:20]
    )

    # --------------------------------------------------------
    # ACTIVITY HISTORY
    # --------------------------------------------------------

    history = (
        person.history
        .all()
        .order_by("-created_at")[:30]
    )

    # --------------------------------------------------------
    # MEMBER TRANSACTIONS
    # --------------------------------------------------------

    transactions = (
        person.member_transactions
        .all()
        .order_by(
            "-transaction_date",
            "-created_at"
        )
    )

    # --------------------------------------------------------
    # PERSONAL PAYMENT CREDIT
    # --------------------------------------------------------
    # Only PAID payments belonging to PERSONAL plans
    # are added to the member's personal balance.
    #
    # Wabii payments are NOT included here.

    payment_credit = (
        Payment.objects
        .filter(
            person=person,
            status="paid",
            plan__plan_type="personal",
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # MEMBER DEPOSITS
    # --------------------------------------------------------

    deposit_total = (
        transactions
        .filter(
            transaction_type="deposit"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # SAVINGS
    # --------------------------------------------------------

    saving_total = (
        transactions
        .filter(
            transaction_type="saving"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # INTEREST EARNED
    # --------------------------------------------------------
    # Interest is stored as a separate MemberTransaction.
    # It is added to the member's personal balance.

    interest_total = (
        transactions
        .filter(
            transaction_type="interest"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # WITHDRAWALS
    # --------------------------------------------------------

    withdrawal_total = (
        transactions
        .filter(
            transaction_type="withdrawal"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # TOTAL CREDITED
    # --------------------------------------------------------
    # Personal payments
    # + deposits
    # + savings
    # + earned interest

    total_credited = (
        payment_credit
        + deposit_total
        + saving_total
        + interest_total
    )

    # --------------------------------------------------------
    # TOTAL DEBITED
    # --------------------------------------------------------
    # Withdrawals reduce the member's balance.

    total_debited = withdrawal_total

    # --------------------------------------------------------
    # TOTAL PERSONAL BALANCE
    # --------------------------------------------------------

    total_balance = (
        total_credited
        - total_debited
    )

    # --------------------------------------------------------
    # RENDER MEMBER DETAIL PAGE
    # --------------------------------------------------------

    return render(
        request,
        "person_detail.html",
        {
            "person": person,

            "payments": payments,

            "assigned_plans": assigned_plans,

            "notifications": notifications,

            "history": history,

            "transactions": transactions,

            # Financial summary
            "payment_credit": payment_credit,

            "deposit_total": deposit_total,

            "saving_total": saving_total,

            "interest_total": interest_total,

            "withdrawal_total": withdrawal_total,

            "total_credited": total_credited,

            "total_debited": total_debited,

            "total_balance": total_balance,
        },
    )
# ============================================================
# PERSON PROFILE
# ============================================================

@login_required
def person_profile(request, person_id):

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    documents = (
        person.documents
        .all()
        .order_by("-uploaded_at")
    )

    return render(
        request,
        "person_profile.html",
        {
            "person": person,
            "documents": documents,
        },
    )


# ============================================================
# PAYMENT PLAN MANAGEMENT
# ADMIN ONLY
# ============================================================

@login_required
@user_passes_test(admin_only)
def plan_manage(request):
    form = PaymentPlanForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        messages.success(
            request,
            "Payment plan saved successfully."
        )

        return redirect(
            "plans"
        )

    plans = PaymentPlan.objects.all().order_by(
        "-id"
    )

    return render(
        request,
        "plans.html",
        {
            "form": form,
            "plans": plans,
        },
    )


# ============================================================
# ASSIGN PAYMENT PLAN TO PERSON
# ADMIN ONLY
# ============================================================

# ============================================================
# ASSIGN PAYMENT PLAN TO PERSON
# ADMIN ONLY
# ============================================================


@login_required
@user_passes_test(admin_only)
def assign_plan(request, person_id):
    person = get_object_or_404(
        Person,
        pk=person_id
    )

    form = AssignPlanForm(
        request.POST or None
    )

    if request.method == "POST":
        if form.is_valid():
            obj = form.save(
                commit=False
            )

            obj.person = person
            obj.save()

            # Create a payment record for every assigned plan,
            # including Deposit / On-Demand plans.
            Payment.objects.get_or_create(
                person=person,
                plan=obj.plan,
                due_date=obj.start_date,
                defaults={
                    "amount": obj.plan.amount,
                    "status": "unpaid",
                },
            )

            # Record the assignment
            ActivityHistory.objects.create(
                person=person,
                action="Payment plan assigned",
                description=(
                    f"Plan {obj.plan} "
                    f"was assigned to this person."
                ),
                created_by=request.user,
            )

            messages.success(
                request,
                "Plan assigned successfully. "
                "Payment record created."
            )

            return redirect(
                "person_detail",
                person_id=person.pk
            )

    return render(
        request,
        "assign_plan.html",
        {
            "form": form,
            "person": person,
        }
    )



# ============================================================
# CONFIRM PAYMENT
# EXACT AMOUNT ONLY
# ============================================================

@login_required
def payment_create(request, payment_id):
    # Update payment statuses first
    refresh_payments()

    payment = get_object_or_404(
        Payment,
        pk=payment_id
    )

    # Do not allow payment twice
    if payment.status == "paid":
        messages.error(
            request,
            "This payment is already paid."
        )

        return redirect(
            "person_detail",
            person_id=payment.person_id
        )

    # Expected amount is the amount set by admin
    form = PaymentForm(
        request.POST or None,
        expected_amount=payment.amount
    )

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data

        # Do not allow payment date before scheduled due date
        if data["payment_date"] < payment.due_date:
            form.add_error(
                "payment_date",
                "Payment date cannot be before "
                "the scheduled due date."
            )

        else:
            # Save payment information
            payment.payment_date = data[
                "payment_date"
            ]

            payment.payment_method = data[
                "payment_method"
            ]

            payment.reference_number = data[
                "reference_number"
            ]

            payment.notes = data[
                "notes"
            ]

            # Mark as paid
            payment.status = "paid"

            # Store who confirmed payment
            payment.verified_by = request.user

            payment.verified_at = timezone.now()

            payment.save()

            # Create payment notification
            Notification.objects.create(
                person=payment.person,
                payment=payment,
                notification_type="paid",
                title="Payment Confirmed",
                message=(
                    f"{payment.person.full_name} "
                    f"paid {payment.amount}. "
                    f"Due date was "
                    f"{payment.due_date}."
                ),
            )

            # Save payment history
            ActivityHistory.objects.create(
                person=payment.person,
                action="Payment confirmed",
                description=(
                    f"Payment of {payment.amount} "
                    f"was confirmed."
                ),
                created_by=request.user,
            )

            messages.success(
                request,
                "Payment confirmed successfully."
            )

            return redirect(
                "person_detail",
                person_id=payment.person_id
            )

    return render(
        request,
        "payment_form.html",
        {
            "form": form,
            "payment": payment,
            "person": payment.person,
        },
    )


# ============================================================
# ALL PAYMENTS
# ============================================================

@login_required
def payments_list(request):
    # Refresh unpaid and overdue status
    refresh_payments()

    q = request.GET.get(
        "q",
        ""
    ).strip()

    status = request.GET.get(
        "status",
        ""
    )

    payments = Payment.objects.select_related(
        "person",
        "plan"
    ).all()

    # Filter by payment status
    if status in (
        "unpaid",
        "overdue",
        "paid"
    ):
        payments = payments.filter(
            status=status
        )

    # Search by person or payment reference
    if q:
        payments = payments.filter(
            Q(
                person__person_id__icontains=q
            )
            | Q(
                person__full_name__icontains=q
            )
            | Q(
                reference_number__icontains=q
            )
        )

    return render(
        request,
        "payments.html",
        {
            "payments": payments,
            "q": q,
            "status": status,
        },
    )


# ============================================================
# UNPAID LIST
# ============================================================

@login_required
def unpaid_list(request):
    refresh_payments()

    payments = Payment.objects.filter(
        status="unpaid"
    ).select_related(
        "person",
        "plan"
    ).order_by(
        "due_date"
    )

    return render(
        request,
        "payments.html",
        {
            "payments": payments,
            "q": "",
            "status": "unpaid",
        },
    )

# ============================================================
# OVERDUE LIST
# ============================================================

@login_required
def overdue_list(request):
    refresh_payments()

    payments = Payment.objects.filter(
        status="overdue"
    ).select_related(
        "person",
        "plan"
    ).order_by(
        "due_date"
    )

    return render(
        request,
        "payments.html",
        {
            "payments": payments,
            "q": "",
            "status": "overdue",
        },
    )

# ============================================================
# PAID LIST
# ============================================================

@login_required
def paid_list(request):
    payments = Payment.objects.filter(
        status="paid"
    ).select_related(
        "person",
        "plan"
    ).order_by(
        "-payment_date"
    )

    return render(
        request,
        "payments.html",
        {
            "payments": payments,
            "q": "",
            "status": "paid",
        },
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@login_required
def notifications_list(request):
    # Check for new overdue payments
    refresh_payments()

    notifications = Notification.objects.select_related(
        "person",
        "payment"
    ).order_by(
        "-created_at"
    )

    # Mark notifications as read when opened
    Notification.objects.filter(
        is_read=False
    ).update(
        is_read=True
    )

    return render(
        request,
        "notifications.html",
        {
            "notifications": notifications
        },
    )
# ============================================================
# MEMBER DEPOSIT
# ============================================================

@login_required
def member_deposit(request, person_id):

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    form = MemberTransactionForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        transaction = form.save(
            commit=False
        )

        transaction.person = person
        transaction.transaction_type = "deposit"
        transaction.recorded_by = request.user

        transaction.save()

        ActivityHistory.objects.create(
            person=person,
            action="Deposit",
            description=(
                f"Deposit of {transaction.amount} "
                f"was recorded."
            ),
            created_by=request.user,
        )

        messages.success(
            request,
            "Deposit recorded successfully."
        )

        return redirect(
            "person_detail",
            person_id=person.pk
        )

    return render(
        request,
        "member_transaction_form.html",
        {
            "form": form,
            "person": person,
            "transaction_title": "Make Deposit",
            "transaction_type": "Deposit",
        },
    )
# ============================================================
# MEMBER WITHDRAWAL
# ============================================================

@login_required
def member_withdrawal(request, person_id):

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    form = MemberTransactionForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        transaction = form.save(
            commit=False
        )

        transaction.person = person
        transaction.transaction_type = "withdrawal"
        transaction.recorded_by = request.user

        try:
            transaction.full_clean()
            transaction.save()

        except ValidationError as error:
            form.add_error(
                None,
                error
            )

        else:

            ActivityHistory.objects.create(
                person=person,
                action="Withdrawal",
                description=(
                    f"Withdrawal of {transaction.amount} "
                    f"was recorded."
                ),
                created_by=request.user,
            )

            messages.success(
                request,
                "Withdrawal recorded successfully."
            )

            return redirect(
                "person_detail",
                person_id=person.pk
            )

    return render(
        request,
        "member_transaction_form.html",
        {
            "form": form,
            "person": person,
            "transaction_title": "Make Withdrawal",
            "transaction_type": "Withdrawal",
        },
    )
# ============================================================
# MEMBER SAVING
# ============================================================

@login_required
def member_saving(request, person_id):

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    form = MemberTransactionForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        transaction = form.save(
            commit=False
        )

        transaction.person = person
        transaction.transaction_type = "saving"
        transaction.recorded_by = request.user

        transaction.save()

        ActivityHistory.objects.create(
            person=person,
            action="Saving",
            description=(
                f"Saving of {transaction.amount} "
                f"was recorded."
            ),
            created_by=request.user,
        )

        messages.success(
            request,
            "Saving recorded successfully."
        )

        return redirect(
            "person_detail",
            person_id=person.pk
        )

    return render(
        request,
        "member_transaction_form.html",
        {
            "form": form,
            "person": person,
            "transaction_title": "Add Saving",
            "transaction_type": "Saving",
        },
    )
# ============================================================
# MEMBER TRANSACTIONS
# ============================================================

@login_required
def member_transactions(request, person_id):

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    transactions = (
        person.member_transactions
        .all()
        .order_by(
            "-transaction_date",
            "-created_at"
        )
    )

    deposits = transactions.filter(
        transaction_type="deposit"
    )

    savings = transactions.filter(
        transaction_type="saving"
    )

    withdrawals = transactions.filter(
        transaction_type="withdrawal"
    )

    return render(
        request,
        "member_transactions.html",
        {
            "person": person,
            "transactions": transactions,
            "deposits": deposits,
            "savings": savings,
            "withdrawals": withdrawals,
        },
    )
# ============================================================
# MEMBER TRANSACTIONS
# ============================================================

@login_required
def member_transactions(request, person_id):

    person = get_object_or_404(
        Person,
        pk=person_id
    )

    payments = Payment.objects.filter(
        person=person
    ).select_related(
        "plan"
    ).order_by(
        "-due_date"
    )

    # Total money actually paid by this member
    total_paid = payments.filter(
        status="paid"
    ).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    # Total scheduled payments
    total_scheduled = payments.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    return render(
        request,
        "member_transactions.html",
        {
            "person": person,
            "payments": payments,
            "total_paid": total_paid,
            "total_scheduled": total_scheduled,
        },
    )
@login_required
def recent_deposits(request):
    deposits = (
        MemberTransaction.objects
        .filter(transaction_type="deposit")
        .select_related("person", "recorded_by")
        .order_by("-transaction_date", "-created_at")
    )

    return render(
        request,
        "recent_deposits.html",
        {
            "deposits": deposits,
        },
    )


@login_required
def recent_withdrawals(request):
    withdrawals = (
        MemberTransaction.objects
        .filter(transaction_type="withdrawal")
        .select_related("person", "recorded_by")
        .order_by("-transaction_date", "-created_at")
    )

    return render(
        request,
        "recent_withdrawals.html",
        {
            "withdrawals": withdrawals,
        },
    ) 