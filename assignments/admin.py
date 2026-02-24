from django.contrib import admin
from .models import Task, Submission, FinalSubmission

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'task_type', 'is_live')
    list_filter = ('group', 'task_type', 'is_live')
    search_fields = ('title', 'description', 'group__name')

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'task', 'submitted', 'submitted_at', 'grade')
    list_filter = ('task', 'submitted', 'submitted_at')
    search_fields = ('student__display_name', 'task__title')

@admin.register(FinalSubmission)
class FinalSubmissionAdmin(admin.ModelAdmin):
    list_display = ('submission', 'submitted_at')
    search_fields = ('submission__task__title', 'submission__student__display_name')
