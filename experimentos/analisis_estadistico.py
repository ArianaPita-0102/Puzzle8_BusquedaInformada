"""
Análisis Estadístico Formal (Parte 3).

Lee resultados_experimento1.csv y genera:
  1. Estadísticas descriptivas + IC 95% por algoritmo-heurística-métrica.
  2. Prueba de Friedman (por algoritmo, sobre nodos_expandidos y tiempo_ms).
  3. Post-hoc de Nemenyi si Friedman da significativo.
  4. Ranking compuesto de heurísticas.
  5. Gráficos: boxplots y barras con IC 95%.

Requiere: pandas, numpy, scipy, scikit-posthocs, matplotlib.
Si falta scikit-posthocs:  pip install scikit-posthocs

Uso (desde la carpeta raíz del proyecto):
    python experimentos/analisis_estadistico.py
"""

import argparse
import os
import warnings
import pandas as pd
import numpy as np
from scipy import stats
import scikit_posthocs as sp
import matplotlib.pyplot as plt

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RESULTADOS_DIR = os.path.join(_AQUI, "resultados")
_CSV_DEFAULT = os.path.join(_RESULTADOS_DIR, "resultados_experimento1.csv")

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*tick_labels.*")

ALPHA = 0.05
ORDEN_HEURISTICAS = ["h1", "h2", "h3", "h4", "h5", "h6_w0.3", "h6_w0.6", "h6_w1.0"]
METRICAS_FRIEDMAN = ["nodos_expandidos", "tiempo_ms"]


def cargar(csv_path):
    df = pd.read_csv(csv_path)
    df["heuristica"] = pd.Categorical(df["heuristica"], categories=ORDEN_HEURISTICAS, ordered=True)
    return df


def intervalo_confianza_95(serie):
    n = len(serie)
    media = serie.mean()
    error_std = serie.std(ddof=1) / np.sqrt(n)
    t_critico = stats.t.ppf(0.975, df=n - 1)
    return media - t_critico * error_std, media + t_critico * error_std


def estadisticas_descriptivas(df, metricas):
    filas = []
    for (algoritmo, heuristica), grupo in df.groupby(["algoritmo", "heuristica"], observed=True):
        for metrica in metricas:
            serie = grupo[metrica]
            ic_bajo, ic_alto = intervalo_confianza_95(serie)
            filas.append({
                "algoritmo": algoritmo,
                "heuristica": heuristica,
                "metrica": metrica,
                "media": serie.mean(),
                "mediana": serie.median(),
                "std": serie.std(ddof=1),
                "min": serie.min(),
                "max": serie.max(),
                "p25": serie.quantile(0.25),
                "p75": serie.quantile(0.75),
                "ic95_bajo": ic_bajo,
                "ic95_alto": ic_alto,
            })
    return pd.DataFrame(filas)


def tabla_por_instancia(df, algoritmo, metrica):
    """Pivotea a instancia_id x heurística, para Friedman y Nemenyi
    (cada instancia es un 'bloque' que recibe las 8 heurísticas)."""
    sub = df[df["algoritmo"] == algoritmo]
    tabla = sub.pivot(index="instancia_id", columns="heuristica", values=metrica)
    return tabla[ORDEN_HEURISTICAS]  # orden fijo de columnas


def prueba_friedman(tabla):
    columnas = [tabla[c].values for c in tabla.columns]
    estadistico, p_valor = stats.friedmanchisquare(*columnas)
    return estadistico, p_valor


def posthoc_nemenyi(tabla):
    return sp.posthoc_nemenyi_friedman(tabla.values)


def ranking_compuesto(df):
    """Para cada algoritmo, rankea las heurísticas por mediana de nodos,
    tiempo y memoria (menor=mejor) y promedia los 3 rangos."""
    resultados = []
    for algoritmo, grupo in df.groupby("algoritmo"):
        medianas = grupo.groupby("heuristica", observed=True).agg(
            nodos_expandidos=("nodos_expandidos", "median"),
            tiempo_ms=("tiempo_ms", "median"),
            memoria_max=("memoria_max", "median"),
        )
        rangos = medianas.rank(method="average")  # 1 = mejor (menor valor)
        rango_compuesto = rangos.mean(axis=1).sort_values()
        for heuristica, valor in rango_compuesto.items():
            resultados.append({
                "algoritmo": algoritmo,
                "heuristica": heuristica,
                "rango_promedio": valor,
            })
    return pd.DataFrame(resultados).sort_values(["algoritmo", "rango_promedio"])


def graficar_boxplot(df, metrica, algoritmo, salida):
    sub = df[df["algoritmo"] == algoritmo]
    datos = [sub[sub["heuristica"] == h][metrica].values for h in ORDEN_HEURISTICAS]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot(datos, showfliers=False)
    ax.set_xticks(range(1, len(ORDEN_HEURISTICAS) + 1))
    ax.set_xticklabels(ORDEN_HEURISTICAS)
    ax.set_title(f"{metrica} por heurística — {algoritmo}")
    ax.set_ylabel(metrica)
    ax.set_xlabel("heurística")
    plt.xticks(rotation=30)
    plt.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)


def graficar_barras_ic(desc_df, metrica, algoritmo, salida):
    sub = desc_df[(desc_df["algoritmo"] == algoritmo) & (desc_df["metrica"] == metrica)]
    sub = sub.set_index("heuristica").loc[ORDEN_HEURISTICAS]
    errores = [sub["media"] - sub["ic95_bajo"], sub["ic95_alto"] - sub["media"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(ORDEN_HEURISTICAS, sub["media"], yerr=errores, capsize=4)
    ax.set_title(f"Media de {metrica} ± IC 95% — {algoritmo}")
    ax.set_ylabel(metrica)
    plt.xticks(rotation=30)
    plt.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)


def main(csv_path):
    df = cargar(csv_path)
    metricas_desc = ["pasos", "tiempo_ms", "nodos_expandidos", "nodos_generados", "memoria_max"]

    # 1. Estadísticas descriptivas
    os.makedirs(_RESULTADOS_DIR, exist_ok=True)

    desc = estadisticas_descriptivas(df, metricas_desc)
    ruta_desc = os.path.join(_RESULTADOS_DIR, "resumen_descriptivo.csv")
    desc.to_csv(ruta_desc, index=False)
    print(f"Guardado: {ruta_desc}")

    # 2 y 3. Friedman + post-hoc, por algoritmo y por métrica
    lineas_friedman = []
    for algoritmo in df["algoritmo"].unique():
        for metrica in METRICAS_FRIEDMAN:
            tabla = tabla_por_instancia(df, algoritmo, metrica)
            estadistico, p_valor = prueba_friedman(tabla)
            significativo = p_valor < ALPHA
            lineas_friedman.append(
                f"{algoritmo:12s} | {metrica:18s} | chi2={estadistico:10.2f} | "
                f"p={p_valor:.3e} | {'SIGNIFICATIVO' if significativo else 'no significativo'}"
            )
            print(lineas_friedman[-1])

            if significativo:
                nemenyi = posthoc_nemenyi(tabla)
                nemenyi.columns = ORDEN_HEURISTICAS
                nemenyi.index = ORDEN_HEURISTICAS
                salida = os.path.join(_RESULTADOS_DIR, f"posthoc_nemenyi_{algoritmo}_{metrica}.csv")
                nemenyi.to_csv(salida)
                print(f"  -> post-hoc guardado en {salida}")

    ruta_friedman = os.path.join(_RESULTADOS_DIR, "friedman_resultados.txt")
    with open(ruta_friedman, "w") as f:
        f.write("\n".join(lineas_friedman))
    print(f"Guardado: {ruta_friedman}")

    # 4. Ranking compuesto
    ranking = ranking_compuesto(df)
    ruta_ranking = os.path.join(_RESULTADOS_DIR, "ranking_compuesto.csv")
    ranking.to_csv(ruta_ranking, index=False)
    print(f"Guardado: {ruta_ranking}")
    print(ranking.to_string(index=False))

    # 5. Gráficos
    for algoritmo in df["algoritmo"].unique():
        graficar_boxplot(df, "nodos_expandidos", algoritmo, os.path.join(_RESULTADOS_DIR, f"boxplot_nodos_{algoritmo}.png"))
        graficar_boxplot(df, "tiempo_ms", algoritmo, os.path.join(_RESULTADOS_DIR, f"boxplot_tiempo_{algoritmo}.png"))
        graficar_barras_ic(desc, "nodos_expandidos", algoritmo, os.path.join(_RESULTADOS_DIR, f"barras_ic_nodos_{algoritmo}.png"))
    print("Guardados: boxplots y barras con IC (.png)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default=_CSV_DEFAULT)
    args = parser.parse_args()
    main(args.csv)