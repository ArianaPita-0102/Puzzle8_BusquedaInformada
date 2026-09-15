"""
Verificación de CONSISTENCIA de las heurísticas (complementa a
verificar_admisibilidad.py, que solo comprueba admisibilidad).

Admisibilidad:  h(s) <= distancia_optima(s, meta)            [global]
Consistencia:   h(s) <= costo(s, s') + h(s')  para TODO vecino s' de s   [local]

Consistencia es una condición más fuerte: implica admisibilidad, pero
no al revés. Acá se reconstruye el mismo espacio de 181.440 estados
solubles del Puzzle-8 (mismo BFS que verificar_admisibilidad.py) y,
en vez de comparar cada estado contra la meta, se revisa la
desigualdad de consistencia sobre cada arista (estado, vecino) del
grafo de estados. Como todos los movimientos cuestan 1, la condición
queda simplemente h(s) <= 1 + h(s').

No modifica AgenteRK8.py ni ninguna heurística: solo las usa tal como
están, igual que ya hace verificar_admisibilidad.py.
"""

import os
import sys
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)
# Bootstrap para poder ejecutar este script directamente
# (python carpeta/archivo.py) sin instalar el proyecto como paquete.

from core.AgenteRK8 import AgenteRK8
from collections import deque

ESTADO_META = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]

# Heurísticas a comprobar. H6 no hace falta: al ser una combinación
# convexa de H1 y H2 (ambas consistentes), hereda la propiedad
# automáticamente para cualquier peso w.
HEURISTICAS_A_VERIFICAR = ["h1", "h2", "h3", "h4", "h5"]


def a_tupla(e):
    return tuple(tuple(f) for f in e)


def construir_espacio_de_estados(solver, estado_meta):
    """Mismo BFS que verificar_admisibilidad.py, pero acá además nos
    quedamos con la lista de aristas (estado, vecino) para poder
    revisar consistencia sobre cada una."""
    frontera = deque([estado_meta])
    visitados = {a_tupla(estado_meta)}
    aristas = []  # pares (estado, vecino) tal como los devuelve generar_hijos

    while frontera:
        actual = frontera.popleft()
        for hijo in solver.generar_hijos(actual):
            if hijo is not None:  # movimiento inválido -> None
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
        # costo(s, s') = 1 para cualquier movimiento del Puzzle-8
        if h_estado > 1 + h_vecino:
            fallas += 1
            peor_exceso = max(peor_exceso, h_estado - (1 + h_vecino))
    return fallas, peor_exceso


if __name__ == "__main__":
    solver = AgenteRK8()
    solver.set_estado_meta(ESTADO_META)
    solver.h5(ESTADO_META)  # fuerza construir la pattern database una vez

    aristas, total_estados = construir_espacio_de_estados(solver, ESTADO_META)
    print(f"Total de estados solubles: {total_estados}")
    print(f"Total de aristas (estado, vecino) a revisar: {len(aristas)}")
    print()

    for nombre in HEURISTICAS_A_VERIFICAR:
        fallas, peor_exceso = verificar_consistencia(solver, nombre, aristas)
        print(f"{nombre}: fallas de consistencia = {fallas} / {len(aristas)}  "
              f"(peor exceso: {peor_exceso})")
