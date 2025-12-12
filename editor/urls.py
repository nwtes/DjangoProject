from django.urls import path
from . import views

urlpatterns = [
    path('pyodide-editor/', views.pyodide_editor, name='pyodide_editor'),
]

