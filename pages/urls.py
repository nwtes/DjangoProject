from django.urls import path
from . import views

urlpatterns = [
    path("",views.home_view,name="home"),
    path("teacher/dashboard",views.teacher_dashboard_view,name="teacher_dashboard"),
    path("teacher/analytics",views.teacher_analytics_view,name="teacher_analytics"),
    path("student/dashboard",views.student_dashboard_view,name="student_dashboard"),
    path("tasks/create/",views.create_task,name="create_task"),
    path("tasks/<int:task_id>",views.task_page_view,name = "view_task"),
    path("tasks/<int:task_id>/edit",views.task_page_edit,name = "edit_task"),
    path("tasks/<int:task_id>/delete",views.task_page_delete,name = "delete_task"),
    path("group",views.student_group_view,name= "groups"),
    path('group/<int:group_id>/' , views.student_group , name = 'group'),
    path("teacher/groups",views.teacher_group_view,name= "teacher_groups"),
    path("site-admin/", views.admin_dashboard_view, name="admin_dashboard"),
    path("site-admin/users/", views.admin_users_view, name="admin_users"),
    path("site-admin/users/<int:user_id>/edit/", views.admin_user_edit_view, name="admin_user_edit"),
    path("site-admin/subjects/", views.admin_subjects_view, name="admin_subjects"),
    path("site-admin/subjects/<int:subject_id>/edit/", views.admin_subject_edit_view, name="admin_subject_edit"),
    path("site-admin/groups/", views.admin_groups_view, name="admin_groups"),
    path("site-admin/groups/<int:group_id>/", views.admin_group_detail_view, name="admin_group_detail"),
]

