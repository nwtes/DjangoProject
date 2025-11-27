from django.urls import path
from . import views

urlpatterns = [
    path("/task/<int:task_id>",views.student_task_view,name = "task")
]