from django import forms
from assignments.models import Submission

class GradingForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ["grade", "comment"]
        widgets = {
            "grade": forms.NumberInput(attrs={"min": 0, "max": 100, "placeholder": "0 - 100"}),
        }

    def clean_grade(self):
        grade = self.cleaned_data.get("grade")
        if grade is not None and not (0 <= grade <= 100):
            raise forms.ValidationError("Grade must be between 0 and 100.")
        return grade
