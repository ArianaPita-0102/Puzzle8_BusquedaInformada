"""
Experimento 1: Comparación de Heurísticas en Puzzle-8.

Corre Codicioso y A* con H1, H2, H3, H4, H5 y H6 (con w=0.3, 0.6, 1.0)
sobre las mismas 1000 instancias (generadas por generar_instancias.py) y
exporta todas las métricas a resultados_experimento1.csv.

Usa RK8Informado (AgenteBuscadorInformado + AgenteRK8), que extiende de
verdad la clase AgenteIA.AgenteBuscador del proyecto agregando las
técnicas "codicioso" y "a_estrella".

Uso:
    python experimentos/experimento1.py                # corre las 1000 instancias
    python experimentos/experimento1.py --n 50         # corrida rápida de prueba
"""

import argparse
import csv
import json
import os
import sys
import time

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ_PROYECTO = os.path.dirname(_AQUI)
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)
# Bootstrap para poder ejecutar este script directamente
# (python carpeta/archivo.py) sin instalar el proyecto como paquete.

from busqueda.rk8_informado import RK8Informado

# Rutas por defecto, siempre relativas a esta carpeta (experimentos/),
# sin importar desde dónde se llame al script.
_INSTANCIAS_DEFAULT = os.path.join(_AQUI, "instancias_puzzle8.json")
_RESULTADOS_DIR = os.path.join(_AQUI, "resultados")
_SALIDA_DEFAULT = os.path.join(_RESULTADOS_DIR, "resultados_experimento1.csv")

ESTADO_META = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]

# Cada entrada: (etiqueta_para_csv, nombre_metodo_heuristica, peso_o_None)
CONFIGURACIONES_HEURISTICA = [
    ("h1", "h1", None),
    ("h2", "h2", None),
    ("h3", "h3", None),
    ("h4", "h4", None),
    ("h5", "h5", None),
    ("h6_w0.3", "h6", 0.3),
    ("h6_w0.6", "h6", 0.6),
    ("h6_w1.0", "h6", 1.0),
]

ALGORITMOS = ["codicioso", "a_estrella"]


def construir_agente(nombre_metodo, peso):
    agente = RK8Informado(heuristica=nombre_metodo)
    agente.set_estado_meta(ESTADO_META)
    if peso is not None:
        agente.set_w(peso)
    return agente


def correr_experimento(instancias, salida_csv):
    columnas = [
        "instancia_id", "algoritmo", "heuristica",
        "encontrado", "pasos", "tiempo_ms",
        "nodos_expandidos", "nodos_generados", "memoria_max",
    ]

    total_corridas = len(instancias) * len(CONFIGURACIONES_HEURISTICA) * len(ALGORITMOS)
    hechas = 0
    t_inicio_global = time.perf_counter()

    with open(salida_csv, "w", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()

        # Un agente por (heurística, peso): así la Pattern Database de H5
        # se construye UNA sola vez y se reutiliza en las 1000 instancias.
        agentes = {
            etiqueta: construir_agente(metodo, peso)
            for etiqueta, metodo, peso in CONFIGURACIONES_HEURISTICA
        }

        for idx, estado_inicial in enumerate(instancias):
            for etiqueta, _, _ in CONFIGURACIONES_HEURISTICA:
                agente = agentes[etiqueta]
                for algoritmo in ALGORITMOS:
                    agente.set_estado_inicial(estado_inicial)
                    agente.set_tecnica(algoritmo)

                    t0 = time.perf_counter()
                    agente.programa()
                    t1 = time.perf_counter()

                    r = agente.get_medida_rendimiento()
                    encontrado = r.get("pasos") is not None

                    escritor.writerow({
                        "instancia_id": idx,
                        "algoritmo": algoritmo,
                        "heuristica": etiqueta,
                        "encontrado": encontrado,
                        # "pasos" en este framework = len(camino), que
                        # incluye el estado inicial -> movimientos = pasos-1
                        "pasos": (r["pasos"] - 1) if encontrado else None,
                        "tiempo_ms": round((t1 - t0) * 1000, 3),
                        "nodos_expandidos": r["nodos_expandidos"],
                        "nodos_generados": r["nodos_generados"],
                        "memoria_max": r["memoria_max"],
                    })

                    hechas += 1
                    if hechas % 200 == 0:
                        transcurrido = time.perf_counter() - t_inicio_global
                        print(f"  {hechas}/{total_corridas} corridas "
                              f"({transcurrido:.1f}s transcurridos)")

    print(f"Listo. Resultados en {salida_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=None,
                         help="Usar solo las primeras N instancias (para pruebas rápidas)")
    parser.add_argument("--instancias", type=str, default=_INSTANCIAS_DEFAULT)
    parser.add_argument("--salida", type=str, default=_SALIDA_DEFAULT)
    args = parser.parse_args()

    os.makedirs(_RESULTADOS_DIR, exist_ok=True)

    with open(args.instancias) as f:
        instancias = json.load(f)

    if args.n is not None:
        instancias = instancias[:args.n]

    print(f"Corriendo experimento sobre {len(instancias)} instancias, "
          f"{len(CONFIGURACIONES_HEURISTICA)} heurísticas x {len(ALGORITMOS)} algoritmos...")
    correr_experimento(instancias, args.salida)
