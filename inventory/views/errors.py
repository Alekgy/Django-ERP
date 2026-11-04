from django.shortcuts import render

def error_400(request, exception=None):
    """Manejo de peticiones incorrectas (Bad Request)."""
    context = {
        'code': '400',
        'title': 'Solicitud Inválida',
        'description': 'La solicitud enviada no pudo ser interpretada por el servidor o contiene parámetros alterados.',
        'icon': 'bi-exclamation-octagon',
    }
    return render(request, 'errors/400.html', context, status=400)


def error_403(request, exception=None):
    """Manejo de accesos no autorizados por roles/permisos."""
    context = {
        'code': '403',
        'title': 'Permiso Denegado',
        'description': 'Tu rol o cuenta de usuario no dispone de las credenciales necesarias para acceder a esta área o modificar este registro.',
        'icon': 'bi-shield-lock',
    }
    return render(request, 'errors/403.html', context, status=403)


def error_404(request, exception=None):
    """Manejo de recursos o URLs inexistentes."""
    context = {
        'code': '404',
        'title': 'Recurso o Mesa No Encontrada',
        'description': 'La comanda, plato o enlace al que intentas acceder no existe, fue archivado o se movió de área.',
        'icon': 'bi-search',
    }
    return render(request, 'errors/404.html', context, status=404)


def error_500(request):
    """Manejo de errores internos del servidor / caídas imprevistas."""
    context = {
        'code': '500',
        'title': 'Fallo Operativo del Sistema',
        'description': 'Ocurrió una interrupción al sincronizar con el servidor o la base de datos. El incidente ya fue registrado.',
        'icon': 'bi-exclamation-triangle',
    }
    return render(request, 'errors/500.html', context, status=500)


def csrf_failure(request, reason=""):
    """Manejo exclusivo para fallos de validación CSRF (reemplaza la pantalla de Django)."""
    context = {
        'code': '403',
        'title': 'Fallo de Verificación de Seguridad',
        'description': 'La sesión o el token de seguridad CSRF caducó o no es válido. Por favor recarga e intenta de nuevo.',
        'icon': 'bi-shield-x',
        'reason': reason,
    }
    return render(request, 'errors/403.html', context, status=403)