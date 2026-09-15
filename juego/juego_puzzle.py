"""
Juego del Puzzle-N (deslizante) en pygame, para la Parte 4 de la
práctica. El tamaño del tablero funciona como nivel de dificultad, y
hay un "asistente" que resuelve el rompecabezas usando A* en vivo,
reutilizando exactamente el mismo código de búsqueda de las Partes 2-4
(rkn_informado.py / AgenteBuscadorInformado / AgenteRKN).

Controles:
  - Clic en una ficha adyacente al espacio vacío -> la mueve.
  - Botón "Asistente" -> A* resuelve y anima la solución automáticamente.
  - Botón "Barajar" -> genera un tablero nuevo (siempre soluble).
  - Botón "Menú" -> vuelve a elegir dificultad.

Ejecutar (desde la carpeta raíz del proyecto):
    python juego/juego_puzzle.py
"""

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

import pygame

# Evita que Windows escale la ventana de forma rara cuando el "zoom"
# de pantalla no es 100% (125%, 150%, etc.). Tiene que fijarse ANTES
# de pygame.init().
if sys.platform == "win32":
    os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"

from busqueda.rkn_informado import RKNInformado
from experimentos.generar_instancias_n import estado_meta

# ------------------------------------------------------------------
# Configuración general
# ------------------------------------------------------------------
TAMANO_FICHA = 100
ALTO_HEADER = 150
FPS = 60

# La ventana tiene un tamaño FIJO durante toda la ejecución del juego
# -- nunca se vuelve a llamar pygame.display.set_mode() después de
# main(). Antes la ventana cambiaba de tamaño según N (3x3, 4x4, 5x5)
# y al volver al menú, lo que desalineaba los clicks respecto a los
# botones (un clic en cualquier lado terminaba "cayendo" sobre algún
# botón viejo). Con tamaño fijo ese problema no puede volver a pasar,
# sea cual sea el N elegido: los tableros más chicos simplemente se
# centran dentro de la misma ventana.
ANCHO_VENTANA = 650
ALTO_VENTANA = ALTO_HEADER + TAMANO_FICHA * 5 + 90  # alcanza para N=5, el más grande

DIFICULTADES = [
    ("Fácil (3x3)", 3, 25),
    ("Medio (4x4)", 4, 30),
    ("Difícil (5x5)", 5, 30),
]  # (etiqueta, N, longitud de la caminata de barajado)
# Estos valores son más chicos que los usados en escalabilidad.py (Parte
# 4) a propósito: ahí queríamos ENCONTRAR el límite de A* con instancias
# bien difíciles; acá queremos que el juego sea DIVERTIDO y que el
# asistente responda rápido casi siempre.

# Límite de seguridad para el asistente: aun con caminatas cortas, por
# si el jugador mueve fichas manualmente hacia una configuración más
# difícil antes de pedir ayuda.
LIMITE_NODOS_ASISTENTE = 400_000
LIMITE_TIEMPO_ASISTENTE_S = 35

COLOR_FONDO = (30, 30, 40)
COLOR_FICHA = (70, 130, 200)
COLOR_FICHA_HOVER = (90, 150, 220)
COLOR_VACIO = (30, 30, 40)
COLOR_TEXTO = (255, 255, 255)
COLOR_BOTON = (60, 180, 100)
COLOR_BOTON_HOVER = (80, 200, 120)
COLOR_BOTON_ASISTENTE = (200, 130, 60)
COLOR_BOTON_ASISTENTE_HOVER = (220, 150, 80)
COLOR_GANASTE = (250, 210, 50)


def generar_tablero_barajado(n, longitud_caminata, rng):
    """Arranca en la meta y aplica movimientos válidos al azar (evitando
    deshacer el paso anterior), igual que en escalabilidad.py. Así el
    tablero siempre es soluble por construcción."""
    agente = RKNInformado(n=n, heuristica="h2")
    meta = estado_meta(n)
    agente.set_estado_meta(meta)
    estado = [fila[:] for fila in meta]
    anterior_inverso = None
    funciones = {
        "arriba": (agente.arriba, "abajo"),
        "abajo": (agente.abajo, "arriba"),
        "izquierda": (agente.izquierda, "derecha"),
        "derecha": (agente.derecha, "izquierda"),
    }
    for _ in range(longitud_caminata):
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


def resolver_con_asistente(n, estado_actual, meta):
    """Corre A* con distancia Manhattan (h2) desde el estado actual.

    Devuelve (pasos, motivo_timeout):
      - pasos: lista de tableros de la solución (vacía si no se encontró).
      - motivo_timeout: None si encontró solución; si no, "nodos" o
        "tiempo" según cuál límite se alcanzó primero (viene directo
        de rendimiento["timeout"], que agente_buscador_informado.py ya
        calcula). Sirve para poder avisarle al jugador la razón real
        en vez de un genérico "no encontró solución", que sería
        engañoso: todo estado alcanzable jugando SIEMPRE es soluble
        (los movimientos preservan la solubilidad), así que si no se
        encontró solución es 100% porque se cortó por presupuesto, no
        porque el estado sea irresoluble.

    Se usa h2 (no h5) porque el puzzle generalizado a NxN
    (agente_rkn.py) no implementa Pattern Database — ver la
    justificación en ese archivo.
    """
    agente = RKNInformado(n=n, heuristica="h2")
    agente.set_estado_meta(meta)
    agente.set_estado_inicial(estado_actual)
    agente.set_tecnica("a_estrella")
    agente.set_limites(nodos=LIMITE_NODOS_ASISTENTE, tiempo_s=LIMITE_TIEMPO_ASISTENTE_S)
    agente.programa()
    pasos = agente.get_acciones()  # lista de tableros, del inicial al final
    motivo_timeout = agente.get_medida_rendimiento().get("timeout")
    return pasos, motivo_timeout


def pos_blanco(estado):
    n = len(estado)
    for i in range(n):
        for j in range(n):
            if estado[i][j] == 0:
                return i, j


def mover_si_valido(estado, fila_click, col_click):
    """Si la celda clickeada es adyacente al blanco, intercambia y
    devuelve el nuevo estado; si no, devuelve el mismo estado."""
    fi, fj = pos_blanco(estado)
    if abs(fi - fila_click) + abs(fj - col_click) == 1:
        nuevo = [f[:] for f in estado]
        nuevo[fi][fj], nuevo[fila_click][col_click] = nuevo[fila_click][col_click], nuevo[fi][fj]
        return nuevo
    return estado


class Boton:
    def __init__(self, rect, texto, color, color_hover):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.color = color
        self.color_hover = color_hover

    def dibujar(self, pantalla, fuente, mouse_pos):
        color = self.color_hover if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(pantalla, color, self.rect, border_radius=8)
        superficie_texto = fuente.render(self.texto, True, COLOR_TEXTO)
        pantalla.blit(superficie_texto, superficie_texto.get_rect(center=self.rect.center))

    def clickeado(self, pos):
        return self.rect.collidepoint(pos)


def pantalla_menu(pantalla, fuente_grande, fuente):
    botones = []
    ancho, _ = pantalla.get_size()
    y = 250
    for etiqueta, n, longitud in DIFICULTADES:
        rect = (ancho // 2 - 150, y, 300, 70)
        botones.append((Boton(rect, etiqueta, COLOR_BOTON, COLOR_BOTON_HOVER), n, longitud))
        y += 100

    fuente_titulo = pygame.font.SysFont("arial", 30, bold=True)
    reloj = pygame.time.Clock()
    while True:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                for boton, n, longitud in botones:
                    if boton.clickeado(evento.pos):
                        return n, longitud

        pantalla.fill(COLOR_FONDO)
        linea1 = fuente_titulo.render("Puzzle Deslizante", True, COLOR_TEXTO)
        linea2 = fuente_titulo.render("Elige la dificultad", True, COLOR_TEXTO)
        pantalla.blit(linea1, linea1.get_rect(center=(ancho // 2, 100)))
        pantalla.blit(linea2, linea2.get_rect(center=(ancho // 2, 145)))
        for boton, _, _ in botones:
            boton.dibujar(pantalla, fuente, mouse_pos)
        pygame.display.flip()
        reloj.tick(FPS)


def jugar(pantalla, fuente_grande, fuente, n, longitud_caminata):
    # OJO: ya NO se llama a pygame.display.set_mode() acá. La ventana
    # mantiene el tamaño fijo (ANCHO_VENTANA x ALTO_VENTANA) de main();
    # tableros más chicos que 5x5 se centran horizontalmente adentro.
    ancho_tablero = TAMANO_FICHA * n
    offset_x = (ANCHO_VENTANA - ancho_tablero) // 2

    meta = estado_meta(n)
    rng = random.Random()
    estado = generar_tablero_barajado(n, longitud_caminata, rng)

    movimientos_totales = 0
    uso_asistente = False  # solo indica SI se usó, no un número separado --
    # así nunca puede haber dos números distintos en pantalla al mismo tiempo.
    tiempo_inicio = time.time()
    tiempo_final = None
    ganado = False

    # Animación del asistente
    animacion_pasos = None
    indice_animacion = 0
    ultimo_paso_tiempo = 0
    INTERVALO_ANIMACION_MS = 300

    boton_asistente = Boton((20, 20, 160, 50), "Asistente (A*)", COLOR_BOTON_ASISTENTE, COLOR_BOTON_ASISTENTE_HOVER)
    boton_barajar = Boton((200, 20, 130, 50), "Barajar", COLOR_BOTON, COLOR_BOTON_HOVER)
    boton_menu = Boton((350, 20, 110, 50), "Menú", COLOR_BOTON, COLOR_BOTON_HOVER)

    reloj = pygame.time.Clock()
    mensaje_estado = ""

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_menu.clickeado(evento.pos):
                    return
                if boton_barajar.clickeado(evento.pos):
                    estado = generar_tablero_barajado(n, longitud_caminata, rng)
                    movimientos_totales = 0
                    uso_asistente = False
                    tiempo_inicio = time.time()
                    tiempo_final = None
                    ganado = False
                    animacion_pasos = None
                    mensaje_estado = ""
                    continue
                if boton_asistente.clickeado(evento.pos) and animacion_pasos is None and not ganado:
                    mensaje_estado = "Resolviendo con A*..."
                    pantalla.fill(COLOR_FONDO)
                    aviso = fuente.render(mensaje_estado, True, COLOR_TEXTO)
                    pantalla.blit(aviso, aviso.get_rect(center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2)))
                    pygame.display.flip()

                    pasos, motivo_timeout = resolver_con_asistente(n, estado, meta)
                    if not pasos or pasos[-1] != meta:
                        # Todo estado alcanzado jugando es soluble por
                        # construcción (los movimientos preservan la
                        # solubilidad); si no hay pasos es porque se
                        # agotó el presupuesto de nodos o de tiempo,
                        # no porque el estado sea irresoluble. Avisamos
                        # cuál de los dos límites fue.
                        if motivo_timeout == "nodos":
                            mensaje_estado = (
                                f"El asistente alcanzó el límite de "
                                f"{LIMITE_NODOS_ASISTENTE:,} nodos expandidos "
                                f"sin terminar de resolverlo (tablero {n}x{n} "
                                f"muy difícil desde este estado)."
                            )
                        elif motivo_timeout == "tiempo":
                            mensaje_estado = (
                                f"El asistente alcanzó el límite de "
                                f"{LIMITE_TIEMPO_ASISTENTE_S}s sin terminar de "
                                f"resolverlo (tablero {n}x{n} muy difícil desde "
                                f"este estado)."
                            )
                        else:
                            mensaje_estado = "El asistente no pudo resolverlo dentro del presupuesto disponible."
                        animacion_pasos = None
                    else:
                        animacion_pasos = pasos
                        indice_animacion = 0
                        ultimo_paso_tiempo = pygame.time.get_ticks()
                        mensaje_estado = "Asistente resolviendo..."
                    continue

                if animacion_pasos is None and not ganado:
                    x, y = evento.pos
                    if y >= ALTO_HEADER and x >= offset_x:
                        col = (x - offset_x) // TAMANO_FICHA
                        fila = (y - ALTO_HEADER) // TAMANO_FICHA
                        if 0 <= fila < n and 0 <= col < n:
                            nuevo_estado = mover_si_valido(estado, fila, col)
                            if nuevo_estado != estado:
                                estado = nuevo_estado
                                movimientos_totales += 1
                                mensaje_estado = ""
                                if estado == meta:
                                    ganado = True
                                    tiempo_final = time.time() - tiempo_inicio

        # Animación del asistente: avanza un paso cada INTERVALO_ANIMACION_MS
        if animacion_pasos is not None:
            ahora = pygame.time.get_ticks()
            if ahora - ultimo_paso_tiempo >= INTERVALO_ANIMACION_MS:
                indice_animacion += 1
                ultimo_paso_tiempo = ahora
                if indice_animacion >= len(animacion_pasos):
                    estado = animacion_pasos[-1]
                    uso_asistente = True
                    animacion_pasos = None
                    ganado = True
                    tiempo_final = time.time() - tiempo_inicio
                    mensaje_estado = ""
                else:
                    estado = animacion_pasos[indice_animacion]
                    movimientos_totales += 1  # un movimiento real = pasar de
                    # un estado al siguiente; la última vuelta del loop solo
                    # detecta el final y no mueve ninguna ficha, así que no
                    # debe contar (antes sumaba uno de más).

        # --- Dibujo ---
        pantalla.fill(COLOR_FONDO)

        boton_asistente.dibujar(pantalla, fuente, mouse_pos)
        boton_barajar.dibujar(pantalla, fuente, mouse_pos)
        boton_menu.dibujar(pantalla, fuente, mouse_pos)

        tiempo_mostrado = tiempo_final if tiempo_final is not None else (time.time() - tiempo_inicio)
        info = f"Movimientos: {movimientos_totales}    Tiempo: {int(tiempo_mostrado)}s"
        superficie_info = fuente.render(info, True, COLOR_TEXTO)
        pantalla.blit(superficie_info, (20, 80))
        if mensaje_estado:
            superficie_mensaje = fuente.render(mensaje_estado, True, COLOR_TEXTO)
            pantalla.blit(superficie_mensaje, (20, 110))

        for i in range(n):
            for j in range(n):
                valor = estado[i][j]
                x = offset_x + j * TAMANO_FICHA
                y = ALTO_HEADER + i * TAMANO_FICHA
                rect = pygame.Rect(x, y, TAMANO_FICHA - 4, TAMANO_FICHA - 4)
                if valor == 0:
                    pygame.draw.rect(pantalla, COLOR_VACIO, rect, border_radius=6)
                else:
                    color = COLOR_FICHA_HOVER if rect.collidepoint(mouse_pos) else COLOR_FICHA
                    pygame.draw.rect(pantalla, color, rect, border_radius=6)
                    texto = fuente_grande.render(str(valor), True, COLOR_TEXTO)
                    pantalla.blit(texto, texto.get_rect(center=rect.center))

        if ganado:
            overlay = pygame.Surface((ANCHO_VENTANA, ALTO_VENTANA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            pantalla.blit(overlay, (0, 0))
            texto_victoria = fuente_grande.render("¡Resuelto!", True, COLOR_GANASTE)
            pantalla.blit(texto_victoria, texto_victoria.get_rect(
                center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2 - 20)))
            if uso_asistente:
                detalle = f"Resuelto en {movimientos_totales} movimientos (con ayuda del asistente)"
            else:
                detalle = f"Resuelto en {movimientos_totales} movimientos"
            sub = fuente.render(detalle, True, COLOR_TEXTO)
            pantalla.blit(sub, sub.get_rect(center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2 + 25)))
            sub2 = fuente.render("Clic en Barajar o Menú para seguir", True, COLOR_TEXTO)
            pantalla.blit(sub2, sub2.get_rect(center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2 + 55)))

        pygame.display.flip()
        reloj.tick(FPS)


def main():
    pygame.init()
    pygame.display.set_caption("Puzzle-N — Proyecto IA")
    # Único lugar de todo el programa donde se fija el tamaño de
    # ventana -- nunca se vuelve a tocar. Esto es lo que elimina el
    # bug de clicks desalineados de raíz.
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    fuente_grande = pygame.font.SysFont("arial", 40, bold=True)
    fuente = pygame.font.SysFont("arial", 22)

    while True:
        n, longitud_caminata = pantalla_menu(pantalla, fuente_grande, fuente)
        jugar(pantalla, fuente_grande, fuente, n, longitud_caminata)


if __name__ == "__main__":
    main()