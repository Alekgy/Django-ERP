import json
import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from inventory.models import Products, Sales, Branches

def menu_digital(request, n_mesa, sede_id=None):
    """Vista pública para el cliente adaptada a la sede y mesa real usando el QR."""
    if sede_id is None:
        sede = Branches.objects.first()
    else:
        sede = get_object_or_404(Branches, id=sede_id)
        
    if not sede:
        return render(request, 'inventory/error.html', {'mensaje': 'No hay ninguna sede configurada en el ERP.'})

    # MODIFICACIÓN: Separar los productos por su área de preparación
    productos_cocina = Products.objects.filter(preparation_area='COCINA', is_active=True)
    productos_bar = Products.objects.filter(preparation_area='BAR', is_active=True)

    return render(request, 'inventory/menu_digital.html', {
        'productos_cocina': productos_cocina,  # <-- Nueva variable
        'productos_bar': productos_bar,        # <-- Nueva variable
        'sede_id': sede.id,
        'nombre_sede': sede.name,
        'n_mesa': n_mesa
    })

@csrf_exempt
@transaction.atomic
def procesar_pedido(request, sede_id):
    """Lógica optimizada (Bulk Create) para recibir el JSON del carrito en un solo query."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
        
    try:
        sede = Branches.objects.get(id=sede_id)
        data = json.loads(request.body)
        items = data.get('items', [])
        n_mesa = data.get('n_mesa', 'Barra')
        
        if not items:
            return JsonResponse({'status': 'error', 'message': 'El carrito está vacío.'}, status=400)

        producto_ids = list(set(item['id'] for item in items))
        productos_db = Products.objects.filter(id__in=producto_ids)
        
        productos_map = {str(p.id): p for p in productos_db}
        ventas_a_crear = []
        
        for item in items:
            p_id = str(item['id'])
            producto = productos_map.get(p_id)
            
            if not producto:
                raise Exception(f"El producto con ID {p_id} no está disponible.")
            
            cantidad = int(item.get('cantidad', 1))
            precio_total = producto.sale_price * cantidad
            
            ventas_a_crear.append(
                Sales(
                    id=uuid.uuid4(),
                    branch_id=sede.id,
                    product=producto,
                    quantity=cantidad,
                    total_sale_price=precio_total,
                    table_name=f"Mesa {n_mesa}"
                )
            )
            
        Sales.objects.bulk_create(ventas_a_crear)
        
        return JsonResponse({'status': 'success', 'message': '¡Pedido enviado a la barra!'})
        
    except Branches.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'La sede de este código QR no existe.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def home_redirect(request):
    user_profile = request.user.profile
    rol_actual = user_profile.role.upper() if user_profile.role else ""
    
    sedes_selector = Branches.objects.all()
    
    if request.user.is_superuser or rol_actual == 'OWNER':
        sede_sesion_id = request.session.get('sede_activa_id')
        
        if sede_sesion_id and sede_sesion_id != "0":
            sede_actual = Branches.objects.filter(id=sede_sesion_id).first()
            nombre_sede = f"Sede: {sede_actual.name}" if sede_actual else "Consolidado Global"
            es_owner = True
        else:
            nombre_sede = "Consolidado Global"
            es_owner = True
    else:
        nombre_sede = user_profile.branch.name if user_profile.branch else "Sin Sede Asignada"
        es_owner = False

    return render(request, 'home.html', {
        'nombre_sede': nombre_sede,
        'es_owner': es_owner,
        'sedes_selector': sedes_selector
    })

@login_required
def cambiar_sede_sesion(request, branch_id):
    """
    Permite al Owner/Superuser alternar entre sedes de forma global usando UUID o 0.
    """
    if not request.user.is_superuser and (not request.user.profile.role or request.user.profile.role.upper() != 'OWNER'):
        messages.error(request, "No tienes permisos para cambiar de sede de forma global.")
        return redirect('home')

    if str(branch_id) == "0":
        request.session['sede_activa_id'] = "0"
        messages.success(request, "Visualizando el Consolidado Global de todas las sedes.")
    else:
        sede = get_object_or_404(Branches, id=branch_id)
        request.session['sede_activa_id'] = str(sede.id)
        messages.success(request, f"Cambiado a vista de sede: {sede.name}")

    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'home')


def sedes_context_processor(request):
    """
    Inyecta el selector de sedes en TODOS los templates del proyecto de forma global.
    Evita errores de Attribute o variables faltantes al navegar entre rutas.
    """
    if not request.user.is_authenticated:
        return {}

    user_profile = getattr(request.user, 'profile', None)
    rol_actual = user_profile.role.upper() if user_profile and user_profile.role else ""
    
    sedes_selector = Branches.objects.all()
    sede_activa_id = request.session.get('sede_activa_id')
    
    if request.user.is_superuser or rol_actual == 'OWNER':
        if sede_activa_id == "0":
            sede_activa_nombre = "Consolidado Global"
        elif sede_activa_id:
            sede_actual = Branches.objects.filter(id=sede_activa_id).first()
            sede_activa_nombre = sede_actual.name if sede_actual else "Consolidado Global"
        else:
            primera_sede = Branches.objects.first()
            sede_activa_nombre = primera_sede.name if primera_sede else "Consolidado Global"
    else:
        if user_profile and user_profile.branch:
            sede_activa_nombre = getattr(user_profile.branch, 'name', str(user_profile.branch))
        else:
            sede_activa_nombre = "Sin Sede Asignada"

    return {
        'sedes_selector': sedes_selector,
        'sede_activa_nombre': sede_activa_nombre
    }