from django import forms
from assignments.models import Task

class TaskCreationForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['title', 'description', 'group']