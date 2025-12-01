from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(allowed_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request,*args,**kwargs):
            print(request.user.username, getattr(request.user.profile, 'role', None))
            if not request.user.is_authenticated:
                return redirect('login')
            if hasattr(request.user,'profile') and request.user.profile.role == allowed_role:
                return view_func(request,*args,**kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator