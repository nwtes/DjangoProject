from django.urls import path
from . import views

urlpatterns = [
    path("",views.home_view,name="home"),
    path("teacher/dashboard",views.teacher_dashboard_view,name="teacher_dashboard"),
    path("student/dashboard",views.student_dashboard_view,name="student_dashboard"),
    path("tasks/create/",views.create_task,name="create_task"),
    path("tasks/<int:task_id>",views.task_page_view,name = "view_task"),
    path("tasks/<int:task_id>/edit",views.task_page_edit,name = "edit_task"),
    path("tasks/<int:task_id>/delete",views.task_page_delete,name = "delete_task"),
    path("group/<int:group_id>",views.student_group_view,name= "groups"),
    path("teacher/groups",views.teacher_group_view,name= "teacher_groups")

]