from django.shortcuts import render,redirect
from .forms import AnnouncementForm
from .models import Announcement,ClassGroup



def create_announcement(request):
    teacher = request.user.profile
    allowed_groups = ClassGroup.objects.filter(subject__teacher = teacher)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        form.fields['group'].queryset = allowed_groups

        if form.is_valid():
            announcement = form.save(commit= False)
            announcement.created_by = teacher
            announcement.save()
            return redirect('teacher_dashboard')
    else:
        form = AnnouncementForm()
        form.fields['group'].queryset = allowed_groups
    return render(request,"teacher/create_announcement.html",{"form" : form})