from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.contrib.auth import login
from inventory.models import UserProfile, Branches
from inventory.forms import UserCreateForm
from inventory.decorators import role_required


def demo_login(request):
    """Inicia sesión con un usuario demo sin pedir credenciales."""
    # Busca el usuario demo o tu usuario de pruebas principal
    demo_user = User.objects.filter(is_superuser=True).first()  # o: User.objects.filter(username='tu_usuario_demo').first()
    
    if demo_user:
        login(request, demo_user)
        messages.info(request, "Accediste en Modo Demo.")
        return redirect('admin_panel')
    
    messages.error(request, "No se encontró el usuario demo.")
    return redirect('login')


@login_required
@role_required('ADMIN_SEDE')
def lista_usuarios(request):
    """Muestra los usuarios del sistema. El Owner ve a todos; el Administrador local solo a su sede."""
    user_profile = request.user.profile

    queryset_base = User.objects.exclude(is_superuser=True).select_related('profile', 'profile__branch')

    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        usuarios = queryset_base.order_by('username')
        sedes = Branches.objects.all()
    else:
        if not user_profile.branch:
            messages.error(request, "No tienes una sede asignada para administrar usuarios.")
            return redirect('home')
            
        usuarios = queryset_base.filter(profile__branch=user_profile.branch).order_by('username')
        sedes = Branches.objects.filter(id=user_profile.branch.id)

    return render(request, 'admin/lista_usuarios.html', {
        'usuarios': usuarios,
        'sedes': sedes
    })


@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def crear_usuario_staff(request):
    """Permite registrar nuevos empleados en el sistema."""
    user_profile = request.user.profile
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            role = form.cleaned_data.get('role')
            branch = form.cleaned_data.get('branch')

            if not request.user.is_superuser and user_profile.role.upper() != 'OWNER':
                branch = user_profile.branch

            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': role, 'branch': branch}
            )
            
            messages.success(request, f"Usuario '{user.username}' creado con éxito con el rol de {role}.")
            return redirect('lista_usuarios')
    else:
        form = UserCreateForm()

    return render(request, 'admin/formulario_usuario.html', {'form': form})


@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def editar_usuario(request, user_id):
    """Edición de roles y sedes de los usuarios usando el mismo formulario."""
    user_profile = request.user.profile
    usuario = get_object_or_404(User, id=user_id)
    
    es_admin_superior = request.user.is_superuser or user_profile.role.upper() == 'OWNER'
    es_mismo_usuario = request.user.id == usuario.id

    if not (es_admin_superior or es_mismo_usuario):
        messages.error(request, "No tienes permiso para acceder a este perfil.")
        return redirect('home')

    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, "No tienes permiso para editar al usuario Master.")
        return redirect('lista_usuarios')

    perfil, created = UserProfile.objects.get_or_create(user=usuario)
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST, instance=usuario)
        
        if 'password' in form.fields: 
            del form.fields['password']

        if not es_admin_superior:
            if 'role' in form.fields: del form.fields['role']
            if 'branch' in form.fields: del form.fields['branch']

        if form.is_valid():
            user_saved = form.save() 
            
            if es_admin_superior:
                perfil.role = form.cleaned_data.get('role', perfil.role)
                perfil.branch = form.cleaned_data.get('branch', perfil.branch) if perfil.role != 'OWNER' else None
                perfil.save()
            
            messages.success(request, f"Datos de {user_saved.username} actualizados correctamente.")
            return redirect('lista_usuarios') if es_admin_superior else redirect('home')
    else:
        form = UserCreateForm(instance=usuario, initial={
            'role': perfil.role,
            'branch': perfil.branch
        })
        
        if 'password' in form.fields: 
            del form.fields['password']
            
        if not es_admin_superior:
            if 'role' in form.fields: form.fields['role'].widget = forms.HiddenInput()
            if 'branch' in form.fields: form.fields['branch'].widget = forms.HiddenInput()

    return render(request, 'admin/formulario_usuario.html', {'form': form, 'editando': True})


@login_required
@role_required('OWNER') 
def cambiar_password_admin(request, user_id):
    """Permite al Owner forzar el cambio de contraseña de un empleado."""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_p = request.POST.get('new_password')
        conf_p = request.POST.get('confirm_password')

        if not new_p or new_p != conf_p:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('cambiar_password_admin', user_id=user_id)

        if len(new_p) < 4:
            messages.error(request, "Debe tener al menos 4 caracteres.")
            return redirect('cambiar_password_admin', user_id=user_id)

        usuario.set_password(new_p)
        usuario.save()
        messages.success(request, f"Contraseña de '{usuario.username}' actualizada con éxito.")
        return redirect('lista_usuarios')

    return render(request, 'admin/cambiar_password_solo.html', {'usuario': usuario})


@login_required
def cambiar_mi_password(request):
    """Permite a cualquier usuario logueado cambiar su propia contraseña."""
    user = request.user
    if request.method == 'POST':
        old_p = request.POST.get('old_password')
        new_p = request.POST.get('new_password')
        conf_p = request.POST.get('confirm_password')

        if not user.check_password(old_p):
            messages.error(request, "La contraseña actual es incorrecta.", extra_tags='new_pass_error')
            return redirect('cambiar_mi_password')

        if not new_p or new_p != conf_p:
            messages.error(request, "Las nuevas contraseñas no coinciden.", extra_tags='new_pass_error')
            return redirect('cambiar_mi_password')

        if len(new_p) < 4:
            messages.error(request, "Debe tener al menos 4 caracteres.", extra_tags='new_pass_error')
            return redirect('cambiar_mi_password')

        user.set_password(new_p)
        user.save()
        update_session_auth_hash(request, user)
        
        messages.success(request, "Tu contraseña ha sido actualizada con éxito.")
        return redirect('home')

    return render(request, 'admin/cambiar_password_solo.html')


@login_required
@role_required('OWNER') 
def eliminar_usuario(request, user_id):
    """Eliminación definitiva de un usuario."""
    if request.method == 'POST':
        usuario = get_object_or_404(User, id=user_id)
        
        if usuario == request.user:
            messages.error(request, "No puedes eliminar tu propia cuenta.")
        else:
            usuario.delete()
            messages.success(request, "Usuario eliminado correctamente.")
            
        return redirect('lista_usuarios')
    return redirect('lista_usuarios')