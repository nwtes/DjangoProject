from django import forms
from assignments.models import Task

class TaskCreationForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['title', 'description', 'group','is_live','task_type','starter_code']
        widgets = {
            'starter_code': forms.Textarea(attrs={'rows':8})
        }
