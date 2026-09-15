# Puzzle-8 / Puzzle-N — Heurísticas, Búsqueda Informada y Escalabilidad

Proyecto de la práctica "Estudio Comparativo de Heurísticas, Algoritmo
Codicioso y A\* en el Puzzle-8 y sus Generalizaciones" (Inteligencia
Artificial, UCB).

## 1. Instalación

Requiere Python 3.10+. Instalar dependencias:

```bash
pip install numpy pandas scipy matplotlib scikit-posthocs pygame
```

(o `pip install --break-system-packages ...` si tu sistema lo exige).

Para compilar el informe también hace falta una distribución LaTeX
(MiKTeX en Windows, TeX Live en Linux/Mac) — ver la Sección 6.

## 2. Cómo ejecutar — TODOS los comandos se corren desde la carpeta
raíz del proyecto (esta misma carpeta, donde está este README).

| Qué querés hacer                                                       | Comando                                                              |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Ver el juego (PyGame)                                                  | `python juego/juego_puzzle.py`                                       |
| Correr el Experimento 1 completo (1000 instancias)                     | `python experimentos/experimento1.py`                                |
| Correr el Experimento 1 rápido, de prueba (5 instancias)               | `python experimentos/experimento1.py --n 5 --salida /tmp/prueba.csv` |
| Regenerar las 1000 instancias (ya vienen generadas)                    | `python experimentos/generar_instancias.py`                          |
| Correr el análisis estadístico (Friedman, post-hoc, ranking, gráficos) | `python experimentos/analisis_estadistico.py`                        |
| Correr el Experimento 2 (escalabilidad N×N)                            | `python experimentos/escalabilidad.py`                               |
| Ajustar el modelo de crecimiento (exponencial/potencial)               | `python experimentos/modelar_crecimiento.py`                         |
| Verificar admisibilidad de las heurísticas (181.440 estados)           | `python verificacion/verificar_admisibilidad.py`                     |
| Verificar consistencia de las heurísticas (483.840 aristas)            | `python verificacion/verificar_consistencia.py`                      |
| Ejemplo mínimo de heurísticas                                          | `python core/demo01.py`                                              |
| Compilar el informe final en PDF                                       | ver Sección 6                                                        |

Todos los scripts calculan sus rutas de entrada/salida en base a su
propia ubicación en el proyecto (no dependen de "desde dónde" los
llames), así que también funcionan si los ejecutás desde otra carpeta,
por ejemplo `python /ruta/al/proyecto/experimentos/experimento1.py`.

## 3. Estructura del proyecto

```
proyecto_8puzzle/
├── AgenteIA/                  Framework del curso (Agente, Entorno,
│                               AgenteBuscador). NO modificar.
├── core/                      El "problema": heurísticas y estados.
│   ├── AgenteRK8.py            Puzzle-8 (3x3) con H1-H6.
│   ├── agente_rkn.py           Generalización a N×N (H1, H2).
│   └── demo01.py               Ejemplo mínimo de uso.
├── busqueda/                  Los "algoritmos" (Greedy y A*).
│   ├── agente_buscador_informado.py   Extiende AgenteBuscador con
│   │                                   heapq (Codicioso + A*).
│   ├── rk8_informado.py        Junta Puzzle-8 + Codicioso/A*.
│   └── rkn_informado.py        Junta Puzzle-N + Codicioso/A*.
├── verificacion/              Comprobaciones formales de las heurísticas.
│   ├── verificar_admisibilidad.py   h(s) <= distancia óptima real.
│   └── verificar_consistencia.py    h(s) <= costo(s,s') + h(s').
├── experimentos/              Generación de datos y análisis.
│   ├── generar_instancias.py        1000 instancias (3x3).
│   ├── generar_instancias_n.py      Instancias para N×N.
│   ├── experimento1.py              Corre Codicioso/A* x 6 heurísticas
│   │                                 x 1000 instancias.
│   ├── analisis_estadistico.py      Descriptivas, IC95%, Friedman,
│   │                                 Nemenyi, ranking, gráficos.
│   ├── escalabilidad.py             Experimento 2 (N×N).
│   ├── modelar_crecimiento.py       Ajuste exponencial/potencial.
│   ├── instancias_puzzle8.json      Las 1000 instancias ya generadas.
│   └── resultados/                  Todos los CSV/PNG/TXT generados.
├── juego/
│   ├── juego_puzzle.py         Juego en PyGame (dificultad = tamaño
│   │                             del tablero, botón "Asistente" = A*).
│   └── capturas/                Capturas de pantalla del juego,
│                                 usadas por el informe (menu.png,
│                                 tablero.png).
└── documentos/
    ├── informe.tex              Informe técnico final (ver Sección 6).
    └── informe.pdf              Versión ya compilada.
```

## 4. Estado de los resultados incluidos

- `experimentos/resultados/resultados_experimento1.csv` y todo el
  análisis estadístico derivado (`resumen_descriptivo.csv`,
  `friedman_resultados.txt`, `posthoc_nemenyi_*.csv`,
  `ranking_compuesto.csv`, los `.png`) corresponden a la corrida
  original de 1000 instancias × 2 algoritmos × 8 variantes de
  heurística. **Siguen siendo válidos** — no hace falta volver a
  correr el Experimento 1.
- `experimentos/resultados/resultados_escalabilidad.csv` y
  `crecimiento_nodos_vs_n.png` corresponden a la corrida **con 30
  instancias por tamaño y límite de 60s** — esos son los números que
  usa el informe (`documentos/informe.tex`). El script
  `escalabilidad.py` tiene sus constantes puestas en 100
  instancias/300s (los valores de ejemplo del PDF de la práctica),
  pero **no se volvió a correr con esos valores** — se decidió
  conservar los resultados originales de 30/60s por tiempo de
  cómputo. Si en algún momento se corre con 100/300s, hay que
  actualizar la Sección 5.2 y la Sección de escalabilidad del informe
  con los números nuevos.

## 5. Verificación de consistencia

`verificacion/verificar_consistencia.py` complementa a
`verificar_admisibilidad.py`: reconstruye el mismo espacio de 181.440
estados solubles del Puzzle-8 y, en vez de comparar cada estado contra
la distancia óptima (admisibilidad), revisa la desigualdad
`h(s) ≤ costo(s,s') + h(s')` sobre las 483.840 aristas del grafo de
estados (consistencia). No modifica ninguna heurística existente.

Resultado esperado (ya verificado): H1, H2, H3 y H5 son consistentes
en el 100% de los casos; H4 falla en ~8.6% de las aristas (coherente
con que tampoco es admisible). Estos números ya están incorporados en
`documentos/informe.tex`.

## 6. Informe (LaTeX)

`documentos/informe.tex` es el informe técnico final, con todos los
resultados reales de `experimentos/resultados/`, de `verificacion/` y
las capturas de `juego/capturas/`. Compilarlo:

```bash
cd documentos
pdflatex informe.tex
pdflatex informe.tex   # segunda pasada, para resolver referencias cruzadas
```

Requiere una distribución LaTeX (TeX Live, MiKTeX) con los paquetes
`babel` (idioma español), `booktabs`, `float`, `caption`, `hyperref`,
`geometry`, `graphicx` — todos estándar, vienen incluidos en
cualquier instalación completa de TeX Live/MiKTeX.

**Si usás VS Code + LaTeX Workshop y te da el error `spawn latexmk
ENOENT` o "MiKTeX could not find the script engine 'perl'"**: la
extensión intenta usar `latexmk` por defecto, que necesita Perl.
Configurá una receta que use `pdflatex` directo (Settings →
`latex-workshop.latex.recipes` / `latex-workshop.latex.tools`, dos
pasadas de `pdflatex`), o instalá Perl (Strawberry Perl) si preferís
mantener `latexmk`.

Las imágenes se referencian directamente desde
`experimentos/resultados/` y `juego/capturas/` (no están duplicadas
dentro de `documentos/`), así que si se vuelven a correr los
experimentos o se agregan capturas nuevas, el informe usa
automáticamente las últimas versiones la próxima vez que se compile.

## 7. Notas sobre el juego (PyGame)

- El control es "clic en la ficha adyacente al vacío" — es el
  esquema estándar de cualquier puzzle deslizante; el PDF no exige
  un esquema de control específico.
- El botón "Asistente" usa A\* con Manhattan (H2) sobre el estado
  actual del tablero, reutilizando el mismo motor de búsqueda del
  Experimento 1/2 (`busqueda/rkn_informado.py`).
- En 5×5, si el tablero está muy revuelto (por scramble inicial +
  muchos movimientos manuales), el asistente puede alcanzar su
  límite de nodos (400.000) o de tiempo (35s) sin terminar. Esto es
  esperado: A\* con Manhattan sobre 5×5 tiene un costo que crece muy
  rápido con la dificultad real del tablero (mismo fenómeno que en
  `escalabilidad.py`, donde N=5 ya no siempre se resuelve al 100%).
  El mensaje que se muestra indica explícitamente si se alcanzó el
  límite de nodos o el de tiempo, en vez de sugerir que el tablero no
  tiene solución (todo estado alcanzado jugando SÍ es soluble, porque
  los movimientos preservan la solubilidad).
