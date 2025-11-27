from django.shortcuts import render, redirect, get_object_or_404
from classrooms.models import ClassGroup,Subject,GroupMembership
from assignments.models import Task
from .forms import TaskCreationForm
# Create your views here.

def home_view(request):
    return render(request,"home.html")

def student_dashboard_view(request):
    student = request.user.profile
    membership = GroupMembership.objects.filter(student = student)
    groups = [m.group for m in membership]
    tasks = Task.objects.filter(group__groupmembership__student=student)
    return render(request,"dashboard/student.html", {
        "groups" : groups,
        "tasks" : tasks
    })
def teacher_dashboard_view(request):
    teacher = request.user.profile
    subject = Subject.objects.filter(teacher=teacher)
    groups = ClassGroup.objects.filter(subject__teacher=teacher)
    tasks = Task.objects.filter(created_by = teacher)
    return render(request,"dashboard/teacher.html",{
        "subject" : subject,
        "groups" : groups,
        'tasks' : tasks
    })

def create_task(request):
    teacher = request.user.profile

    allowed_groups = ClassGroup.objects.filter(subject__teacher = teacher)

    if request.method == "POST":
        form = TaskCreationForm(request.POST)
        form.fields['group'].queryset = allowed_groups

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = teacher
            task.save()
            return redirect("teacher_dashboard")

    else:
        form = TaskCreationForm()
        form.fields['group'].queryset = allowed_groups
    return render(request,"tasks/create_task.html",{"form" : form})

def task_page_view(request, task_id):
    teacher = request.user.profile
    task = get_object_or_404(Task, id = task_id, created_by = teacher)
    return render(request,'tasks/view_task.html',{"task":task})
def task_page_edit(request,task_id):
    teacher = request.user.profile

    task = get_object_or_404(Task, id = task_id,created_by = teacher)

    allowed_groups = ClassGroup.objects.filter(subject__teacher = teacher)

    if request.method == "POST":
        form = TaskCreationForm(request.POST, instance = task)
        form.fields['group'].queryset = allowed_groups

        if form.is_valid():
            form.save()
            return redirect("view_task",task_id = task.id)
    else:
        form = TaskCreationForm(instance = task)
        form.fields['group'].queryset = allowed_groups
    return render(request,"tasks/edit_task.html",{"form":form , "task" : task})
def task_page_delete(request,task_id):
    teacher = request.user.profile

    task = get_object_or_404(Task,id = task_id,created_by = teacher)

    if request.method == "POST":
        task.delete()
        return redirect("teacher_dashboard")
    return render(request,'home.html')