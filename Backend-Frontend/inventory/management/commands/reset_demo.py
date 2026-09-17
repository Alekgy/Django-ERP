import os
import uuid
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings

from inventory.models import Branches, Products, Sales, PaymentMethods, Ingredients, Inventories, Recipes

class Command(BaseCommand):
    help = 'Restaura datos base desde base_seed.json y genera ventas dinámicas hasta hoy.'

    def handle(self, *args, **options):
        # 1. Localizar base_seed.json de forma segura
        nombre_seed = 'base_seed.json'
        ruta_seed = os.path.join(settings.BASE_DIR, nombre_seed)
        if not os.path.exists(ruta_seed):
            # Por si el archivo está en la raíz del repositorio
            ruta_seed = os.path.join(settings.BASE_DIR, '..', nombre_seed)

        if not os.path.exists(ruta_seed):
            self.stdout.write(self.style.ERROR(f"No se encontró el archivo {nombre_seed} en {ruta_seed}"))
            return

        self.stdout.write(f"1. Cargando datos maestros desde: {ruta_seed}")
        # Limpiamos tablas operativas para que la seed entre limpia sin duplicados ni huérfanos
        Sales.objects.all().delete()
        Recipes.objects.all().delete()
        Inventories.objects.all().delete()
        Products.objects.all().delete()
        Ingredients.objects.all().delete()

        call_command('loaddata', ruta_seed)

        # 2. Obtener datos maestros restaurados
        sedes = list(Branches.objects.all())
        productos = list(Products.objects.filter(is_active=True))
        metodos_pago = list(PaymentMethods.objects.filter(is_active=True))

        if not productos or not sedes or not metodos_pago:
            self.stdout.write(self.style.ERROR("Faltan datos maestros para poblar ventas."))
            return

        mesas = ["Mesa 1", "Mesa 2", "Mesa 3", "Mesa 4", "Mesa 5", "Mesa 6", "Barra 1", "Barra 2"]
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=90)
        fecha_actual = fecha_inicio

        ventas_crear = []
        self.stdout.write(f"2. Generando historial dinámico entre {fecha_inicio} y {fecha_fin}...")

        while fecha_actual <= fecha_fin:
            # 1 (Malo) a 5 (Espectacular)
            escala = random.randint(1, 5)
            dia_semana = fecha_actual.weekday()

            comandas_map = {
                1: (3, 6),
                2: (7, 12),
                3: (14, 22),
                4: (24, 35),
                5: (36, 50),
            }[escala]

            num_comandas = random.randint(*comandas_map)
            if dia_semana in [4, 5]: # Vie y Sáb más movimiento
                num_comandas = int(num_comandas * 1.3)

            for _ in range(num_comandas):
                hora = random.choices(
                    [12, 13, 14, 18, 19, 20, 21, 22, 23],
                    weights=[10, 15, 10, 5, 12, 18, 20, 8, 2],
                    k=1
                )[0]
                minuto = random.randint(0, 59)

                fecha_hora = timezone.make_aware(
                    timezone.datetime.combine(fecha_actual, timezone.datetime.min.time())
                ).replace(hour=hora, minute=minuto)

                mesa = random.choice(mesas)
                sede = random.choice(sedes)
                metodo = random.choice(metodos_pago)
                prods_comanda = random.sample(productos, k=random.randint(1, 3))

                for prod in prods_comanda:
                    cant = random.randint(1, 2)
                    precio_tot = (prod.sale_price or Decimal('0')) * cant
                    costo_unit = prod.production_cost if prod.production_cost is not None else Decimal('0')
                    costo_tot = costo_unit * cant

                    ventas_crear.append(
                        Sales(
                            id=uuid.uuid4(),
                            branch=sede,
                            product=prod,
                            quantity=cant,
                            total_sale_price=precio_tot,
                            total_cost_at_sale=costo_tot,
                            table_name=mesa,
                            payment_method=metodo,
                            is_paid=True,
                            is_prepared=True,
                            created_at=fecha_hora
                        )
                    )

            fecha_actual += timedelta(days=1)

        Sales.objects.bulk_create(ventas_crear, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"¡Listo! Se cargó base_seed.json y se insertaron {len(ventas_crear)} ventas frescas."))