from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm
from .models import Profile
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView

# Create your views here.
def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()

            role = form.cleaned_data['role']
            user.profile.role = role
            user.profile.save()
            login(request,user)
            return redirect("home")
    else:
        form = UserRegistrationForm()

    return render(request,'accounts/register.html',{"form":form})

class RoleBasedLoginView(LoginView):

    def get_success_url(self):
        user = self.request.user
        role = user.profile.role

        if role == "teacher":
            return "/teacher/dashboard"
        elif role == "student":
            return "/student/dashboard"
        else:
            return "/"