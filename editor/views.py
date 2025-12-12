from django.shortcuts import render

# Create your views here.

def pyodide_editor(request):
    return render(request, 'tasks/pyodide_editor.html')
