import random
import uuid
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from inventory.models import Branches, Products, Sales, PaymentMethods

class Command(BaseCommand):
    help = 'Restaura los datos maestros y genera ventas dinámicas hasta el día de hoy.'

    def handle(self, *args, **options):
        self.stdout.write("1. Cargando datos maestros desde la seed...")
        # Carga tu archivo base con usuarios, sedes, insumos y recetas
        call_command('loaddata', 'demo_seed.json')

        self.stdout.write("2. Limpiando historial de ventas para regenerar métricas frescas...")
        Sales.objects.all().delete()[cite: 16]

        sedes = list(Branches.objects.all())
        productos = list(Products.objects.filter(is_active=True))
        metodos_pago = list(PaymentMethods.objects.filter(is_active=True))

        if not productos or not sedes or not metodos_pago:
            self.stdout.write(self.style.ERROR("Faltan datos maestros para generar las ventas."))
            return

        mesas = ["Mesa 1", "Mesa 2", "Mesa 3", "Mesa 4", "Mesa 5", "Mesa 6", "Barra 1", "Barra 2"][cite: 16]
        
        # Generar los últimos 90 días calculados hasta hoy
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=90)[cite: 16]
        fecha_actual = fecha_inicio

        ventas_crear = []
        self.stdout.write(f"3. Generando ventas entre {fecha_inicio} y {fecha_fin}...")

        while fecha_actual <= fecha_fin:
            # Índice aleatorio: 1 (Día malo) a 5 (Día excelente)
            escala_dia = random.randint(1, 5)
            dia_semana = fecha_actual.weekday() # 4=Viernes, 5=Sábado

            # Rangos de comandas según el índice
            comandas_rango = {
                1: (3, 7),     # Día flojo
                2: (8, 14),    # Día bajo-medio
                3: (15, 24),   # Día normal
                4: (25, 36),   # Buen día
                5: (38, 55),   # Día espectacular
            }[escala_dia]

            num_comandas = random.randint(*comandas_rango)

            # Impulso para fines de semana
            if dia_semana in [4, 5]:
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
                    precio_tot = prod.sale_price * cant
                    costo_tot = (prod.production_cost or Decimal('0')) * cant

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

        # Inserción masiva de alto rendimiento
        Sales.objects.bulk_create(ventas_crear, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"¡Éxito! Se crearon {len(ventas_crear)} ventas dinámicas hasta hoy."))