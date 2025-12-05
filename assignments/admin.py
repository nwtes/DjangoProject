from django.contrib import admin
from .models import Task,Submission,FinalSubmission
# Register your models here.


admin.site.register(Task)
admin.site.register(Submission)
admin.site.register(FinalSubmission)