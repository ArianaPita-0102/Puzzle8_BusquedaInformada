import heapq
import itertools
import time

from AgenteIA.AgenteBuscador import AgenteBuscador


def _a_tupla(estado):
    if isinstance(estado, list):
        return tuple(_a_tupla(x) for x in estado)
    return estado


class AgenteBuscadorInformado(AgenteBuscador):

    TECNICAS_PROPIAS = ("codicioso", "a_estrella")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tecnica_informada = None
        self._limite_nodos = None
        self._limite_tiempo_s = None

    def set_limites(self, nodos=None, tiempo_s=None):
        self._limite_nodos = nodos
        self._limite_tiempo_s = tiempo_s

    def set_tecnica(self, t):
        self._tecnica_informada = t
        super().set_tecnica(t)

    def programa(self):
        if self._tecnica_informada not in self.TECNICAS_PROPIAS:
            return super().programa()
        return self._programa_informado()

    def _programa_informado(self):
        inicio_reloj = time.time()
        contador = itertools.count()

        estado_inicial = self.get_estado_inicial()
        camino_inicial = [estado_inicial]

        if self._tecnica_informada == "codicioso":
            f0 = self.get_heuristica(camino_inicial)
        else:
            f0 = self.get_funcion_a(camino_inicial)

        frontera = [(f0, next(contador), camino_inicial)]
        visitados = set()

        rendimiento = self.get_medida_rendimiento()
        rendimiento["max_profundidad"] = 0
        rendimiento["nodos_expandidos"] = 0
        rendimiento["nodos_generados"] = 1
        rendimiento["memoria_max"] = 1
        rendimiento["timeout"] = None

        while frontera:
            rendimiento["memoria_max"] = max(
                rendimiento["memoria_max"], len(frontera) + len(visitados))

            _, _, camino = heapq.heappop(frontera)
            nodo = camino[-1]
            clave_nodo = _a_tupla(nodo)

            if clave_nodo in visitados:
                continue
            visitados.add(clave_nodo)

            rendimiento["max_profundidad"] = max(rendimiento["max_profundidad"], len(camino))
            rendimiento["nodos_expandidos"] += 1

            if self._limite_nodos is not None and rendimiento["nodos_expandidos"] >= self._limite_nodos:
                rendimiento["pasos"] = None
                rendimiento["Costo"] = None
                rendimiento["tiempo"] = time.time() - inicio_reloj
                rendimiento["timeout"] = "nodos"
                return
            if self._limite_tiempo_s is not None and (time.time() - inicio_reloj) >= self._limite_tiempo_s:
                rendimiento["pasos"] = None
                rendimiento["Costo"] = None
                rendimiento["tiempo"] = time.time() - inicio_reloj
                rendimiento["timeout"] = "tiempo"
                return

            if self.test_objetivo(nodo):
                self.set_acciones(camino)
                rendimiento["pasos"] = len(camino)
                rendimiento["Costo"] = self.get_costo(camino)
                rendimiento["tiempo"] = time.time() - inicio_reloj
                return

            for hijo in self.generar_hijos(nodo):
                if hijo is None:
                    continue
                if _a_tupla(hijo) in visitados:
                    continue
                rendimiento["nodos_generados"] += 1
                nuevo_camino = camino + [hijo]
                if self._tecnica_informada == "codicioso":
                    f_hijo = self.get_heuristica(nuevo_camino)
                else:
                    f_hijo = self.get_funcion_a(nuevo_camino)
                heapq.heappush(frontera, (f_hijo, next(contador), nuevo_camino))

        rendimiento["pasos"] = None
        rendimiento["Costo"] = None
        rendimiento["tiempo"] = time.time() - inicio_reloj