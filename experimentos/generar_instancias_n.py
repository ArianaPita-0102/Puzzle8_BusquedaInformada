"""
Genera configuraciones iniciales aleatorias y solubles para un
Puzzle-N (tablero N x N), donde la meta es 1..N²-1 seguido del 0
en la última celda.

Regla de solubilidad (resultado clásico de teoría de grupos):
- Si N es IMPAR: soluble si el número de inversiones es PAR.
- Si N es PAR: soluble si (inversiones + fila_del_blanco_desde_abajo,
  contando desde 1) es IMPAR.

Para N=3 esto coincide exactamente con la regla que ya usamos en
generar_instancias.py (caso impar).
"""

import random


def contar_inversiones(permutacion_sin_blanco):
    inversiones = 0
    m = len(permutacion_sin_blanco)
    for i in range(m):
        for j in range(i + 1, m):
            if permutacion_sin_blanco[i] > permutacion_sin_blanco[j]:
                inversiones += 1
    return inversiones


def es_soluble(plano, n):
    sin_blanco = [v for v in plano if v != 0]
    inversiones = contar_inversiones(sin_blanco)
    if n % 2 == 1:
        return inversiones % 2 == 0
    else:
        fila_blanco_idx = plano.index(0) // n          # 0-indexada desde arriba
        fila_desde_abajo = n - fila_blanco_idx          # 1-indexada desde abajo
        return (inversiones + fila_desde_abajo) % 2 == 1


def plano_a_tablero(plano, n):
    return [plano[i * n:(i + 1) * n] for i in range(n)]


def estado_meta(n):
    plano = list(range(1, n * n)) + [0]
    return plano_a_tablero(plano, n)


def generar_una_instancia_soluble(n, rng):
    plano = list(range(n * n))
    while True:
        rng.shuffle(plano)
        if es_soluble(plano, n):
            return plano_a_tablero(plano, n)


def generar_instancias_n(n, cantidad, semilla=42):
    rng = random.Random(semilla + n)  # semilla distinta por tamaño, reproducible
    instancias = []
    vistos = set()
    intentos_maximos = cantidad * 50  # margen de seguridad contra duplicados
    intentos = 0
    while len(instancias) < cantidad and intentos < intentos_maximos:
        intentos += 1
        tablero = generar_una_instancia_soluble(n, rng)
        clave = tuple(tuple(f) for f in tablero)
        if clave in vistos:
            continue
        vistos.add(clave)
        instancias.append(tablero)
    return instancias


if __name__ == "__main__":
    for n in [3, 4, 5]:
        ejemplo = generar_instancias_n(n, 3, semilla=42)
        print(f"N={n}, meta={estado_meta(n)}")
        for e in ejemplo:
            print("  ", e)
