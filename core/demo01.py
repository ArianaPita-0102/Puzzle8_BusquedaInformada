import os
import sys
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

from core.AgenteRK8 import AgenteRK8

estado_inicial = [[7, 2, 4],[5,0,6],[8,3,1]]
estado_meta = [[1,2,3], [4,5,6], [7,8,0]]

if __name__ == "__main__":
    solver = AgenteRK8(heuristica="h6")
    solver.set_estado_inicial(estado_inicial)
    solver.set_estado_meta(estado_meta)
    print(solver.generar_hijos(estado_inicial))
    print(solver.get_heuristica([estado_inicial]))