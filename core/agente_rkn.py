from copy import deepcopy
from AgenteIA.AgenteBuscador import AgenteBuscador


class AgenteRKN(AgenteBuscador):

    HEURISTICAS_DISPONIBLES = ("h1", "h2")

    def __init__(self, n=3, heuristica="h2"):
        AgenteBuscador.__init__(self)
        self.n = n
        self.add_funcion(self.arriba)
        self.add_funcion(self.abajo)
        self.add_funcion(self.izquierda)
        self.add_funcion(self.derecha)
        self.set_heuristica(heuristica)

    def set_heuristica(self, nombre):
        if nombre not in self.HEURISTICAS_DISPONIBLES:
            raise ValueError(f"Heurística '{nombre}' no reconocida para AgenteRKN")
        self.__heuristica = nombre

    def get_costo(self, tup):
        return len(tup)

    def pos(self, e):
        n = self.n
        for i in range(n):
            for j in range(n):
                if e[i][j] == 0:
                    return (i, j)

    def arriba(self, e):
        t = self.pos(e)
        if t[0] != 0:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0] - 1][t[1]]
            aux[t[0] - 1][t[1]] = 0
            return aux
        return None

    def abajo(self, e):
        t = self.pos(e)
        if t[0] != self.n - 1:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0] + 1][t[1]]
            aux[t[0] + 1][t[1]] = 0
            return aux
        return None

    def derecha(self, e):
        t = self.pos(e)
        if t[1] != self.n - 1:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0]][t[1] + 1]
            aux[t[0]][t[1] + 1] = 0
            return aux
        return None

    def izquierda(self, e):
        t = self.pos(e)
        if t[1] != 0:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0]][t[1] - 1]
            aux[t[0]][t[1] - 1] = 0
            return aux
        return None

    def _posiciones_meta(self):
        meta = self.get_estado_meta()
        posiciones = {}
        for x in range(self.n):
            for y in range(self.n):
                posiciones[meta[x][y]] = (x, y)
        return posiciones

    def get_heuristica(self, camino):
        estado = camino[-1]
        metodo = getattr(self, self.__heuristica)
        return metodo(estado)

    def h1(self, estado):
        meta = self.get_estado_meta()
        n = self.n
        contador = 0
        for i in range(n):
            for j in range(n):
                valor = estado[i][j]
                if valor != 0 and valor != meta[i][j]:
                    contador += 1
        return contador

    def h2(self, estado):
        n = self.n
        posiciones_meta = self._posiciones_meta()
        distancia = 0
        for i in range(n):
            for j in range(n):
                valor = estado[i][j]
                if valor != 0:
                    x, y = posiciones_meta[valor]
                    distancia += abs(i - x) + abs(j - y)
        return distancia
