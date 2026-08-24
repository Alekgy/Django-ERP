from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from inventory.models import Sales, Inventories, Branches
from inventory.decorators import role_required

def obtener_ordenes_agrupadas(request, area_preparacion):
    """
    Función utilitaria para evitar repetir código. 
    Filtra y agrupa las ventas según el área ('BAR' o 'COCINA').
    """
    user_profile = request.user.profile
    
    # FILTRO CLAVE: Filtramos por el preparation_area del producto vinculado a la venta
    ventas_base = Sales.objects.filter(
        is_prepared=False, 
        is_paid=False,
        product__preparation_area=area_preparacion
    ).order_by('created_at').select_related('product', 'branch')
    
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        sede_filtrada_id = request.session.get('sede_activa_id')
        
        if sede_filtrada_id is None:
            primera_sede = Branches.objects.first()
            if primera_sede:
                sede_filtrada_id = str(primera_sede.id)
                request.session['sede_activa_id'] = sede_filtrada_id

        if sede_filtrada_id and sede_filtrada_id != "0":
            ventas_base = ventas_base.filter(branch_id=sede_filtrada_id)
            
    else:
        if not user_profile.branch:
            return None
        ventas_base = ventas_base.filter(branch_id=user_profile.branch.id)
        
    mesas_con_productos = {}
    for venta in ventas_base:
        if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
            nombre_sede = venta.branch.name if venta.branch else "Global"
            mesa_actual = f"{venta.table_name or 'Barra'} ({nombre_sede})"
        else:
            mesa_actual = venta.table_name or "Barra"
            
        producto = venta.product
        producto_id = str(producto.id)
        
        if mesa_actual not in mesas_con_productos:
            mesas_con_productos[mesa_actual] = {}
            
        if producto_id in mesas_con_productos[mesa_actual]:
            mesas_con_productos[mesa_actual][producto_id]['cantidad'] += venta.quantity
        else:
            mesas_con_productos[mesa_actual][producto_id] = {
                'producto': producto,
                'cantidad': venta.quantity,
                'sale_id_referencia': venta.id 
            }

    ordenes_agrupadas = {}
    for mesa, productos_dict in mesas_con_productos.items():
        ordenes_agrupadas[mesa] = list(productos_dict.values())
        
    return ordenes_agrupadas


@login_required
@role_required('STAFF', 'BARTENDER', 'ADMIN_SEDE')
def bartender_dashboard(request):
    """Muestra exclusivamente las comandas destinadas a la Barra."""
    ordenes = obtener_ordenes_agrupadas(request, area_preparacion='BAR')
    if ordenes is None:
        messages.error(request, "Tu usuario no tiene una sede asignada para operar la barra.")
        return redirect('home')
        
    return render(request, 'inventory/bartender_dashboard.html', {'ordenes': ordenes, 'area': 'Barra'})


@login_required
@role_required('STAFF', 'CHEF', 'ADMIN_SEDE')  # Puedes agregar el rol 'CHEF' si lo deseas en el futuro
def kitchen_dashboard(request):
    """Muestra exclusivamente las comandas destinadas a la Cocina."""
    ordenes = obtener_ordenes_agrupadas(request, area_preparacion='COCINA')
    if ordenes is None:
        messages.error(request, "Tu usuario no tiene una sede asignada para operar la cocina.")
        return redirect('home')
        
    return render(request, 'inventory/kitchen_dashboard.html', {'ordenes': ordenes, 'area': 'Cocina'})


@login_required
@role_required('STAFF', 'BARTENDER', 'CHEF', 'ADMIN_SEDE')
@transaction.atomic
def completar_pedido(request, sale_id):
    """
    Despacha las comandas pendientes de una mesa, pero filtrando ESTRICTAMENTE 
    por el área del producto de referencia para no mezclar cocina y barra.
    """
    if request.method == 'POST':
        venta_referencia = get_object_or_404(Sales, id=sale_id)
        area_actual = venta_referencia.product.preparation_area
        
        # Filtramos para que solo afecte a las órdenes de la misma mesa, misma sede, misma área y que no estén preparadas
        ventas_a_preparar = Sales.objects.filter(
            branch_id=venta_referencia.branch_id,
            table_name=venta_referencia.table_name,
            product__preparation_area=area_actual,
            is_prepared=False
        ).select_related('product')
        
        for venta in ventas_a_preparar:
            for item in venta.product.recipes_set.all():
                try:
                    inventario_item = Inventories.objects.get(
                        branch_id=venta.branch_id, 
                        ingredient=item.ingredient
                    )
                    cantidad_a_descontar = item.quantity_required * venta.quantity
                    
                    inventario_item.stock_level -= cantidad_a_descontar
                    inventario_item.save()
                    
                except Inventories.DoesNotExist:
                    pass
            
            venta.is_prepared = True
            venta.save()
        
        messages.success(request, f"¡Pedido de {venta_referencia.table_name} ({area_actual}) despachado e inventario descontado!")
        
        # Redirigir dinámicamente a la pantalla que originó el despacho
        if area_actual == 'COCINA':
            return redirect('kitchen_dashboard')
        return redirect('bartender_dashboard')
        
    return redirect('home')