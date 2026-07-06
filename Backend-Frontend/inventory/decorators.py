# inventory/decorators.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*allowed_roles):
    """
    Decorador personalizado para controlar el acceso basado en el UserProfile del ERP.
    Soporta múltiples roles combinados. El Superuser de Django siempre tiene acceso.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login') 
                
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            if hasattr(request.user, 'profile') and request.user.profile.role:
                user_role = request.user.profile.role.upper() 
                allowed_roles_upper = [role.upper() for role in allowed_roles]
                
                if user_role in allowed_roles_upper or user_role == 'OWNER':
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, "No tienes permisos suficientes para acceder a esta sección.")
            raise PermissionDenied
            
        return _wrapped_view
    return decorator