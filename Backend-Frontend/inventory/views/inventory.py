import json
import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncMinute
from inventory.models import Branches, Ingredients, Inventories, Transformations, TransformationItems, Sales, InventoryMovements, PaymentMethods
from inventory.decorators import role_required

@login_required
@role_required('ADMIN_SEDE')
def gestion_inventario(request):
    """Página principal de gestión. El Owner ve todo, el administrador local su sede."""
    user_profile = request.user.profile
    
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        sedes = Branches.objects.all()
        todos_los_ingredientes = Ingredients.objects.all() 
    else:
        if not user_profile.branch:
            messages.error(request, "No tienes una sede asignada.")
            return redirect('home')
        sedes = Branches.objects.filter(id=user_profile.branch.id)
        todos_los_ingredientes = Ingredients.objects.all() 

    return render(request, 'inventory/gestion_inventario.html', {
        'sedes': sedes,
        'todos_los_ingredientes': todos_los_ingredientes
    })


@login_required
@role_required('ADMIN_SEDE')
def ver_inventario(request):
    """Visualización de existencias físicas y costos por sede."""
    user_profile = request.user.profile
    sede_id = request.GET.get('branch')
    stock_actual = []
    
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        sedes = Branches.objects.all()
    else:
        sedes = Branches.objects.filter(id=user_profile.branch.id)
        sede_id = str(user_profile.branch.id)
    
    if sede_id:
        stock_actual = Inventories.objects.filter(branch_id=sede_id).select_related('ingredient').order_by('ingredient__name')
        
    return render(request, 'inventory/ver_inventario.html', {
        'sedes': sedes,
        'stock_actual': stock_actual,
        'sede_seleccionada': sede_id
    })


@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def nueva_transformacion(request):
    """Procesamiento de recetas industriales (Pulpas/Siropes) en la Planta de Producción."""
    user_profile = request.user.profile
    
    sede_produccion = Branches.objects.filter(name__icontains='producción').first()
    if not sede_produccion:
        sede_produccion = Branches.objects.first()
        
    if not sede_produccion:
        messages.error(request, "No hay ninguna sede configurada en el sistema.")
        return redirect('home')

    if not (request.user.is_superuser or user_profile.role.upper() == 'OWNER'):
        if user_profile.branch != sede_produccion:
            messages.error(request, "Tu usuario no pertenece a la sede de Planta de Producción.")
            return redirect('home')

    if request.method == 'POST':
        try:
            result_id = request.POST.get('result_ingredient')
            qty_produced = Decimal(request.POST.get('quantity_produced'))
            materials_ids = request.POST.getlist('material_id[]')
            materials_qtys = request.POST.getlist('material_qty[]')

            transformation = Transformations.objects.create(
                id=uuid.uuid4(),
                result_ingredient_id=result_id,
                quantity_produced=qty_produced,
                cost_total=0 
            )
            total_cost = Decimal('0.00')

            for m_id, m_qty in zip(materials_ids, materials_qtys):
                m_qty = Decimal(str(m_qty))
                try:
                    inv_material = Inventories.objects.get(branch=sede_produccion, ingredient_id=m_id)
                    item_cost = (inv_material.current_unit_cost or Decimal('0.00')) * m_qty
                    total_cost += item_cost

                    inv_material.stock_level -= m_qty
                    inv_material.save()
                except Inventories.DoesNotExist:
                    raise Exception(f"El ingrediente con ID {m_id} no está en el inventario de la planta.")

                TransformationItems.objects.create(
                    id=uuid.uuid4(),
                    transformation=transformation,
                    ingredient_id=m_id,
                    quantity_used=m_qty
                )

            transformation.cost_total = total_cost
            transformation.save()

            inv_producto_final, created = Inventories.objects.get_or_create(
                branch=sede_produccion,
                ingredient_id=result_id,
                defaults={'id': uuid.uuid4(), 'stock_level': 0, 'current_unit_cost': 0}
            )
            
            stock_ant = inv_producto_final.stock_level
            costo_ant = inv_producto_final.current_unit_cost
            nuevo_stock = stock_ant + qty_produced
            
            if nuevo_stock > 0:
                nuevo_costo_promedio = ((stock_ant * costo_ant) + total_cost) / nuevo_stock
            else:
                nuevo_costo_promedio = total_cost / qty_produced

            inv_producto_final.stock_level = nuevo_stock
            inv_producto_final.current_unit_cost = nuevo_costo_promedio
            inv_producto_final.save()

            messages.success(request, f"¡Transformación procesada en {sede_produccion.name}!")
            return redirect('historial_transformaciones')

        except Exception as e:
            messages.error(request, f"Error en transformación: {str(e)}")
            
    context = {
        'productos_resultantes': Ingredients.objects.filter(category='MATERIA PRIMA').order_by('name'),
        'materias_primas': Ingredients.objects.filter(category='INSUMO').order_by('name'),
    }
    return render(request, 'production/nueva_transformacion.html', context)


@login_required
@role_required('ADMIN_SEDE')
def historial_transformaciones(request):
    transformaciones = Transformations.objects.all().order_by('-created_at').prefetch_related('items__ingredient')
    return render(request, 'production/historial_transformaciones.html', {'transformaciones': transformaciones})


@login_required
@role_required('STAFF', 'CAJERO', 'ADMIN_SEDE')
@transaction.atomic
def modulo_caja(request):
    """Módulo de Facturación. El Owner ve los cierres de todas las mesas/sedes."""
    user_profile = request.user.profile
    umbral = 200000
    
    if request.method == 'POST':
        nombre_mesa = request.POST.get('table_name')
        sede_id = request.POST.get('branch_id')
        payment_method_id = request.POST.get('payment_method_id')
        
        if not payment_method_id:
            messages.error(request, "Debes seleccionar un método de pago.")
            return redirect('modulo_caja')

        if nombre_mesa:
            query_ventas = Sales.objects.filter(table_name=nombre_mesa, is_paid=False)
            if sede_id:
                query_ventas = query_ventas.filter(branch_id=sede_id)
                
            # Actualiza tanto el estado pagado como el método de pago elegido
            query_ventas.update(
                is_paid=True,
                payment_method_id=payment_method_id
            )
            messages.success(request, f"¡{nombre_mesa} cerrada con éxito!")
            return redirect('modulo_caja')

    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        sede_filtrada_id = request.session.get('sede_activa_id')
        
        if sede_filtrada_id is None:
            primera_sede = Branches.objects.first()
            if primera_sede:
                sede_filtrada_id = str(primera_sede.id)
                request.session['sede_activa_id'] = sede_filtrada_id

        ventas_abiertas = Sales.objects.filter(is_paid=False).select_related('product', 'branch')
        ventas_cerradas = Sales.objects.filter(is_paid=True)

        if sede_filtrada_id and sede_filtrada_id != "0":
            ventas_abiertas = ventas_abiertas.filter(branch_id=sede_filtrada_id)
            ventas_cerradas = ventas_cerradas.filter(branch_id=sede_filtrada_id)
            
    else:
        if not user_profile.branch:
            messages.error(request, "Tu usuario no tiene una sede asignada para operar la caja.")
            return redirect('home')
            
        ventas_abiertas = Sales.objects.filter(is_paid=False, branch=user_profile.branch).select_related('product', 'branch')
        ventas_cerradas = Sales.objects.filter(is_paid=True, branch=user_profile.branch)

    mesas_dict = {}
    for venta in ventas_abiertas:
        mesa = venta.table_name or "Sin Mesa"
        if mesa not in mesas_dict:
            mesas_dict[mesa] = {'items': [], 'total': 0, 'branch_id': str(venta.branch_id)}
        
        mesas_dict[mesa]['items'].append({
            'nombre': venta.product.name,
            'cantidad': venta.quantity,
            'subtotal': venta.total_sale_price
        })
        mesas_dict[mesa]['total'] += float(venta.total_sale_price)

    ventas_cerradas_agrupadas = ventas_cerradas.annotate(fecha_minuto=TruncMinute('created_at'))\
        .values('table_name', 'fecha_minuto')\
        .annotate(total_cuenta=Sum('total_sale_price'))\
        .order_by('-fecha_minuto')[:10]

    # Obtenemos los métodos de pago habilitados
    metodos_pago = PaymentMethods.objects.filter(is_active=True)

    return render(request, 'inventory/caja.html', {
        'mesas_abiertas': mesas_dict,
        'mesas_cerradas': ventas_cerradas_agrupadas,
        'metodos_pago': metodos_pago,
        'umbral': umbral
    })


@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def registrar_ingreso_mercancia(request):
    user_profile = request.user.profile
    if request.method == 'POST':
        ingrediente_id = request.POST.get('ingrediente')
        sede_id = request.POST.get('sede')
        cantidad_nueva = Decimal(request.POST.get('cantidad'))
        precio_total_compra = Decimal(request.POST.get('precio_total'))
        
        ingrediente = Ingredients.objects.get(id=ingrediente_id)
        sede = Branches.objects.get(id=sede_id)
        costo_unitario_compra = precio_total_compra / cantidad_nueva
        
        InventoryMovements.objects.create(
            id=uuid.uuid4(),
            branch=sede,
            ingredient=ingrediente,
            quantity_received=cantidad_nueva,       
            total_purchase_price=precio_total_compra, 
            unit_cost_at_time=costo_unitario_compra,
            movement_type='INGRESO'
        )
        
        inventario, created = Inventories.objects.get_or_create(
            branch=sede, 
            ingredient=ingrediente,
            defaults={'id': uuid.uuid4(), 'stock_level': 0, 'current_unit_cost': 0}
        )
        
        stock_viejo = inventario.stock_level
        costo_viejo = inventario.current_unit_cost
        nuevo_stock = stock_viejo + cantidad_nueva
        nuevo_costo_promedio = ((stock_viejo * costo_viejo) + precio_total_compra) / nuevo_stock
        
        inventario.stock_level = nuevo_stock
        inventario.current_unit_cost = nuevo_costo_promedio
        inventario.last_purchase_price = costo_unitario_compra
        inventario.save()
        
        return redirect('ver_inventario')

    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        sedes_disponibles = Branches.objects.all()
    else:
        sedes_disponibles = Branches.objects.filter(id=user_profile.branch.id)

    context = {
        'ingredientes': Ingredients.objects.all(),
        'sedes': sedes_disponibles
    }
    return render(request, 'inventory/registrar_ingreso.html', context)


@login_required
@role_required('ADMIN_SEDE')
@transaction.atomic
def realizar_ingreso_masivo(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        branch_id = data.get('branch_id')
        items = data.get('items', [])

        if not branch_id or not items:
            return JsonResponse({'status': 'error', 'message': 'Faltan datos'}, status=400)

        branch = Branches.objects.get(id=branch_id)

        for item in items:
            ingrediente = Ingredients.objects.get(id=item['id'])
            cantidad_nueva = Decimal(str(item['cantidad']))
            precio_total = Decimal(str(item['precio_total']))
            costo_unitario_entrada = precio_total / cantidad_nueva

            inventario, created = Inventories.objects.get_or_create(
                branch=branch,
                ingredient=ingrediente,
                defaults={'id': uuid.uuid4(), 'stock_level': 0, 'current_unit_cost': 0}
            )

            stock_anterior = inventario.stock_level
            costo_anterior = inventario.current_unit_cost
            nuevo_stock = stock_anterior + cantidad_nueva
            
            if nuevo_stock > 0:
                nuevo_costo_promedio = ((stock_anterior * costo_anterior) + precio_total) / nuevo_stock
            else:
                nuevo_costo_promedio = costo_unitario_entrada

            inventario.stock_level = nuevo_stock
            inventario.current_unit_cost = nuevo_costo_promedio
            inventario.last_purchase_price = costo_unitario_entrada
            inventario.save()

            InventoryMovements.objects.create(
                id=uuid.uuid4(),
                branch=branch,
                ingredient=ingrediente,
                quantity_received=cantidad_nueva,
                total_purchase_price=precio_total,
                unit_cost_at_time=costo_unitario_entrada,
                movement_type='INGRESO'
            )

        return JsonResponse({'status': 'success', 'message': 'Inventario y costos actualizados.'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)