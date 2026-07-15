from django.http import JsonResponse
from django.db.models import Sum
from django.db.models.functions import ExtractWeekDay, ExtractWeek, ExtractYear, ExtractQuarter, ExtractMonth, ExtractHour
from django.utils import timezone
from datetime import timedelta 
from ..models import Sales, Products, Branches
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from ..decorators import role_required


@login_required
@role_required('ADMIN_SEDE')
def reportes_panel(request):
    """Renderiza el panel visual de reportes y gráficas filtrado por sede si aplica."""
    user_profile = request.user.profile
    
    # Aplicamos la misma lógica de permisos que tienes en el admin_panel
    if request.user.is_superuser or user_profile.role.upper() == 'OWNER':
        # Dueños ven todos los productos activos
        productos = Products.objects.filter(is_active=True).order_by('name')
    else:
        if not user_profile.branch:
            messages.error(request, "Tu usuario no tiene una sede asignada para ver estadísticas.")
            return redirect('home')
            
        # Administradores locales solo ven los productos de su sede
        productos = Products.objects.filter(branch=user_profile.branch, is_active=True).order_by('name')

    return render(request, 'admin/graficos.html', {
        'productos': productos,
    })

def api_ventas_producto_semana(request):
    producto_id = request.GET.get('producto_id')
    semana_seleccionada = request.GET.get('semana') # Capturamos el nuevo parámetro
    
    dias_semana_nombres = {
        2: "Lunes", 3: "Martes", 4: "Miércoles", 
        5: "Jueves", 6: "Viernes", 7: "Sábado", 1: "Domingo"
    }
    
    ventas_por_dia = {dia: 0 for dia in dias_semana_nombres.values()}

    if producto_id:
        # Filtro base
        filtros = {
            'product_id': producto_id,
            'is_paid': True
        }
        
        # Si nos pasan una semana específica, filtramos por el número de semana
        if semana_seleccionada:
            # Creamos un queryset anotado con el número de semana para poder aplicar el filtro
            ventas_query = (
                Sales.objects.annotate(num_semana=ExtractWeek('created_at'))
                .filter(**filtros, num_semana=int(semana_seleccionada))
                .annotate(dia_semana=ExtractWeekDay('created_at'))
                .values('dia_semana')
                .annotate(total_cantidad=Sum('quantity'))
            )
        else:
            # Si no hay semana seleccionada (comportamiento anterior/total acumulado)
            ventas_query = (
                Sales.objects.filter(**filtros)
                .annotate(dia_semana=ExtractWeekDay('created_at'))
                .values('dia_semana')
                .annotate(total_cantidad=Sum('quantity'))
            )

        for registro in ventas_query:
            num_dia = registro['dia_semana']
            nombre_dia = dias_semana_nombres.get(num_dia)
            if nombre_dia:
                ventas_por_dia[nombre_dia] = registro['total_cantidad'] or 0

    return JsonResponse({
        'labels': list(ventas_por_dia.keys()),
        'valores': list(ventas_por_dia.values())
    })

def api_ventas_historico_semanal(request):
    # Definimos el rango: hace 3 meses hasta hoy
    hace_tres_meses = timezone.now() - timedelta(days=90)
    
    # Agrupamos por año y número de semana para que no se mezclen si cruzas fin de año
    ventas_semanales = (
        Sales.objects.filter(
            is_paid=True, 
            created_at__gte=hace_tres_meses
        )
        .annotate(
            semana=ExtractWeek('created_at'),
            ano=ExtractYear('created_at')
        )
        .values('semana', 'ano')
        .annotate(total_ventas=Sum('total_sale_price'))
        .order_by('ano', 'semana')
    )
    
    labels = []
    valores = []
    
    for registro in ventas_semanales:
        # Generamos una etiqueta legible como "Semana 18" o "S18 - 2026"
        labels.append(f"Sem S{registro['semana']}")
        valores.append(float(registro['total_ventas'] or 0))
        
    return JsonResponse({
        'labels': labels,
        'valores': valores
    })

def aplicar_filtro_temporal(queryset, tipo_filtro, valor_filtro):
    """Función auxiliar para reutilizar la lógica de filtrado temporal en SQL."""
    if not tipo_filtro or not valor_filtro:
        return queryset

    # CORREGIDO: Se cambió 'valor_filter' por 'valor_filtro'
    valor = int(valor_filtro) if isinstance(valor_filtro, str) and valor_filtro.isdigit() else int(valor_filtro)

    if tipo_filtro == 'semana':
        return queryset.annotate(temp_semana=ExtractWeek('created_at')).filter(temp_semana=valor)
    
    elif tipo_filtro == 'trimestre':
        return queryset.annotate(temp_trimestre=ExtractQuarter('created_at')).filter(temp_trimestre=valor)
    
    elif tipo_filtro == 'semestre':
        # CORREGIDO: Extrae de forma segura con ExtractMonth que ya incluimos en los imports superiores
        queryset = queryset.annotate(temp_mes=ExtractMonth('created_at'))
        if valor == 1:
            return queryset.filter(temp_mes__gte=1, temp_mes__lte=6)
        elif valor == 2:
            return queryset.filter(temp_mes__gte=7, temp_mes__lte=12)
            
    return queryset


def api_ventas_metodos_pago(request):
    """Retorna la distribución de ventas según el método de pago con filtros temporales."""
    tipo_filtro = request.GET.get('tipo_filtro')
    valor_filtro = request.GET.get('valor_filtro')

    queryset = Sales.objects.filter(is_paid=True)
    queryset = aplicar_filtro_temporal(queryset, tipo_filtro, valor_filtro)

    ventas = (
        queryset.values('payment_method__name')
        .annotate(total=Sum('total_sale_price'))
        .order_by('-total')
    )
    
    labels = [v['payment_method__name'] for v in ventas if v['payment_method__name']]
    valores = [float(v['total']) for v in ventas]

    return JsonResponse({'labels': labels, 'valores': valores})


def api_ventas_por_sede(request):
    """Retorna el total de ventas acumuladas por cada sede con filtros temporales."""
    tipo_filtro = request.GET.get('tipo_filtro')
    valor_filtro = request.GET.get('valor_filtro')

    queryset = Sales.objects.filter(is_paid=True)
    queryset = aplicar_filtro_temporal(queryset, tipo_filtro, valor_filtro)

    ventas_sedes = (
        queryset.values('branch__name')
        .annotate(total=Sum('total_sale_price'))
        .order_by('-total')
    )
    
    labels = []
    valores = []
    for registro in ventas_sedes:
        nombre_sede = registro['branch__name'] or 'General / Barra'
        labels.append(nombre_sede)
        valores.append(float(registro['total']))
        
    return JsonResponse({'labels': labels, 'valores': valores})

def api_margen_ganancia_productos(request):
    """Retorna el Top 10 de productos con sus ventas totales contra sus costos teóricos totales."""
    ventas = (
        Sales.objects.filter(is_paid=True)
        .values('product__name')
        .annotate(
            ingresos_totales=Sum('total_sale_price'),
            costos_totales=Sum('total_cost_at_sale') # Ya calcula tu modelo en el .save()[cite: 16]
        )
        .order_by('-ingresos_totales')[:10] # Tomamos el Top 10 para evitar ruido visual
    )

    labels = [v['product__name'] for v in ventas]
    ingresos = [float(v['ingresos_totales'] or 0) for v in ventas]
    costos = [float(v['costos_totales'] or 0) for v in ventas]

    return JsonResponse({
        'labels': labels,
        'ingresos': ingresos,
        'costos': costos
    })


def api_horas_pico_ventas(request):
    """Retorna la cantidad de comandas atendidas agrupadas por bloques horarios."""
    ventas_horarias = (
        Sales.objects.filter(is_paid=True)
        .annotate(hora=ExtractHour('created_at'))
        .values('hora')
        .annotate(total_pedidos=Sum('quantity')) # Sumamos la cantidad física de platos/bebidas
        .order_by('hora')
    )

    # Formateamos las horas a formato legible de 12 horas (AM/PM)
    labels_horas = {
        12: "12 PM", 13: "1 PM", 14: "2 PM", 
        19: "7 PM", 20: "8 PM", 21: "9 PM", 22: "10 PM", 23: "11 PM"
    }

    valores_por_hora = {label: 0 for label in labels_horas.values()}

    for registro in ventas_horarias:
        hora_num = registro['hora']
        label_legible = labels_horas.get(hora_num)
        if label_legible:
            valores_por_hora[label_legible] = registro['total_pedidos'] or 0

    return JsonResponse({
        'labels': list(valores_por_hora.keys()),
        'valores': list(valores_por_hora.values())
    })