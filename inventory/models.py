import uuid
from django.db import models
from decimal import Decimal

# ==========================================
# 1. Modelos de Soporte (Tablas maestras)
# ==========================================

class UnitMeasures(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    abbreviation = models.TextField()

    class Meta:
        managed = True
        db_table = 'unit_measures'

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
    
class PaymentMethods(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField() # Ej: "Efectivo", "Tarjeta Débito/Crédito"
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'payment_methods'

    def __str__(self):
        return self.name


class Branches(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    address = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'branches'

    def __str__(self):
        return self.name


# ==========================================
# 2. Modelos de Inventario
# ==========================================

class Ingredients(models.Model):
    CATEGORY_CHOICES = [
        ('INSUMO', 'Insumo'),
        ('MATERIA PRIMA', 'Materia Prima'),
        ('LICOR', 'Licores y Destilados'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    min_stock_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_measure = models.ForeignKey(UnitMeasures, models.DO_NOTHING, blank=True, null=True, db_column='unit_measure_id')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Campos de auditoría agregados (coincidentes con Supabase)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)  # Para soft-deletes si los usas en la DB

    class Meta:
        managed = True
        db_table = 'ingredients'

    def __str__(self):
        return self.name


class Inventories(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branches, models.DO_NOTHING, db_column='branch_id')
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING, db_column='ingredient_id')
    stock_level = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    last_purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_unit_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'inventories'
        unique_together = (('branch', 'ingredient'),)


# ==========================================
# 3. Productos y Recetas
# ==========================================

class Products(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(blank=True, null=True)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    production_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    # Soporte para ambas columnas de imagen presentes en tu SQL
    image_path = models.ImageField(upload_to='media_erp/', null=True, blank=True)
    image_url = models.TextField(blank=True, null=True) 
    
    # Campos de auditoría agregados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    AREA_CHOICES = [
        ('BAR', 'Barra de Cócteles'),
        ('COCINA', 'Cocina / Alimentos'),
    ]
    preparation_area = models.CharField(
        max_length=15, 
        choices=AREA_CHOICES, 
        default='BAR'
    )
    class Meta:
        managed = True
        db_table = 'products'

    def __str__(self):
        return self.name

    def calculate_theoretical_cost(self, branch_id):
        if not branch_id:
            return Decimal('0.00')
            
        total = Decimal('0.00')
        for item in self.recipes_set.all():
            try:
                inventario_item = Inventories.objects.get(branch_id=branch_id, ingredient=item.ingredient)
                costo_ingrediente = inventario_item.current_unit_cost or Decimal('0.00')
            except Inventories.DoesNotExist:
                costo_ingrediente = Decimal('0.00')
                
            total += item.quantity_required * costo_ingrediente
        return total


class Recipes(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Products, models.DO_NOTHING, related_name='recipes_set', db_column='product_id')
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING, db_column='ingredient_id')
    quantity_required = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Campos de auditoría agregados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'recipes'

class Sales(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branches, models.DO_NOTHING, db_column='branch_id', null=True, blank=True) 
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    quantity = models.IntegerField(default=1)
    total_sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    table_name = models.CharField(max_length=100, default='Barra')
    is_paid = models.BooleanField(default=False)
    is_prepared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    total_cost_at_sale = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Permitir nulo mientras la venta esté abierta
    payment_method = models.ForeignKey(
        PaymentMethods, 
        on_delete=models.PROTECT, 
        db_column='payment_method_id', 
        null=True, 
        blank=True
    )

    class Meta:
        managed = True
        db_table = 'sales'

# ==========================================
# 4. Transformaciones y Movimientos
# ==========================================

class Transformations(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result_ingredient = models.ForeignKey(
        Ingredients, 
        on_delete=models.PROTECT, 
        related_name='produced_in',
        db_column='result_ingredient_id'
    )
    quantity_produced = models.DecimalField(max_digits=10, decimal_places=2)
    cost_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'transformations'
        verbose_name = 'Transformación'


class TransformationItems(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transformation = models.ForeignKey(
        Transformations, 
        on_delete=models.CASCADE, 
        related_name='items',
        db_column='transformation_id'
    )
    ingredient = models.ForeignKey(
        Ingredients, 
        on_delete=models.PROTECT,
        db_column='ingredient_id'
    )
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = True
        db_table = 'transformation_items'
        verbose_name = 'Ítem de Transformación'


class InventoryMovements(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branches, on_delete=models.CASCADE, db_column='branch_id')
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE, db_column='ingredient_id')
    
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2)
    total_purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost_at_time = models.DecimalField(max_digits=10, decimal_places=4)
    
    MOVEMENT_TYPES = [
        ('INGRESO', 'Ingreso de Mercancía'),
        ('AJUSTE', 'Ajuste de Inventario'),
        ('MERMA', 'Merma / Desperdicio'),
    ]
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, default='INGRESO') 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'inventory_movements'
        verbose_name = 'Movimiento de Inventario'

    def __str__(self):
        return f"{self.movement_type} - {self.ingredient.name} ({self.created_at.date()})"


# ==========================================
# 5. Usuarios y Roles
# ==========================================

class UserProfile(models.Model):
    ROLES = [
        ('OWNER', 'Dueño de Negocio (Acceso Total)'),
        ('ADMIN_SEDE', 'Administrador de Sede'),
        ('STAFF', 'Personal (Caja/Barra)'),
    ]
    
    # CORREGIDO: Mapeo explícito a BigAutoField por el tipo bigint de Postgres
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile', db_column='user_id')
    role = models.TextField(choices=ROLES, default='STAFF')  # Cambiado a TextField para hacer match con 'text' de Postgres
    branch = models.ForeignKey(Branches, on_delete=models.SET_NULL, null=True, blank=True, db_column='branch_id')

    class Meta:
        managed = True
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
