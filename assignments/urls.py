from django.urls import path
from . import views

urlpatterns = [
    path("task/toggle-live/<int:task_id>", views.toggle_live, name="toggle_live"),
    path("task/autosave/<int:task_id>", views.autosave_task, name="autosave"),
    path("task/snapshot/<int:task_id>", views.snapshot_task, name="snapshot"),
    path("task/submit/<int:task_id>", views.submit_task, name="submit"),
    path("task/<int:task_id>", views.student_task_view, name="task"),
    path("submission/<int:submission_id>", views.submission_task_view, name="submission"),
    path("student/submission/<int:submission_id>", views.student_submission_view, name="student_submission"),
    path("list", views.student_tasks_view, name="student_tasks"),
    path("live/available/", views.live_tasks_for_student, name="live_tasks_available"),
    path("teacher/list", views.teacher_tasks_view, name="teacher_tasks"),
]