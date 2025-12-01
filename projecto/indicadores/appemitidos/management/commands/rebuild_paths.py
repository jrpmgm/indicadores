from django.core.management.base import BaseCommand
from appemitidos.models import Location

class Command(BaseCommand):
    help = "Reconstruye el campo path para todas las localizaciones"

    def handle(self, *args, **kwargs):

        def update_path(node, parent_path=""):
            node.path = f"{parent_path}{node.id}/"
            node.save(update_fields=["path"])
            for child in node.children.all():
                update_path(child, node.path)

        roots = Location.objects.filter(parent__isnull=True)

        for r in roots:
            update_path(r)

        self.stdout.write(self.style.SUCCESS("✔ Paths reconstruidos correctamente"))