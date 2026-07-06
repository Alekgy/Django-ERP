from django.contrib import admin
from .models import (
    Branches, Ingredients, Products, 
    Recipes, Inventories, Sales, UnitMeasures
)

class InventoriesInline(admin.TabularInline):
    model = Inventories
    extra = 0
    fields = ('branch', 'stock_level')

class RecipeInline(admin.TabularInline):
    model = Recipes
    extra = 1
    autocomplete_fields = ['ingredient']

@admin.register(UnitMeasures)
class UnitMeasuresAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name',)

@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'sale_price', 'production_cost', 'is_active')
    list_editable = ('sale_price', 'is_active')
    inlines = [RecipeInline]
    search_fields = ('name',)

@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit_measure', 'min_stock_threshold')
    list_editable = ('min_stock_threshold',)
    search_fields = ('name',) 
    inlines = [InventoriesInline]

@admin.register(Branches)
class BranchesAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'created_at')
    search_fields = ('name',)

@admin.register(Inventories)
class InventoriesAdmin(admin.ModelAdmin):
    list_display = ('branch', 'ingredient', 'stock_level')
    list_filter = ('branch', 'ingredient')
    
@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    # Solo incluimos campos que están en tu captura de Supabase + los nuevos para la caja
    list_display = ('id', 'product', 'quantity', 'total_sale_price', 'table_name', 'is_paid', 'created_at')
    
    # Filtros laterales basados en los nuevos campos
    list_filter = ('is_paid', 'created_at', 'table_name')
    
    # Buscador por nombre de producto o mesa
    search_fields = ('product__name', 'table_name')
    
    # Campos de solo lectura
    readonly_fields = ('created_at',)
    
    ordering = ('-created_at',)

    fieldsets = (
        ('Información de la Mesa', {
            'fields': ('table_name', 'is_paid')
        }),
        ('Detalle de Venta', {
            'fields': ('product', 'quantity', 'total_sale_price')
        }),
        ('Datos Temporales', {
            'fields': ('created_at',),
        }),
    )