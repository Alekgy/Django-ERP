from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from inventory import views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.home_redirect, name='home'),
    path('cambiar-sede/<str:branch_id>/', views.cambiar_sede_sesion, name='cambiar_sede_sesion'),
    
    # Menú y Pedidos
    path('menu/<int:n_mesa>/', views.menu_digital, name='menu_digital_local'),
    path('menu/<uuid:sede_id>/mesa/<int:n_mesa>/', views.menu_digital, name='menu_digital'),
    path('api/<uuid:sede_id>/pedido/', views.procesar_pedido, name='procesar_pedido'),
    
    # Dashboard de Barra
    path('barra/', views.bartender_dashboard, name='bartender_dashboard'),
    path('barra/completar/<uuid:sale_id>/', views.completar_pedido, name='completar_pedido_barra'),
    
    # Dashboard de Cocina
    path('cocina/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('cocina/completar/<uuid:sale_id>/', views.completar_pedido, name='completar_pedido_cocina'),
    
    # Inventario
    path('inventario/ingreso/', views.gestion_inventario, name='gestion_inventario'),
    path('inventario/api/ingreso-masivo/', views.realizar_ingreso_masivo, name='realizar_ingreso_masivo'),
    path('inventario/ver/', views.ver_inventario, name='ver_inventario'),
    
    # Panel de Administración personalizado
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    
    # CRUD Productos
    path('admin-panel/productos/', views.lista_productos, name='lista_productos'),
    path('admin-panel/productos/nuevo/', views.crear_producto, name='crear_producto'),
    path('admin-panel/productos/eliminar/<uuid:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('admin-panel/productos/editar/<uuid:producto_id>/', views.editar_producto, name='editar_producto'),
    
    # CRUD Ingredientes
    path('admin-panel/ingredientes/', views.lista_ingredientes, name='lista_ingredientes'),
    path('admin-panel/ingredientes/nuevo/', views.crear_ingrediente, name='crear_ingrediente'),
    path('admin-panel/ingredientes/editar/<uuid:ingrediente_id>/', views.editar_ingrediente, name='editar_ingrediente'),
    path('admin-panel/ingredientes/eliminar/<uuid:ingrediente_id>/', views.eliminar_ingrediente, name='eliminar_ingrediente'),
    
    # CRUD Sedes
    path('admin-panel/sedes/', views.lista_sedes, name='lista_sedes'),
    path('admin-panel/sedes/nuevo/', views.crear_sede, name='crear_sede'),
    path('admin-panel/sedes/editar/<uuid:sede_id>/', views.editar_sede, name='editar_sede'),
    path('admin-panel/sedes/eliminar/<uuid:sede_id>/', views.eliminar_sede, name='eliminar_sede'),
    
    # Transformaciones
    path('transformaciones/nueva/', views.nueva_transformacion, name='nueva_transformacion'),
    path('transformaciones/historial/', views.historial_transformaciones, name='historial_transformaciones'),
    
    # Graficos
    path('admin-panel/reportes/', views.reportes_panel, name='reportes'),
    path('api/ventas-producto-semana/', views.api_ventas_producto_semana, name='api_ventas_producto_semana'),
    path('api/ventas-historico-semanal/', views.api_ventas_historico_semanal, name='api_ventas_historico_semanal'),
    path('api/ventas-metodos-pago/', views.api_ventas_metodos_pago, name='api_ventas_metodos_pago'),
    path('api/ventas-por-sede/', views.api_ventas_por_sede, name='api_ventas_por_sede'),
    path('api/margen-ganancia-productos/', views.api_margen_ganancia_productos, name='api_margen_ganancia_productos'),
    path('api/horas-pico-ventas/', views.api_horas_pico_ventas, name='api_horas_pico_ventas'),
    
    # Módulo de Caja
    path('caja/', views.modulo_caja, name='modulo_caja'),
    
    # Gestión de Usuarios y Personal
    path('admin-panel/usuarios/nuevo/', views.crear_usuario_staff, name='crear_usuario_staff'),
    path('admin-panel/usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('admin-panel/usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('admin-panel/usuarios/eliminar/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('admin-panel/usuarios/cambiar-password/<int:user_id>/', views.cambiar_password_admin, name='cambiar_password_admin'),
    path('perfil/cambiar-password/', views.cambiar_mi_password, name='cambiar_mi_password'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)