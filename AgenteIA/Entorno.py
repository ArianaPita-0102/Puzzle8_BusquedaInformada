class Entorno:
    def __init__(self):
        self.agentes = []

    def insertar(self, agente):
        self.agentes.append(agente)

    def get_percepciones(self, agente):
        pass

    def ejecutar(self, agente):
        pass

    def finalizado(self):
        contador_habilitados = 0
        for a in self.agentes:
            if a.habilitado:
                contador_habilitados = contador_habilitados + 1
        return contador_habilitados == 0

    def run(self):
        while not self.finalizado():
            for a in self.agentes:
                if a.habilitado:
                    self.get_percepciones(a)
                    self.ejecutar(a)
