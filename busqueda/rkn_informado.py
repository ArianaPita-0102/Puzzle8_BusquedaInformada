"""
Junta AgenteBuscadorInformado (Codicioso/A* sobre la clase real del
profe) con AgenteRKN (Puzzle-N generalizado), lista para usar.
"""
from busqueda.agente_buscador_informado import AgenteBuscadorInformado
from core.agente_rkn import AgenteRKN


class RKNInformado(AgenteBuscadorInformado, AgenteRKN):
    pass
