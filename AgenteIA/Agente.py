class Agente:
    def __init__(self):
        self.percepciones = None
        self.acciones = []
        self.habilitado = True
        self.rendimiento = {}

    def get_percepciones(self):
        return self.percepciones

    def set_percepciones(self, p):
        self.percepciones = p

    def get_acciones(self):
        return self.acciones

    def set_acciones(self, a):
        self.acciones = a

    def get_medida_rendimiento(self):
        return self.rendimiento

    def inhabilitar(self):
        self.habilitado = False

    def programa(self):
        pass
