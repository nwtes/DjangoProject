from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import UserRegistrationForm, ProfileForm
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required

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

@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})
