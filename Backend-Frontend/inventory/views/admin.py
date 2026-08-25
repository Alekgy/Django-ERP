import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from ..models import Products, Recipes, Ingredients, Branches
from ..forms import ProductForm, IngredientForm, BranchForm
from inventory.decorators import role_required

RecipeFormSet = inlineformset_factory(
    Products, 
    Recipes, 
    fields=['ingredient', 'quantity_required'], 
    extra=1, 
    can_delete=True
)

@login_required
@role_required('ADMIN_SEDE') 
def admin_panel(request):
    """Panel principal: El Owner ve todas las sedes; el Administrador local solo la suya."""
    user_profile = request.user.profile
    print("=== CONTROL DE DIAGNÓSTICO DE ROL ===")
    print(f"Usuario actual: {request.user.username}")
    print(f"¿Es Superusuario nativo?: {request.user.is_superuser}")
    print(f"Rol guardado en Base de Datos: '{user_profile.role}'")
    print(f"Sede asociada en Base de Datos: {user_profile.branch}")
    print("=====================================")
    
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        sedes = Branches.objects.all()
        productos = Products.objects.all()
        ingredientes = Ingredients.objects.all()
    else:
        if not user_profile.branch:
            messages.error(request, "Tu usuario no tiene una sede asignada para administrar.")
            return redirect('home')
            
        sedes = Branches.objects.filter(id=user_profile.branch.id)
        productos = Products.objects.filter(branch=user_profile.branch)
        ingredientes = Ingredients.objects.filter(branch=user_profile.branch)

    return render(request, 'admin_panel.html', {
        'sedes': sedes,
        'productos': productos,
        'ingredientes': ingredientes,
    })

# ==========================================
# CRUD DE PRODUCTOS (Filtrados por permisos)
# ==========================================

@login_required
@role_required('ADMIN_SEDE')
def lista_productos(request):
    user_profile = request.user.profile
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        productos = Products.objects.all()
    else:
        productos = Products.objects.filter(branch=user_profile.branch)
        
    return render(request, 'admin/lista_productos.html', {'productos': productos})

@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def crear_producto(request):
    user_profile = request.user.profile
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.id = uuid.uuid4()
            
            if not request.user.is_superuser and user_profile.role.upper() != 'OWNER':
                producto.branch = user_profile.branch
                
            producto.save()
            form.save_m2m()
            
            formset = RecipeFormSet(request.POST, instance=producto)
            if formset.is_valid():
                formset.save()
                messages.success(request, f"Producto '{producto.name}' creado con éxito.")
                return redirect('lista_productos')
    else:
        form = ProductForm()
        formset = RecipeFormSet()
        
    return render(request, 'admin/formulario_producto.html', {
    'form': form, 
    'formset': formset, 
    'edit': False
})

@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def editar_producto(request, producto_id):
    user_profile = request.user.profile
    
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        producto = get_object_or_404(Products, id=producto_id)
    else:
        producto = get_object_or_404(Products, id=producto_id, branch=user_profile.branch)
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=producto)
        formset = RecipeFormSet(request.POST, instance=producto)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Producto '{producto.name}' actualizado.")
            return redirect('lista_productos')
    else:
        form = ProductForm(instance=producto)
        formset = RecipeFormSet(instance=producto)
        
    return render(request, 'admin/formulario_producto.html', {
    'form': form, 
    'formset': formset, 
    'producto': producto,
    'edit': True
})

@login_required
@role_required('ADMIN_SEDE')
def eliminar_producto(request, producto_id):
    user_profile = request.user.profile
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        producto = get_object_or_404(Products, id=producto_id)
    else:
        producto = get_object_or_404(Products, id=producto_id, branch=user_profile.branch)
        
    if request.method == 'POST':
        producto.delete()
        messages.success(request, "Producto eliminado correctamente.")
        return redirect('lista_productos')
    return render(request, 'admin/confirm_delete.html', {'object': producto, 'type': 'Producto'})


# ==========================================
# CRUD DE INGREDIENTES
# ==========================================

@login_required
@role_required('ADMIN_SEDE')
def lista_ingredientes(request):
    user_profile = request.user.profile
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        ingredientes = Ingredients.objects.all()
    else:
        ingredientes = Ingredients.objects.filter(branch=user_profile.branch)
    return render(request, 'admin/lista_ingredientes.html', {'ingredientes': ingredientes})

@login_required
@role_required('ADMIN_SEDE')
def crear_ingrediente(request):
    user_profile = request.user.profile
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingrediente = form.save(commit=False)
            ingrediente.id = uuid.uuid4()
            if not request.user.is_superuser and user_profile.role.upper() != 'OWNER':
                ingrediente.branch = user_profile.branch
            ingrediente.save()
            messages.success(request, f"Ingrediente '{ingrediente.name}' creado con éxito.")
            return redirect('lista_ingredientes')
    else:
        form = IngredientForm()
    return render(request, 'admin/formulario_ingrediente.html', {'form': form, 'edit': False})

@login_required
@role_required('ADMIN_SEDE')
def editar_ingrediente(request, ingrediente_id):
    user_profile = request.user.profile
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        ingrediente = get_object_or_404(Ingredients, id=ingrediente_id)
    else:
        ingrediente = get_object_or_404(Ingredients, id=ingrediente_id, branch=user_profile.branch)
        
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingrediente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Ingrediente '{ingrediente.name}' actualizado.")
            return redirect('lista_ingredientes')
    else:
        form = IngredientForm(instance=ingrediente)
    return render(request, 'admin/formulario_ingrediente.html', {'form': form, 'ingrediente': ingrediente, 'edit': True})

@login_required
@role_required('ADMIN_SEDE')
def eliminar_ingrediente(request, ingrediente_id):
    user_profile = request.user.profile
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        ingrediente = get_object_or_404(Ingredients, id=ingrediente_id)
    else:
        ingrediente = get_object_or_404(Ingredients, id=ingrediente_id, branch=user_profile.branch)
        
    if request.method == 'POST':
        ingrediente.delete()
        messages.success(request, "Ingrediente eliminado correctamente.")
        return redirect('lista_ingredientes')
    return render(request, 'admin/confirm_delete.html', {'object': ingrediente, 'type': 'Ingrediente'})


# ==========================================
# CRUD DE SEDES (Exclusivo de Owners / Superusers)
# ==========================================

@login_required
@role_required('OWNER')
def lista_sedes(request):
    sedes = Branches.objects.all()
    return render(request, 'admin/lista_sedes.html', {'sedes': sedes})

@login_required
@role_required('OWNER')
def crear_sede(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            sede = form.save(commit=False)
            sede.id = uuid.uuid4()
            sede.save()
            messages.success(request, f"Sede '{sede.name}' creada exitosamente.")
            return redirect('lista_sedes')
    else:
        form = BranchForm()
    return render(request, 'admin/formulario_sede.html', {'form': form})

@login_required
@role_required('OWNER')
def editar_sede(request, sede_id):
    sede = get_object_or_404(Branches, id=sede_id)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=sede)
        if form.is_valid():
            form.save()
            messages.success(request, f"Sede '{sede.name}' actualizada.")
            return redirect('lista_sedes')
    else:
        form = BranchForm(instance=sede)
    return render(request, 'admin/formulario_sede.html', {'form': form, 'sede': sede})

@login_required
@role_required('OWNER')
def eliminar_sede(request, sede_id):
    sede = get_object_or_404(Branches, id=sede_id)
    if request.method == 'POST':
        sede.delete()
        messages.success(request, "Sede eliminada correctamente del sistema.")
        return redirect('lista_sedes')
    return render(request, 'admin/confirm_delete.html', {'object': sede, 'type': 'Sede'})