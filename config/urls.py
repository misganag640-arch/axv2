from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path
from core import views

urlpatterns = [
    # Django Admin
   path("control-panel/", admin.site.urls),

    # Login
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html"
        ),
        name="login"
    ),

   # Logout
path(
    "logout/",
    views.logout_view,
    name="logout"
),
    # Dashboard
    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    # ========================================================
    # PEOPLE
    # ========================================================

    path(
        "people/",
        views.people_list,
        name="people"
    ),

    path(
        "people/add/",
        views.person_create,
        name="person_create"
    ),

    path(
        "people/<int:person_id>/",
        views.person_detail,
        name="person_detail"
    ),
    path(
    "people/<int:person_id>/profile/",
    views.person_profile,
    name="person_profile",
    ),

    path(
        "people/<int:person_id>/assign-plan/",
        views.assign_plan,
        name="assign_plan"
    ),

    # ========================================================
    # PAYMENT PLANS
    # ========================================================

    path(
        "plans/",
        views.plan_manage,
        name="plans"
    ),

    # ========================================================
    # PAYMENTS
    # ========================================================

    # All payments
    path(
        "payments/",
        views.payments_list,
        name="payments"
    ),

    # Unpaid payments
    path(
        "payments/unpaid/",
        views.unpaid_list,
        name="unpaid"
    ),

    # Overdue payments
    path(
        "payments/overdue/",
        views.overdue_list,
        name="overdue"
    ),

    # Paid payments
    path(
        "payments/paid/",
        views.paid_list,
        name="paid"
    ),

    # Confirm payment
    path(
        "payments/<int:payment_id>/pay/",
        views.payment_create,
        name="payment_create"
    ),

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    path(
        "notifications/",
        views.notifications_list,
        name="notifications"
    ),
    path(
    "people/<int:person_id>/deposit/",
    views.member_deposit,
    name="member_deposit"
),

path(
    "people/<int:person_id>/withdraw/",
    views.member_withdrawal,
    name="member_withdrawal"
),

path(
    "people/<int:person_id>/saving/",
    views.member_saving,
    name="member_saving"
),

path(
    "members/<int:person_id>/transactions/",
    views.member_transactions,
    name="member_transactions",
),
path(
    "transactions/deposits/",
    views.recent_deposits,
    name="recent_deposits",
),

path(
    "transactions/withdrawals/",
    views.recent_withdrawals,
    name="recent_withdrawals",
),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )