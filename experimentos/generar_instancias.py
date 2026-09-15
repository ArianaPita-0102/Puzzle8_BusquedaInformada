import json
import os
import random

_AQUI = os.path.dirname(os.path.abspath(__file__))
_SALIDA_DEFAULT = os.path.join(_AQUI, "instancias_puzzle8.json")

ESTADO_META = [[1, 2, 3], [4, 5, 6], [7, 8, 0]]


def contar_inversiones(permutacion_sin_blanco):
    inversiones = 0
    n = len(permutacion_sin_blanco)
    for i in range(n):
        for j in range(i + 1, n):
            if permutacion_sin_blanco[i] > permutacion_sin_blanco[j]:
                inversiones += 1
    return inversiones


def es_soluble(plano):
    sin_blanco = [v for v in plano if v != 0]
    return contar_inversiones(sin_blanco) % 2 == 0


def plano_a_tablero(plano):
    return [plano[0:3], plano[3:6], plano[6:9]]


def generar_una_instancia_soluble(rng):
    plano = list(range(9))
    while True:
        rng.shuffle(plano)
        if es_soluble(plano):
            return plano_a_tablero(plano)


def generar_instancias(n, semilla=42):
    rng = random.Random(semilla)
    instancias = []
    vistos = set()
    while len(instancias) < n:
        tablero = generar_una_instancia_soluble(rng)
        clave = tuple(tuple(f) for f in tablero)
        if clave in vistos:
            continue
        vistos.add(clave)
        instancias.append(tablero)
    return instancias


if __name__ == "__main__":
    N = 1000
    instancias = generar_instancias(N, semilla=42)

    print(f"Generadas {len(instancias)} instancias únicas y solubles.")
    print("Ejemplo de instancia 0:", instancias[0])

    with open(_SALIDA_DEFAULT, "w") as f:
        json.dump(instancias, f)
    print(f"Guardado en {_SALIDA_DEFAULT}")
