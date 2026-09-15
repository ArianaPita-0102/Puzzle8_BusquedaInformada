"""
Experimento 2: Escalabilidad por Tamaño de Tablero.

Para N = 3, 4, 5, ... genera instancias solubles y corre A* con H2
(Manhattan generalizada — ver agente_rkn.py para por qué no se usa H5
acá), con un presupuesto de nodos/tiempo para no reventar la memoria
en tableros grandes. Mide nodos expandidos, tiempo y tasa de éxito, y
determina el N máximo donde se resuelve al menos el 50% de instancias
dentro del presupuesto.

Para N >= 4, las instancias NO se generan 100% al azar (una
permutación aleatoria del 15-puzzle puede estar a 50+ movimientos de
la meta y ser intratable para A* + Manhattan puro). En su lugar se
arma cada instancia con una CAMINATA ALEATORIA de longitud controlada
desde la meta (el propio enunciado de la práctica sugiere esto como
alternativa al chequeo de paridad). La longitud de la caminata crece
con N para que la dificultad crezca de forma controlada.

Uso (desde la carpeta raíz del proyecto):
    python experimentos/escalabilidad.py
"""

import csv
import os
import random
import sys
import time

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ_PROYECTO = os.path.dirname(_AQUI)
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)
# Bootstrap para poder ejecutar este script directamente
# (python carpeta/archivo.py) sin instalar el proyecto como paquete.

from busqueda.rkn_informado import RKNInformado
from experimentos.generar_instancias_n import estado_meta, generar_instancias_n

_RESULTADOS_DIR = os.path.join(_AQUI, "resultados")
_SALIDA_DEFAULT = os.path.join(_RESULTADOS_DIR, "resultados_escalabilidad.csv")

# --- Configuración del experimento ---
TAMANOS = [3, 4, 5, 6]
INSTANCIAS_POR_TAMANO = 100  # como pide el PDF ("generar 100 instancias...")
LONGITUD_CAMINATA = {3: None, 4: 40, 5: 60, 6: 80}  # None = usar generador por paridad (100% aleatorio)
LIMITE_NODOS = 300_000
LIMITE_TIEMPO_S = 300  # 5 minutos por instancia, como sugiere el PDF
UMBRAL_EXITO = 0.5  # 50%, como pide la consigna


def generar_por_caminata(n, longitud, rng):
    """Arranca en la meta y aplica `longitud` movimientos válidos al
    azar (evitando deshacer el movimiento anterior, para no perder
    pasos yendo y viniendo). El resultado es soluble por construcción:
    basta con invertir la misma secuencia de movimientos."""
    agente = RKNInformado(n=n, heuristica="h2")
    meta = estado_meta(n)
    agente.set_estado_meta(meta)
    estado = meta
    anterior_inverso = None
    funciones = {
        "arriba": (agente.arriba, "abajo"),
        "abajo": (agente.abajo, "arriba"),
        "izquierda": (agente.izquierda, "derecha"),
        "derecha": (agente.derecha, "izquierda"),
    }
    for _ in range(longitud):
        opciones = [nombre for nombre in funciones if nombre != anterior_inverso]
        rng.shuffle(opciones)
        for nombre in opciones:
            funcion, inverso = funciones[nombre]
            resultado = funcion(estado)
            if resultado is not None:
                estado = resultado
                anterior_inverso = inverso
                break
    return estado


def generar_instancias_para_n(n, cantidad, semilla=42):
    rng = random.Random(semilla + n)
    if LONGITUD_CAMINATA[n] is None:
        return generar_instancias_n(n, cantidad, semilla=semilla)
    return [generar_por_caminata(n, LONGITUD_CAMINATA[n], rng) for _ in range(cantidad)]


def correr_instancia(n, estado_inicial, meta):
    agente = RKNInformado(n=n, heuristica="h2")
    agente.set_estado_meta(meta)
    agente.set_estado_inicial(estado_inicial)
    agente.set_tecnica("a_estrella")
    agente.set_limites(nodos=LIMITE_NODOS, tiempo_s=LIMITE_TIEMPO_S)

    t0 = time.perf_counter()
    agente.programa()
    t1 = time.perf_counter()

    r = agente.get_medida_rendimiento()
    return {
        "n": n,
        "encontrado": r["pasos"] is not None,
        "timeout": r.get("timeout"),
        "pasos": (r["pasos"] - 1) if r["pasos"] is not None else None,
        "tiempo_ms": round((t1 - t0) * 1000, 3),
        "nodos_expandidos": r["nodos_expandidos"],
        "nodos_generados": r["nodos_generados"],
        "memoria_max": r["memoria_max"],
    }


def main():
    filas = []
    resumen_por_n = {}

    for n in TAMANOS:
        meta = estado_meta(n)
        instancias = generar_instancias_para_n(n, INSTANCIAS_POR_TAMANO)
        exitos = 0
        print(f"\n--- N={n} ({n}x{n}, {len(instancias)} instancias) ---")

        for idx, inst in enumerate(instancias):
            r = correr_instancia(n, inst, meta)
            r["instancia_id"] = idx
            filas.append(r)
            if r["encontrado"]:
                exitos += 1
            estado_str = "OK" if r["encontrado"] else f"TIMEOUT({r['timeout']})"
            print(f"  instancia {idx}: {estado_str}  "
                  f"nodos={r['nodos_expandidos']:>7}  tiempo={r['tiempo_ms']:>9.1f}ms")

        tasa_exito = exitos / len(instancias)
        resumen_por_n[n] = tasa_exito
        print(f"  Tasa de éxito N={n}: {tasa_exito:.0%}")

    os.makedirs(_RESULTADOS_DIR, exist_ok=True)
    with open(_SALIDA_DEFAULT, "w", newline="") as f:
        columnas = ["n", "instancia_id", "encontrado", "timeout", "pasos",
                    "tiempo_ms", "nodos_expandidos", "nodos_generados", "memoria_max"]
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"\nGuardado: {_SALIDA_DEFAULT}")

    n_max_factible = max([n for n, tasa in resumen_por_n.items() if tasa >= UMBRAL_EXITO], default=None)
    print(f"\nN máximo con >= {UMBRAL_EXITO:.0%} de éxito: {n_max_factible}")
    for n, tasa in resumen_por_n.items():
        print(f"  N={n}: {tasa:.0%} de éxito")


if __name__ == "__main__":
    main()
