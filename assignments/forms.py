from django import forms
from assignments.models import Submission

class GradingForm(forms.ModelForm):

    class Meta:
        model = Submission
        fields = ["grade","comment"]
