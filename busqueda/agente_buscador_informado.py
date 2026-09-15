"""
Extiende la clase REAL AgenteIA.AgenteBuscador (la del framework del
proyecto) agregando las técnicas "codicioso" y "a_estrella", que la
clase original no trae (solo soporta amplitud / profundidad / costouniforme).

Uso (mismo estilo que ya usa el resto del proyecto, ver demo01.py):

    from agente_buscador_informado import AgenteBuscadorInformado
    from AgenteRK8 import AgenteRK8

    class RK8Informado(AgenteBuscadorInformado, AgenteRK8):
        pass

    agente = RK8Informado(heuristica="h5")
    agente.set_estado_inicial(estado_inicial)
    agente.set_estado_meta(estado_meta)
    agente.set_tecnica("a_estrella")   # o "codicioso"
    agente.programa()
    print(agente.get_medida_rendimiento())

Por qué no se reutiliza tal cual el "frontera.sort(...)" que la clase
original usa para costouniforme: para el Experimento 1 (1000 instancias
x 8 heurísticas x 2 algoritmos) hay corridas -sobre todo A* con H1, la
heurística más débil- que expanden decenas de miles de nodos. Reordenar
la lista completa de la frontera en cada una de esas iteraciones sería
demasiado lento. heapq logra el mismo orden de expansión (mismo
resultado) en O(log n) por operación en vez de O(n log n).

También se cambia "visitados" de lista a set de tuplas (los estados acá
son listas de listas, que no son hasheables), por la misma razón de
performance: buscar en un set es O(1), buscar en una lista con "in" es
O(n) y con miles de nodos visitados se nota mucho.
"""

import heapq
import itertools
import time

from AgenteIA.AgenteBuscador import AgenteBuscador


def _a_tupla(estado):
    """Convierte un estado (lista de listas, como el tablero del
    Puzzle-8) en algo hasheable para poder meterlo en un set."""
    if isinstance(estado, list):
        return tuple(_a_tupla(x) for x in estado)
    return estado


class AgenteBuscadorInformado(AgenteBuscador):

    TECNICAS_PROPIAS = ("codicioso", "a_estrella")

    def __init__(self, *args, **kwargs):
        # __init__ "cooperativo": al usar herencia múltiple con
        # AgenteRK8 (que sí recibe heuristica=..., w=...), esta clase
        # no debe quedarse con esos argumentos, tiene que pasarlos
        # para arriba en la cadena de herencia (MRO) con super().
        super().__init__(*args, **kwargs)
        self._tecnica_informada = None
        self._limite_nodos = None
        self._limite_tiempo_s = None

    def set_limites(self, nodos=None, tiempo_s=None):
        """Corta la búsqueda si se supera el presupuesto de nodos
        expandidos o de tiempo. Sin esto, en tableros grandes (N=4 en
        adelante) A* puede consumir toda la memoria disponible y el
        proceso muere sin avisar (nos pasó probando esto en 4x4). Con
        el límite, se reporta como 'no encontrado' (timeout), que es
        justo la métrica que pide el Experimento 2 para decidir el N
        máximo factible.
        """
        self._limite_nodos = nodos
        self._limite_tiempo_s = tiempo_s

    def set_tecnica(self, t):
        # AgenteBuscador.__tecnica es privado por name mangling: desde
        # acá no se puede leer. Guardamos nuestra propia copia y
        # avisamos también al padre, para no romper nada si en algún
        # momento se usa una técnica ya soportada por la clase base.
        self._tecnica_informada = t
        super().set_tecnica(t)

    def programa(self):
        if self._tecnica_informada not in self.TECNICAS_PROPIAS:
            # amplitud / profundidad / costouniforme: se deja intacto
            # el comportamiento original de AgenteBuscador.
            return super().programa()
        return self._programa_informado()

    def _programa_informado(self):
        inicio_reloj = time.time()
        contador = itertools.count()  # desempate estable en heapq:
        # los caminos son listas de estados (listas de listas) y no
        # son comparables entre sí; sin este contador, heapq explota
        # con TypeError en cuanto dos nodos empatan en f.

        estado_inicial = self.get_estado_inicial()
        camino_inicial = [estado_inicial]

        if self._tecnica_informada == "codicioso":
            f0 = self.get_heuristica(camino_inicial)
        else:  # a_estrella -> usa get_funcion_a = get_costo + get_heuristica
            f0 = self.get_funcion_a(camino_inicial)

        frontera = [(f0, next(contador), camino_inicial)]
        visitados = set()

        rendimiento = self.get_medida_rendimiento()
        rendimiento["max_profundidad"] = 0
        rendimiento["nodos_expandidos"] = 0
        rendimiento["nodos_generados"] = 1  # el estado inicial cuenta como generado
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
                    continue  # movimiento inválido (ver arriba/abajo/etc. en AgenteRK8)
                if _a_tupla(hijo) in visitados:
                    continue
                rendimiento["nodos_generados"] += 1
                nuevo_camino = camino + [hijo]  # no hace falta deepcopy:
                # no se mutan los estados ya creados, solo se arma un
                # camino nuevo que apunta a los mismos objetos.
                if self._tecnica_informada == "codicioso":
                    f_hijo = self.get_heuristica(nuevo_camino)
                else:
                    f_hijo = self.get_funcion_a(nuevo_camino)
                heapq.heappush(frontera, (f_hijo, next(contador), nuevo_camino))

        # Frontera agotada sin encontrar el objetivo.
        rendimiento["pasos"] = None
        rendimiento["Costo"] = None
        rendimiento["tiempo"] = time.time() - inicio_reloj