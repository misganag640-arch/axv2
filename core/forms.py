from django import forms

from .models import (
    Person,
    Payment,
    PaymentPlan,
    PersonPlan,
    Expense,
    MemberTransaction,
)
# ============================================================
# PERSON REGISTRATION FORM
# ============================================================

# ============================================================
# PERSON REGISTRATION FORM
# ============================================================

class PersonForm(forms.ModelForm):

    document_1 = forms.ImageField(
        required=False,
        label="Document Photo 1",
    )

    document_2 = forms.ImageField(
        required=False,
        label="Document Photo 2",
    )

    document_3 = forms.ImageField(
        required=False,
        label="Document Photo 3",
    )

    class Meta:
        model = Person
        fields = [
            "person_id",
            "national_id",
            "full_name",
            "phone",
            "email",
            "address",
            "gender",
            "date_of_birth",
            "employment_status",
            "marital_status",
            "spouse_full_name",
            "spouse_phone",
            "registration_date",
            "photo",
            "national_id_photo",
            "status",
        ]

        widgets = {
            "registration_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Optional"
                }
            ),

            "spouse_full_name": forms.TextInput(
                attrs={
                    "placeholder": "Full name of spouse"
                }
            ),

            "spouse_phone": forms.TextInput(
                attrs={
                    "placeholder": "Spouse phone number"
                }
            ),
                        "photo": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                    "capture": "user",
                }
            ),

            "national_id_photo": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                    "capture": "environment",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")

        # Email is optional.
        if not email:
            return None

        return email

    def clean(self):
        cleaned_data = super().clean()

        marital_status = cleaned_data.get("marital_status")
        spouse_full_name = cleaned_data.get("spouse_full_name")
        spouse_phone = cleaned_data.get("spouse_phone")

        # Spouse information is required for married persons.
        if marital_status == "married":

            if not spouse_full_name:
                self.add_error(
                    "spouse_full_name",
                    "Spouse's full name is required for a married person."
                )

            if not spouse_phone:
                self.add_error(
                    "spouse_phone",
                    "Spouse's phone number is required for a married person."
                )

        else:
            # Do not keep spouse information for non-married persons.
            cleaned_data["spouse_full_name"] = ""
            cleaned_data["spouse_phone"] = ""

        return cleaned_data


# ============================================================
# PAYMENT PLAN FORM
# ============================================================

# ============================================================
# PAYMENT PLAN FORM
# ============================================================

class PaymentPlanForm(forms.ModelForm):

    class Meta:
        model = PaymentPlan

        fields = [
            "name",
            "amount",
            "plan_type",
            "frequency",
            "active",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }


# ============================================================
# ASSIGN PAYMENT PLAN TO PERSON
# ============================================================

class AssignPlanForm(forms.ModelForm):
    class Meta:
        model = PersonPlan

        fields = [
            "plan",
            "start_date",
            "active",
        ]

        widgets = {
            "start_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),
        }


# ============================================================
# PAYMENT CONFIRMATION FORM
# ============================================================

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment

        fields = [
            "amount",
            "payment_date",
            "payment_method",
            "reference_number",
            "notes",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                }
            ),
            "payment_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),
        }

    # --------------------------------------------------------
    # GET EXPECTED PAYMENT AMOUNT
    # --------------------------------------------------------

    def __init__(
        self,
        *args,
        expected_amount=None,
        **kwargs
    ):
        super().__init__(
            *args,
            **kwargs
        )
        self.expected_amount = expected_amount

    # --------------------------------------------------------
    # CHECK EXACT PAYMENT AMOUNT
    # --------------------------------------------------------

    def clean_amount(self):
        amount = self.cleaned_data.get(
            "amount"
        )

        if amount is None:
            raise forms.ValidationError(
                "Payment amount is required."
            )

        # Check that payment amount is exactly
        # the amount set by the administrator
        if (
            self.expected_amount is not None
            and amount != self.expected_amount
        ):
            raise forms.ValidationError(
                f"Amount must be exactly "
                f"{self.expected_amount}."
            )

        return amount

    # --------------------------------------------------------
    # CHECK PAYMENT DATE
    # --------------------------------------------------------

    def clean_payment_date(self):
        payment_date = self.cleaned_data.get(
            "payment_date"
        )

        if payment_date is None:
            raise forms.ValidationError(
                "Payment date is required."
            )

        return payment_date
     # ============================================================
# EXPENSE FORM
# ============================================================

class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense

        fields = [
            "name",
            "expense_type",
            "amount",
            "expense_date",
            "reason",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                }
            ),

            "expense_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
        }
# ============================================================
# MEMBER TRANSACTION FORM
# ============================================================

class MemberTransactionForm(forms.ModelForm):

    class Meta:
        model = MemberTransaction

        fields = [
            "amount",
            "transaction_date",
            "payment_method",
            "reference_number",
            "notes",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                    "placeholder": "Enter amount",
                }
            ),

            "transaction_date": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "reference_number": forms.TextInput(
                attrs={
                    "placeholder": "Optional reference number"
                }
            ),
             "payment_method": forms.Select(),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional notes"
                }
            ),
        }