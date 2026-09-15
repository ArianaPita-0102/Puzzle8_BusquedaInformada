import argparse
import csv
import os
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RESULTADOS_DIR = os.path.join(_AQUI, "resultados")
_CSV_DEFAULT = os.path.join(_RESULTADOS_DIR, "resultados_escalabilidad.csv")
_GRAFICO_DEFAULT = os.path.join(_RESULTADOS_DIR, "crecimiento_nodos_vs_n.png")


UMBRAL_EXITO_PARA_AJUSTE = 0.5


def cargar_medianas(csv_path):
    por_n = defaultdict(list)
    total_por_n = defaultdict(int)
    with open(csv_path) as f:
        for fila in csv.DictReader(f):
            n = int(fila["n"])
            total_por_n[n] += 1
            if fila["encontrado"] == "True":
                por_n[n].append(int(fila["nodos_expandidos"]))

    ns, medianas, excluidos = [], [], []
    for n in sorted(por_n):
        tasa_exito = len(por_n[n]) / total_por_n[n]
        if not por_n[n]:
            continue
        if tasa_exito < UMBRAL_EXITO_PARA_AJUSTE:
            excluidos.append((n, tasa_exito))
            continue
        ns.append(n)
        medianas.append(float(np.median(por_n[n])))

    if excluidos:
        print("Excluidos del ajuste por sesgo de supervivencia (tasa de éxito < "
              f"{UMBRAL_EXITO_PARA_AJUSTE:.0%}):")
        for n, tasa in excluidos:
            print(f"  N={n}: solo {tasa:.0%} de instancias resueltas a tiempo "
                  "-> su mediana no representa el costo real, se descarta del ajuste")

    return np.array(ns), np.array(medianas)


def r_cuadrado(y_real, y_pred):
    ss_res = np.sum((y_real - y_pred) ** 2)
    ss_tot = np.sum((y_real - np.mean(y_real)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def ajustar_exponencial(ns, medianas):
    log_y = np.log(medianas)
    pendiente, intercepto = np.polyfit(ns, log_y, 1)
    a = np.exp(intercepto)
    b = np.exp(pendiente)
    pred = a * b ** ns
    r2 = r_cuadrado(medianas, pred)
    return a, b, r2


def ajustar_potencial(ns, medianas):
    log_y = np.log(medianas)
    log_x = np.log(ns)
    c, intercepto = np.polyfit(log_x, log_y, 1)
    a = np.exp(intercepto)
    pred = a * ns ** c
    r2 = r_cuadrado(medianas, pred)
    return a, c, r2


def graficar(ns, medianas, a_exp, b_exp, a_pot, c_pot, salida):
    ns_finos = np.linspace(ns.min(), ns.max(), 100)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(ns, medianas, label="datos (mediana por N)", zorder=3)
    ax.plot(ns_finos, a_exp * b_exp ** ns_finos, "--", label=f"exponencial: {a_exp:.2f}·{b_exp:.2f}^N")
    ax.plot(ns_finos, a_pot * ns_finos ** c_pot, "--", label=f"potencial: {a_pot:.2f}·N^{c_pot:.2f}")
    ax.set_yscale("log")
    ax.set_xlabel("N (tamaño del tablero)")
    ax.set_ylabel("nodos expandidos (mediana, escala log)")
    ax.set_title("Crecimiento de nodos expandidos vs. tamaño del tablero")
    ax.legend()
    plt.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)


def main(csv_path):
    ns, medianas = cargar_medianas(csv_path)
    print("N con al menos una instancia resuelta:", ns)
    print("Mediana de nodos expandidos:", medianas)

    if len(ns) < 3:
        print("Muy pocos puntos con solución para ajustar un modelo confiable "
              "(hacen falta al menos 3 tamaños de N con éxito). Corré con más "
              "instancias o tamaños más chicos.")
        return

    a_exp, b_exp, r2_exp = ajustar_exponencial(ns, medianas)
    a_pot, c_pot, r2_pot = ajustar_potencial(ns, medianas)

    print(f"\nModelo exponencial: nodos(N) ≈ {a_exp:.3f} * {b_exp:.3f}^N   (R² = {r2_exp:.4f})")
    print(f"Modelo potencial:   nodos(N) ≈ {a_pot:.3f} * N^{c_pot:.3f}     (R² = {r2_pot:.4f})")

    mejor = "exponencial" if r2_exp > r2_pot else "potencial"
    print(f"\nMejor ajuste: modelo {mejor}")

    os.makedirs(_RESULTADOS_DIR, exist_ok=True)
    graficar(ns, medianas, a_exp, b_exp, a_pot, c_pot, _GRAFICO_DEFAULT)
    print(f"Guardado: {_GRAFICO_DEFAULT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=_CSV_DEFAULT)
    args = parser.parse_args()
    main(args.csv)