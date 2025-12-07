from django.urls import path
from . import views

urlpatterns = [
    path("/task/<int:task_id>",views.student_task_view,name = "task"),
    path("/submission/<int:submission_id>",views.submission_task_view,name="submission"),
    path("/student/submission/<int:submission_id>",views.student_submission_view,name="student_submission"),
    path("/task/autosave/<int:task_id>",views.autosave_task,name="autosave"),
    path("/task/submit/<int:task_id>",views.submit_task,name="submit"),
    path("/list" , views.student_tasks_view, name="student_tasks")
]