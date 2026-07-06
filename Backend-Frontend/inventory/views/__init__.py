from .public import menu_digital, procesar_pedido, home_redirect, cambiar_sede_sesion, sedes_context_processor
from .station import bartender_dashboard, completar_pedido
from .admin import admin_panel, crear_producto, editar_producto, eliminar_producto, lista_productos, crear_ingrediente, editar_ingrediente, eliminar_ingrediente, lista_ingredientes, crear_sede, editar_sede, eliminar_sede, lista_sedes
from .inventory import gestion_inventario, ver_inventario, nueva_transformacion, historial_transformaciones, modulo_caja, registrar_ingreso_mercancia, realizar_ingreso_masivo
from .users import crear_usuario_staff, lista_usuarios, editar_usuario, cambiar_password_admin, cambiar_mi_password, eliminar_usuario