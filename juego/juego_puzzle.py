import os
import random
import sys
import time

_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ_PROYECTO = os.path.dirname(_AQUI)
if _RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, _RAIZ_PROYECTO)

import pygame

if sys.platform == "win32":
    os.environ["SDL_WINDOWS_DPI_AWARENESS"] = "permonitorv2"

from busqueda.rkn_informado import RKNInformado
from experimentos.generar_instancias_n import estado_meta

TAMANO_FICHA = 100
ALTO_HEADER = 150
FPS = 60

ANCHO_VENTANA = 650
ALTO_VENTANA = ALTO_HEADER + TAMANO_FICHA * 5 + 90

DIFICULTADES = [
    ("Fácil (3x3)", 3, 25),
    ("Medio (4x4)", 4, 30),
    ("Difícil (5x5)", 5, 30),
]

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
    agente = RKNInformado(n=n, heuristica="h2")
    agente.set_estado_meta(meta)
    agente.set_estado_inicial(estado_actual)
    agente.set_tecnica("a_estrella")
    agente.set_limites(nodos=LIMITE_NODOS_ASISTENTE, tiempo_s=LIMITE_TIEMPO_ASISTENTE_S)
    agente.programa()
    pasos = agente.get_acciones()
    motivo_timeout = agente.get_medida_rendimiento().get("timeout")
    return pasos, motivo_timeout


def pos_blanco(estado):
    n = len(estado)
    for i in range(n):
        for j in range(n):
            if estado[i][j] == 0:
                return i, j


def mover_si_valido(estado, fila_click, col_click):
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
    ancho_tablero = TAMANO_FICHA * n
    offset_x = (ANCHO_VENTANA - ancho_tablero) // 2

    meta = estado_meta(n)
    rng = random.Random()
    estado = generar_tablero_barajado(n, longitud_caminata, rng)

    movimientos_totales = 0
    uso_asistente = False
    tiempo_inicio = time.time()
    tiempo_final = None
    ganado = False

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
                    movimientos_totales += 1

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
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    fuente_grande = pygame.font.SysFont("arial", 40, bold=True)
    fuente = pygame.font.SysFont("arial", 22)

    while True:
        n, longitud_caminata = pantalla_menu(pantalla, fuente_grande, fuente)
        jugar(pantalla, fuente_grande, fuente, n, longitud_caminata)


if __name__ == "__main__":
    main()