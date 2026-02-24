from django.urls import path
from . import views

urlpatterns = [
    path('pyodide-editor/', views.pyodide_editor, name='pyodide_editor'),
    path('messages/', views.dm_inbox, name='dm_inbox'),
    path('messages/<int:user_id>/', views.dm_conversation, name='dm_conversation'),
]
