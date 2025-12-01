from django.core.management.base import BaseCommand

class Cafe():
    def que_soy(self):
        return ("Soy un café")
    
class Te():
    def que_soy(self):
        return ("Soy un té")

def def_bebida(tipo_bebida):
    tipo_bebida.que_soy()

#def_bebida(Cafe())

class Command(BaseCommand):
    print("Comando de prueba de bebidas")
    def_bebida(Cafe())
    def handle(self, *args, **kwargs):
        pass