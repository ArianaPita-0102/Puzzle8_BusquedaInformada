import os
import sys
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

from core.AgenteRK8 import AgenteRK8
from collections import deque

ESTADO_META = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]

HEURISTICAS_A_VERIFICAR = ["h1", "h2", "h3", "h4", "h5"]


def a_tupla(e):
    return tuple(tuple(f) for f in e)


def construir_espacio_de_estados(solver, estado_meta):
    frontera = deque([estado_meta])
    visitados = {a_tupla(estado_meta)}
    aristas = []

    while frontera:
        actual = frontera.popleft()
        for hijo in solver.generar_hijos(actual):
            if hijo is not None:
                aristas.append((actual, hijo))
                th = a_tupla(hijo)
                if th not in visitados:
                    visitados.add(th)
                    frontera.append(hijo)

    return aristas, len(visitados)


def verificar_consistencia(solver, nombre_heuristica, aristas):
    solver.set_heuristica(nombre_heuristica)
    fallas = 0
    peor_exceso = 0
    for estado, vecino in aristas:
        h_estado = solver.get_heuristica([estado])
        h_vecino = solver.get_heuristica([vecino])
        if h_estado > 1 + h_vecino:
            fallas += 1
            peor_exceso = max(peor_exceso, h_estado - (1 + h_vecino))
    return fallas, peor_exceso


if __name__ == "__main__":
    solver = AgenteRK8()
    solver.set_estado_meta(ESTADO_META)
    solver.h5(ESTADO_META)

    aristas, total_estados = construir_espacio_de_estados(solver, ESTADO_META)
    print(f"Total de estados solubles: {total_estados}")
    print(f"Total de aristas (estado, vecino) a revisar: {len(aristas)}")
    print()

    for nombre in HEURISTICAS_A_VERIFICAR:
        fallas, peor_exceso = verificar_consistencia(solver, nombre, aristas)
        print(f"{nombre}: fallas de consistencia = {fallas} / {len(aristas)}  "
              f"(peor exceso: {peor_exceso})")
