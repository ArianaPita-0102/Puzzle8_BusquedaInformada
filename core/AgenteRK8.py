from AgenteIA.AgenteBuscador import AgenteBuscador
from copy import deepcopy
from collections import deque


class AgenteRK8(AgenteBuscador):

    HEURISTICAS_DISPONIBLES = ("h1", "h2", "h3", "h4", "h5", "h6")

    def __init__(self, heuristica="h2", w=0.5):
        AgenteBuscador.__init__(self)
        self.add_funcion(self.arriba)
        self.add_funcion(self.abajo)
        self.add_funcion(self.izquierda)
        self.add_funcion(self.derecha)

        self.set_heuristica(heuristica)
        self.w = w

        self._pdb = None

    def set_heuristica(self, nombre):
        if nombre not in self.HEURISTICAS_DISPONIBLES:
            raise ValueError(
                f"Heurística '{nombre}' no reconocida. "
                f"Usa una de {self.HEURISTICAS_DISPONIBLES}"
            )
        self.__heuristica = nombre

    def get_heuristica_activa(self):
        return self.__heuristica

    def get_costo(self, tup):
        return len(tup)

    def pos(self, e):
        for i in range(3):
            for j in range(3):
                if e[i][j] == 0:
                    return (i, j)

    def arriba(self, e):
        t = self.pos(e)
        if t[0] != 0:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0] - 1][t[1]]
            aux[t[0] - 1][t[1]] = 0
            return aux
        else:
            return None

    def abajo(self, e):
        t = self.pos(e)
        if t[0] != 2:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0] + 1][t[1]]
            aux[t[0] + 1][t[1]] = 0
            return aux
        else:
            return None

    def derecha(self, e):
        t = self.pos(e)
        if t[1] != 2:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0]][t[1] + 1]
            aux[t[0]][t[1] + 1] = 0
            return aux
        else:
            return None

    def izquierda(self, e):
        t = self.pos(e)
        if t[1] != 0:
            aux = deepcopy(e)
            aux[t[0]][t[1]] = aux[t[0]][t[1] - 1]
            aux[t[0]][t[1] - 1] = 0
            return aux
        else:
            return None

    def _posiciones_meta(self):
        meta = self.get_estado_meta()
        posiciones = {}
        for x in range(3):
            for y in range(3):
                posiciones[meta[x][y]] = (x, y)
        return posiciones

    def get_heuristica(self, camino):
        estado = camino[-1]
        metodo = getattr(self, self.__heuristica)
        return metodo(estado)

    def h1(self, estado):
        meta = self.get_estado_meta()
        mal_colocadas = 0
        for i in range(3):
            for j in range(3):
                valor = estado[i][j]
                if valor != 0 and valor != meta[i][j]:
                    mal_colocadas += 1
        return mal_colocadas

    def h2(self, estado):
        posiciones_meta = self._posiciones_meta()
        distancia = 0
        for i in range(3):
            for j in range(3):
                valor = estado[i][j]
                if valor != 0:
                    x, y = posiciones_meta[valor]
                    distancia += abs(i - x) + abs(j - y)
        return distancia

    def h3(self, estado):
        return self.h2(estado) + 2 * self._conflicto_lineal(estado)

    def _conflicto_lineal(self, estado):
        posiciones_meta = self._posiciones_meta()
        conflictos = 0

        for i in range(3):
            elementos = []
            for j in range(3):
                valor = estado[i][j]
                if valor != 0:
                    x_meta, y_meta = posiciones_meta[valor]
                    if x_meta == i:
                        elementos.append((j, y_meta))
            conflictos += self._contar_conflictos_en_linea(elementos)

        for j in range(3):
            elementos = []
            for i in range(3):
                valor = estado[i][j]
                if valor != 0:
                    x_meta, y_meta = posiciones_meta[valor]
                    if y_meta == j:
                        elementos.append((i, x_meta))
            conflictos += self._contar_conflictos_en_linea(elementos)

        return conflictos

    def _contar_conflictos_en_linea(self, elementos):
        n = len(elementos)
        vecinos = [set() for _ in range(n)]
        for a in range(n):
            for b in range(a + 1, n):
                pos_a, meta_a = elementos[a]
                pos_b, meta_b = elementos[b]
                if (pos_a < pos_b) != (meta_a < meta_b):
                    vecinos[a].add(b)
                    vecinos[b].add(a)

        activos = set(range(n))
        removidos = 0
        while True:
            candidato, max_grado = None, 0
            for v in activos:
                grado = len(vecinos[v] & activos)
                if grado > max_grado:
                    candidato, max_grado = v, grado
            if max_grado == 0:
                break
            activos.discard(candidato)
            removidos += 1
        return removidos

    def h4(self, estado):
        return self.h3(estado) + self._penalizacion_esquinas(estado)

    def _penalizacion_esquinas(self, estado):
        posiciones_meta = self._posiciones_meta()
        esquinas_con_ficha = [(0, 0), (0, 2), (2, 0)]
        opuesta = {(0, 0): (2, 2), (0, 2): (2, 0), (2, 0): (0, 2)}
        blanco = self.pos(estado)
        penalizacion = 0
        for (i, j) in esquinas_con_ficha:
            valor = estado[i][j]
            if valor == 0:
                continue
            meta_pos = posiciones_meta[valor]
            if meta_pos in esquinas_con_ficha and meta_pos != (i, j):
                if blanco != opuesta[(i, j)]:
                    penalizacion += 1
        return penalizacion

    def h5(self, estado):
        if self._pdb is None:
            self._pdb = {
                (1, 2, 3, 4): self._construir_pdb((1, 2, 3, 4)),
                (5, 6, 7, 8): self._construir_pdb((5, 6, 7, 8)),
            }
        total = 0
        for grupo, tabla in self._pdb.items():
            total += tabla[self._abstraer(estado, grupo)]
        return total

    def _abstraer(self, estado, grupo):
        plano = [estado[i][j] for i in range(3) for j in range(3)]
        return tuple(v if (v == 0 or v in grupo) else -1 for v in plano)

    def _construir_pdb(self, grupo):
        meta_abs = self._abstraer(self.get_estado_meta(), grupo)
        dist = {meta_abs: 0}
        dq = deque([meta_abs])
        while dq:
            actual = dq.popleft()
            d = dist[actual]
            idx0 = actual.index(0)
            fila, col = divmod(idx0, 3)
            for df, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nf, nc = fila + df, col + dc
                if 0 <= nf < 3 and 0 <= nc < 3:
                    nidx = nf * 3 + nc
                    costo = 1 if actual[nidx] != -1 else 0
                    nuevo = list(actual)
                    nuevo[idx0], nuevo[nidx] = nuevo[nidx], nuevo[idx0]
                    nuevo = tuple(nuevo)
                    nd = d + costo
                    if nuevo not in dist or nd < dist[nuevo]:
                        dist[nuevo] = nd
                        if costo == 0:
                            dq.appendleft(nuevo)
                        else:
                            dq.append(nuevo)
        return dist

    def h6(self, estado):
        return self.w * self.h2(estado) + (1 - self.w) * self.h1(estado)

    def set_w(self, w):
        self.w = w