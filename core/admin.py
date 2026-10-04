from django.contrib import admin
from django.db.models import Sum
from decimal import Decimal

from .models import (
    Person,
    Payment,
    PaymentPlan,
    PersonPlan,
    Expense,
    Borrow,
    BorrowRepayment,
    MemberTransaction,
    FinancialAdjustment,
    Notification,
    ActivityHistory,
     InterestRate,
      DeletedScheduledPayment,
    get_available_balance,
)


# ============================================================
# PERSON ADMIN
# ============================================================

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    list_display = (
        "person_id",
        "full_name",
        "phone",
        "status",
        "registration_date",
    )

    search_fields = (
        "person_id",
        "full_name",
        "phone",
    )

    list_filter = (
        "status",
        "registration_date",
    )

    ordering = (
        "-registration_date",
    )


# ============================================================
# PAYMENT PLAN ADMIN
# ============================================================

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "amount",
        "frequency",
        "active",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "frequency",
        "active",
    )

    ordering = (
        "name",
    )


# ============================================================
# PERSON PLAN ADMIN
# ============================================================

@admin.register(PersonPlan)
class PersonPlanAdmin(admin.ModelAdmin):

    list_display = (
        "person",
        "plan",
        "start_date",
        "active",
    )

    search_fields = (
        "person__person_id",
        "person__full_name",
        "plan__name",
    )

    list_filter = (
        "active",
        "plan",
    )

    ordering = (
        "-start_date",
    )


# ============================================================
# PAYMENT ADMIN
# ============================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "person",
        "amount",
        "due_date",
        "payment_date",
        "status",
        "payment_method",
        "reference_number",
    )

    search_fields = (
        "person__person_id",
        "person__full_name",
        "reference_number",
    )

    list_filter = (
        "status",
        "payment_method",
        "due_date",
    )

    ordering = (
        "-due_date",
    )

    def delete_model(self, request, obj):
        """
        Record intentional deletion of a scheduled payment
        before deleting the Payment itself.
        """

        if obj.plan.frequency != "deposit":
            DeletedScheduledPayment.objects.get_or_create(
                person=obj.person,
                plan=obj.plan,
                due_date=obj.due_date,
            )

        obj.delete()

    def delete_queryset(self, request, queryset):
        """
        Record intentional deletion when using
        'Delete selected payments'.
        """

        for obj in queryset.select_related("person", "plan"):
            if obj.plan.frequency != "deposit":
                DeletedScheduledPayment.objects.get_or_create(
                    person=obj.person,
                    plan=obj.plan,
                    due_date=obj.due_date,
                )

        queryset.delete()


# ============================================================
# NOTIFICATION ADMIN
# ============================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "person",
        "notification_type",
        "channel",
        "title",
        "is_read",
        "created_at",
    )

    search_fields = (
        "person__person_id",
        "person__full_name",
        "title",
        "message",
    )

    list_filter = (
        "notification_type",
        "channel",
        "is_read",
        "created_at",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# ACTIVITY HISTORY ADMIN
# ============================================================

@admin.register(ActivityHistory)
class ActivityHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "person",
        "action",
        "created_by",
        "created_at",
    )

    search_fields = (
        "person__person_id",
        "person__full_name",
        "action",
        "description",
    )

    list_filter = (
        "action",
        "created_at",
    )

    ordering = (
        "-created_at",
    )


# ============================================================
# EXPENSE ADMIN
# ============================================================

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "expense_type",
        "amount",
        "expense_date",
        "recorded_by",
    )

    search_fields = (
        "name",
        "reason",
    )

    list_filter = (
        "expense_type",
        "expense_date",
    )

    readonly_fields = (
        "created_at",
    )

    fields = (
        "name",
        "expense_type",
        "amount",
        "expense_date",
        "reason",
        "recorded_by",
        "created_at",
    )


# ============================================================
# BORROW ADMIN
# ============================================================

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):

    list_display = (
        "person",
        "principal_amount",
        "interest_rate",
        "duration",
        "duration_type",
        "borrow_date",
        "due_date",
        "total_repayment",
        "remaining_balance",
        "payment_method",
        "status",
    )

    search_fields = (
        "person__person_id",
        "person__full_name",
        "person__phone",
    )

    list_filter = (
        "status",
        "duration_type",
        "payment_method",
        "borrow_date",
    )

    readonly_fields = (
        "due_date",
        "interest_amount",
        "total_repayment",
        "remaining_balance",
        "created_at",
    )

    autocomplete_fields = (
        "person",
    )

    ordering = (
        "-borrow_date",
    )


# ============================================================
# BORROW REPAYMENT ADMIN
# ============================================================

@admin.register(BorrowRepayment)
class BorrowRepaymentAdmin(admin.ModelAdmin):

    list_display = (
        "borrow",
        "amount",
        "payment_date",
        "payment_method",
        "reference_number",
        "received_by",
    )

    search_fields = (
        "borrow__person__person_id",
        "borrow__person__full_name",
        "reference_number",
    )

    list_filter = (
        "payment_method",
        "payment_date",
    )

    autocomplete_fields = (
        "borrow",
    )

    ordering = (
        "-payment_date",
    )


# ============================================================
# MEMBER TRANSACTION ADMIN
# ============================================================

@admin.register(MemberTransaction)
class MemberTransactionAdmin(admin.ModelAdmin):

    list_display = (
        "person",
        "transaction_type",
        "amount",
        "transaction_date",
        "reference_number",
        "recorded_by",
    )

    search_fields = (
        "person__person_id",
        "person__full_name",
        "reference_number",
    )

    list_filter = (
        "transaction_type",
        "transaction_date",
    )

    ordering = (
        "-transaction_date",
        "-id",
    )


# ============================================================
# FINANCIAL ADJUSTMENT ADMIN
# ============================================================

@admin.register(FinancialAdjustment)
class FinancialAdjustmentAdmin(admin.ModelAdmin):

    list_display = (
        "transaction_date",
        "name",
        "adjustment_type",
        "category",
        "amount",
        "reference_number",
        "recorded_by",
    )

    search_fields = (
        "name",
        "reason",
        "reference_number",
    )

    list_filter = (
        "adjustment_type",
        "category",
        "transaction_date",
    )

    ordering = (
        "-transaction_date",
        "-created_at",
    )

    readonly_fields = (
        "created_at",
    )

    fields = (
        "adjustment_type",
        "category",
        "name",
        "amount",
        "transaction_date",
        "reason",
        "reference_number",
        "recorded_by",
        "created_at",
    )

    def changelist_view(self, request, extra_context=None):

        # =====================================================
        # NORMAL PAYMENTS
        # =====================================================

        total_deposits = (
            Payment.objects
            .filter(status="paid")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # MEMBER DEPOSITS
        # =====================================================

        total_member_deposits = (
            MemberTransaction.objects
            .filter(transaction_type="deposit")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # MEMBER SAVINGS
        # =====================================================

        total_member_savings = (
            MemberTransaction.objects
            .filter(transaction_type="saving")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # MEMBER WITHDRAWALS
        # =====================================================

        total_member_withdrawals = (
            MemberTransaction.objects
            .filter(transaction_type="withdrawal")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # EXPENSES
        # =====================================================

        total_expenses = (
            Expense.objects
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # BORROWED MONEY
        # =====================================================

        total_borrowed = (
            Borrow.objects
            .aggregate(total=Sum("principal_amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # LOAN REPAYMENTS
        # =====================================================

        total_repaid = (
            BorrowRepayment.objects
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # FINANCIAL ADJUSTMENTS - MONEY IN
        # =====================================================

        total_money_in = (
            FinancialAdjustment.objects
            .filter(adjustment_type="money_in")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # FINANCIAL ADJUSTMENTS - MONEY OUT
        # =====================================================

        total_money_out = (
            FinancialAdjustment.objects
            .filter(adjustment_type="money_out")
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        # =====================================================
        # MAIN BALANCE
        # =====================================================

        total_balance = (
            total_deposits
            + total_member_deposits
            + total_member_savings
            + total_repaid
            + total_money_in
            - total_member_withdrawals
            - total_expenses
            - total_borrowed
            - total_money_out
        )

        # =====================================================
        # ADMIN EXTRA DATA
        # =====================================================

        extra_context = extra_context or {}

        extra_context.update({
            "total_balance": total_balance,
            "total_deposits": total_deposits,
            "total_member_deposits": total_member_deposits,
            "total_member_savings": total_member_savings,
            "total_member_withdrawals": total_member_withdrawals,
            "total_expenses": total_expenses,
            "total_borrowed": total_borrowed,
            "total_repaid": total_repaid,
            "total_money_in": total_money_in,
            "total_money_out": total_money_out,
        })

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )
@admin.register(InterestRate)
class InterestRateAdmin(admin.ModelAdmin):
     list_display = (
        "rate",
        "effective_date",
        "active",
        "created_at",
    )

     list_filter = (
        "active",
        "effective_date",
    )

     search_fields = (
        "rate",
    )

     ordering = (
        "-effective_date",
        "-id",
    )