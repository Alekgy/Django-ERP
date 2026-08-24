from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Limpia la base de datos y restaura el estado semilla del demo"

    def handle(self, *args, **options):
        self.stdout.write("Vaciando tablas existentes...")
        call_command('flush', '--no-input')
        
        self.stdout.write("Cargando datos semilla desde demo_seed.json...")
        call_command('loaddata', 'demo_seed.json')
        
        self.stdout.write(self.style.SUCCESS("¡Base de datos restablecida con éxito!"))