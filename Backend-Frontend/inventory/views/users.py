from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from django.db import transaction

# Importaciones absolutas
from inventory.models import UserProfile, Branches
from inventory.forms import UserCreateForm
from inventory.decorators import role_required

@login_required
@role_required('ADMIN_SEDE') # OWNER y Superuser entran automáticamente
def lista_usuarios(request):
    """Muestra los usuarios del sistema. El Owner ve a todos; el Administrador local solo a su sede."""
    user_profile = request.user.profile

    # CORTOCIRCUITO: El Owner y el Superuser ven la nómina completa del ERP
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        usuarios = User.objects.all().select_related('profile__branch').order_by('username')
        sedes = Branches.objects.all()
    else:
        # El Administrador de Sede solo ve los usuarios asignados a su sucursal
        if not user_profile.branch:
            messages.error(request, "No tienes una sede asignada para administrar usuarios.")
            return redirect('home')
            
        usuarios = User.objects.filter(profile__branch=user_profile.branch).select_related('profile__branch').order_by('username')
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
            user = form.save()
            role = form.cleaned_data.get('role')
            branch = form.cleaned_data.get('branch')

            # Seguridad: Si el que crea es un Administrador de Sede, forzamos que el nuevo empleado sea de su misma sede
            if not request.user.is_superuser and user_profile.role.upper() != 'OWNER':
                branch = user_profile.branch

            # Creamos o actualizamos el perfil de usuario asociado
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': role, 'branch': branch}
            )
            
            messages.success(request, f"Usuario '{user.username}' creado con éxito con el rol de {role}.")
            return redirect('lista_usuarios')
    else:
        form = UserCreateForm()

    return render(request, 'admin/crear_usuario.html', {'form': form})


@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def editar_usuario(request, user_id):
    """Edición de roles y sedes de los usuarios."""
    user_profile = request.user.profile
    usuario_a_editar = get_object_or_404(User, id=user_id)
    perfil_a_editar, created = UserProfile.objects.get_or_create(user=usuario_a_editar)

    # Seguridad: Un administrador de sede no puede editar a un usuario de otra sede
    if not (request.user.is_superuser or user_profile.role.upper() == 'OWNER'):
        if perfil_a_editar.branch != user_profile.branch:
            messages.error(request, "No tienes permisos para editar usuarios de otras sedes.")
            return redirect('lista_usuarios')

    if request.method == 'POST':
        nuevo_rol = request.POST.get('role')
        nueva_sede_id = request.POST.get('branch')

        # Si no es Owner/Superuser, no puede cambiar la sede a otra que no sea la suya
        if not request.user.is_superuser and user_profile.role.upper() != 'OWNER':
            nueva_sede = user_profile.branch
        else:
            nueva_sede = Branches.objects.filter(id=nueva_sede_id).first() if nueva_sede_id else None

        perfil_a_editar.role = nuevo_rol
        perfil_a_editar.branch = nueva_sede
        perfil_a_editar.save()

        messages.success(request, f"Perfil de '{usuario_a_editar.username}' actualizado correctamente.")
        return redirect('lista_usuarios')

    sedes_disponibles = Branches.objects.all() if (request.user.is_superuser or user_profile.role.upper() == 'OWNER') else Branches.objects.filter(id=user_profile.branch.id)

    return render(request, 'admin/editar_usuario.html', {
        'usuario_a_editar': usuario_a_editar,
        'perfil_a_editar': perfil_a_editar,
        'sedes': sedes_disponibles
    })


@login_required
@role_required('OWNER') # Candado estricto: Solo el dueño o superuser resetea claves ajenas
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

    return render(request, 'admin/cambiar_password_admin.html', {'usuario': usuario})


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
        update_session_auth_hash(request, user) # Evita que se cierre la sesión actual
        
        messages.success(request, "Tu contraseña ha sido actualizada con éxito.")
        return redirect('home')

    return render(request, 'admin/cambiar_password_solo.html')


@login_required
@role_required('OWNER') # Candado estricto: Un administrador local no puede borrar cuentas
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