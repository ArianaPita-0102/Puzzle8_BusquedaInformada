"""
Junta las dos piezas en una sola clase lista para usar:
- AgenteBuscadorInformado: agrega Codicioso y A* a la clase real del profe.
- AgenteRK8: el Puzzle-8 con las 6 heuristicas (h1-h6) de Igor.
"""
from busqueda.agente_buscador_informado import AgenteBuscadorInformado
from core.AgenteRK8 import AgenteRK8


class RK8Informado(AgenteBuscadorInformado, AgenteRK8):
    pass
