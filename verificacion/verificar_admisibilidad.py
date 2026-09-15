import os
import sys
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

from core.AgenteRK8 import AgenteRK8
from collections import deque

estado_meta = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]

def a_tupla(e):
    return tuple(tuple(f) for f in e)

solver = AgenteRK8()
solver.set_estado_meta(estado_meta)
solver.h5(estado_meta)

frontera = deque([estado_meta])
visitados = {a_tupla(estado_meta)}
distancia_optima = {a_tupla(estado_meta): 0}
while frontera:
    actual = frontera.popleft()
    ta = a_tupla(actual)
    for hijo in solver.generar_hijos(actual):
        if hijo is not None:
            th = a_tupla(hijo)
            if th not in visitados:
                visitados.add(th)
                distancia_optima[th] = distancia_optima[ta] + 1
                frontera.append(hijo)

print("Total de estados solubles:", len(distancia_optima))

for h_nombre in ["h1", "h2", "h3", "h4", "h5", "h6"]:
    solver.set_heuristica(h_nombre)
    fallas = 0
    peor_exceso = 0
    for tupla_estado, optimo in distancia_optima.items():
        estado = [list(fila) for fila in tupla_estado]
        valor_h = solver.get_heuristica([estado])
        if valor_h > optimo:
            fallas += 1
            peor_exceso = max(peor_exceso, valor_h - optimo)
    print(f"{h_nombre}: fallas de admisibilidad = {fallas} / {len(distancia_optima)}  (peor exceso: {peor_exceso})")

for w in [0.3, 0.6, 1.0]:
    solver.set_heuristica("h6")
    solver.set_w(w)
    fallas = 0
    peor_exceso = 0
    for tupla_estado, optimo in distancia_optima.items():
        estado = [list(fila) for fila in tupla_estado]
        valor_h = solver.get_heuristica([estado])
        if valor_h > optimo:
            fallas += 1
            peor_exceso = max(peor_exceso, valor_h - optimo)
    print(f"h6 (w={w}): fallas de admisibilidad = {fallas} / {len(distancia_optima)}  (peor exceso: {peor_exceso})")