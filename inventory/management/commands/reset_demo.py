import os
import uuid
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings

from inventory.models import (
    Branches, Products, Sales, PaymentMethods, 
    Ingredients, Inventories, Recipes
)

class Command(BaseCommand):
    help = 'Restaura base_seed.json y genera ventas dinámicas con rotación garantizada en todas las semanas.'

    def handle(self, *args, **options):
        # 1. Cargar datos maestros
        ruta_seed = os.path.join(settings.BASE_DIR, 'base_seed.json')
        if not os.path.exists(ruta_seed):
            ruta_seed = os.path.join(settings.BASE_DIR, '..', 'base_seed.json')

        self.stdout.write(f"1. Restaurando catalogo base desde: {ruta_seed}")
        Sales.objects.all().delete()
        Recipes.objects.all().delete()
        Inventories.objects.all().delete()
        Products.objects.all().delete()
        Ingredients.objects.all().delete()

        call_command('loaddata', ruta_seed)

        sedes = list(Branches.objects.all())
        productos = list(Products.objects.filter(is_active=True))
        metodos_pago = list(PaymentMethods.objects.filter(is_active=True))

        if not productos or not sedes or not metodos_pago:
            self.stdout.write(self.style.ERROR("Faltan datos maestros en la base de datos."))
            return

        mesas = ["Mesa 1", "Mesa 2", "Mesa 3", "Mesa 4", "Mesa 5", "Mesa 6", "Barra 1", "Barra 2"]
        
        # 90 días atrás calculados desde la fecha actual
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=90)
        fecha_actual = fecha_inicio

        ventas_crear = []
        self.stdout.write(f"2. Generando ventas distribuidas entre {fecha_inicio} y {fecha_fin}...")

        while fecha_actual <= fecha_fin:
            # Factor de intensidad del día (1: flojo a 5: excelente)
            escala = random.randint(1, 5)
            dia_semana = fecha_actual.weekday() # 4=Viernes, 5=Sábado

            # Base de comandas
            multiplicador = {1: 15, 2: 25, 3: 35, 4: 50, 5: 70}[escala]
            if dia_semana in [4, 5]:
                multiplicador = int(multiplicador * 1.4)

            # A) Asegurar que al menos el 80% del catálogo se venda cada día
            productos_hoy = random.sample(productos, k=int(len(productos) * 0.85))

            for prod in productos_hoy:
                # Cada producto se pide entre 1 y 4 veces al día
                repeticiones = random.randint(1, 3 if escala <= 2 else 5)
                for _ in range(repeticiones):
                    hora = random.choices(
                        [12, 13, 14, 19, 20, 21, 22, 23],
                        weights=[15, 20, 10, 15, 20, 10, 5, 5],
                        k=1
                    )[0]
                    minuto = random.randint(0, 59)

                    # Forzar la zona horaria local de Colombia para evitar desfase de día
                    fecha_hora = timezone.make_aware(
                        timezone.datetime.combine(fecha_actual, timezone.datetime.min.time())
                    ).replace(hour=hora, minute=minuto)

                    cant = random.randint(1, 3)
                    precio_tot = (prod.sale_price or Decimal('0')) * cant
                    costo_unit = prod.production_cost if prod.production_cost is not None else Decimal('0')
                    costo_tot = costo_unit * cant

                    ventas_crear.append(
                        Sales(
                            id=uuid.uuid4(),
                            branch=random.choice(sedes),
                            product=prod,
                            quantity=cant,
                            total_sale_price=precio_tot,
                            total_cost_at_sale=costo_tot,
                            table_name=random.choice(mesas),
                            payment_method=random.choice(metodos_pago),
                            is_paid=True,
                            is_prepared=True,
                            created_at=fecha_hora
                        )
                    )

            fecha_actual += timedelta(days=1)

        # Inserción masiva
        Sales.objects.bulk_create(ventas_crear, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"¡Éxito! Se crearon {len(ventas_crear)} ventas con rotación garantizada en todas las semanas."))