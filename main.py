# -*- coding: utf-8 -*-
"""
Protocolo Cronos: O Bunker Submerso
Escape Room 2D Top-Down de Análise Combinatória (Pygame).

Gráficos e áudio 100% procedurais: nenhum arquivo externo é necessário.
Banco de questões: questoes.py  (BANCO_QUESTOES)

Estrutura do código (POO):
    Som ............. síntese de efeitos e trilha de sonar em memória
    Baralho ......... sorteio sem repetição das questões de uma fase
    Terminal ........ console interativo (pendente = vermelho, concluído = verde)
    Porta ........... porta hidráulica animada da sala
    Fase ............ mapa, colisões, renderização estática do cenário
    Jogador ......... movimento, animação e colisão
    Iluminacao ...... camada de escuridão + lanterna
    BlocoNotas ...... rascunho com mini-calculadora (fatorial incluso)
    Desafio ......... interface do terminal (pergunta, feedback, resolução)
    Jogo ............ máquina de estados, HUD e laço principal
"""

import array
import asyncio
import math
import random
import sys
import time
from fractions import Fraction

import pygame

from questoes import BANCO_QUESTOES

# ----------------------------------------------------------------------------
# CONSTANTES
# ----------------------------------------------------------------------------
LARGURA, ALTURA = 1024, 640
HUD_H = 64                      # altura da barra superior
TILE = 32
COLS, ROWS = 32, 18             # 32*32 = 1024 ; 18*32 = 576 ; 576 + 64 = 640
FPS = 60

TEMPO_TOTAL = 12 * 60           # tempo limite global (segundos)
MAX_ERROS = 5                   # falhas críticas permitidas
PENALIDADE_ERRO = 20            # segundos descontados a cada erro
VEL_JOGADOR = 175               # pixels por segundo
TOTAL_ACERTOS = 12
EH_WEB = sys.platform == "emscripten"   # rodando no navegador (pygbag / WebAssembly)

# Buffer de áudio maior = som sem "picotar" quando um quadro demora. No navegador o áudio roda na
# mesma thread do jogo, então precisa de mais folga (4096 amostras ≈ 0,19 s a 22 kHz; 2048 ≈ 46 ms no PC).
BUFFER_AUDIO = 4096 if EH_WEB else 2048
# No PC usamos 44,1 kHz (taxa nativa das placas de som; evita reamostragem com estalos).
# No navegador fica em 22 kHz: metade do trabalho para gerar os sons em WebAssembly.
FREQ_AUDIO = 22050 if EH_WEB else 44100
if EH_WEB:
    FPS = 30      # no navegador/celular: menos quadros por segundo, mais folga para o áudio

# Em telas mais largas que 16:10 (celular deitado) o jogo 1024x640 fica centralizado e as
# faixas laterais recebem os controles de toque. DESLOCAMENTO_X = largura de cada faixa.
DESLOCAMENTO_X = 0


def mouse_jogo():
    """Posição do mouse em coordenadas do jogo (descontando a faixa lateral)."""
    x, y = pygame.mouse.get_pos()
    return x - DESLOCAMENTO_X, y

# Estados do jogo
MENU, INTRO, JOGANDO, ESCOLHA_FINAL, VITORIA, DERROTA, CINEMA = range(7)

# Cores
BRANCO = (235, 240, 245)
CINZA = (140, 155, 170)
CIANO = (70, 220, 235)
VERDE = (70, 235, 130)
VERMELHO = (245, 70, 60)
AMARELO = (250, 200, 60)
FUNDO = (6, 12, 20)

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO DAS FASES E MAPAS
# ----------------------------------------------------------------------------
FASES = [
    {"nome": "Câmara de Eclusa", "nivel": "Fácil", "meta": 1,
     "conteudo": "Princípio Fundamental da Contagem",
     "historia": "Você acorda na Eclusa de Descompressão da Estação Acheron-4. As luzes de emergência piscam. "
                 "A porta hidráulica só cede se o Painel de Fusíveis for religado."},
    {"nome": "Laboratório Genético", "nivel": "Básico", "meta": 2,
     "conteudo": "Permutação Simples e com Repetição",
     "historia": "Aqui o organismo abissal foi estudado. A equipe anterior trancou o setor com "
                 "sequências de DNA embaralhadas: reordene-as para prosseguir."},
    {"nome": "Central de Sonar", "nivel": "Intermediário", "meta": 2,
     "conteudo": "Arranjo Simples",
     "historia": "Algo enorme se move no escuro lá fora. O radar e o console de pressão só liberam "
                 "a passagem para quem dominar a ordem dos sinais."},
    {"nome": "Câmara do Reator", "nivel": "Avançado", "meta": 3,
     "conteudo": "Combinação Simples",
     "historia": "O núcleo do reator ruge. Três válvulas precisam ser acionadas, mas aqui a ordem "
                 "não importa: apenas quais grupos você escolhe."},
    {"nome": "Sala da Cápsula", "nivel": "Difícil", "meta": 4,
     "conteudo": "Restrições e Integração de Conceitos",
     "historia": "A última barreira. A cápsula de fuga espera do outro lado, mas o protocolo final "
                 "combina TUDO o que você aprendeu. Não há margem para erro."},
]

# solidos: (caractere, coluna, linha, largura, altura) em tiles.
#   '#' parede   'M' mesa   'B' tanque   'K' caixote   'R' núcleo do reator
# terminais: (nome, coluna, linha) — cada terminal ocupa 2x1 tiles.
# porta: linha superior da porta (ocupa 2 tiles) na parede direita.
MAPAS = [
    {   # Fase 1
        "inicio": (2, 8), "porta": 8,
        "solidos": [("M", 5, 2, 4, 2), ("M", 5, 13, 4, 2), ("B", 12, 2, 1, 1), ("B", 14, 2, 1, 1),
                    ("K", 24, 3, 2, 2), ("K", 22, 13, 2, 2), ("B", 28, 14, 1, 1), ("M", 17, 12, 3, 2)],
        "terminais": [("Painel de Fusíveis", 14, 7)],
    },
    {   # Fase 2
        "inicio": (2, 8), "porta": 8,
        "solidos": [("#", 15, 1, 1, 6), ("#", 15, 11, 1, 6),
                    ("M", 3, 2, 4, 2), ("M", 3, 13, 4, 2), ("M", 20, 2, 5, 2), ("M", 20, 13, 5, 2),
                    ("B", 10, 4, 1, 1), ("B", 10, 13, 1, 1), ("B", 27, 8, 2, 2)],
        "terminais": [("Sequenciador Genético", 6, 8), ("Válvula de Contenção", 22, 8)],
    },
    {   # Fase 3
        "inicio": (2, 9), "porta": 12,
        "solidos": [("#", 8, 1, 1, 8), ("#", 8, 12, 1, 5), ("#", 20, 1, 1, 10),
                    ("M", 11, 2, 4, 2), ("M", 11, 13, 4, 2), ("K", 3, 3, 2, 2), ("K", 3, 13, 2, 2),
                    ("B", 17, 6, 1, 1), ("M", 24, 3, 4, 2)],
        "terminais": [("Radar de Sonar", 11, 8), ("Console de Pressão", 25, 9)],
    },
    {   # Fase 4
        "inicio": (2, 9), "porta": 8,
        "solidos": [("R", 13, 6, 5, 4), ("#", 24, 1, 1, 5), ("#", 24, 12, 1, 5),
                    ("K", 3, 3, 2, 2), ("K", 3, 13, 2, 2), ("M", 19, 13, 4, 2),
                    ("B", 20, 3, 1, 1), ("B", 22, 3, 1, 1)],
        "terminais": [("Válvula do Reator A", 8, 3), ("Válvula do Reator B", 11, 13),
                      ("Válvula do Reator C", 26, 5)],
    },
    {   # Fase 5
        "inicio": (2, 8), "porta": 8,
        "solidos": [("B", 10, 3, 1, 1), ("B", 10, 14, 1, 1), ("M", 17, 3, 4, 2), ("M", 17, 13, 4, 2),
                    ("K", 28, 3, 2, 2), ("K", 28, 13, 2, 2), ("K", 6, 8, 2, 2)],
        "terminais": [("Núcleo de Energia", 4, 3), ("Console da Cápsula", 4, 13),
                      ("Painel de Contenção", 14, 8), ("Computador Central", 24, 8)],
    },
]

# piso, piso2 (detalhe), parede, parede_luz, destaque
PALETAS = [
    ((52, 62, 74), (44, 53, 64), (28, 36, 48), (62, 78, 96), (80, 150, 190)),
    ((46, 66, 66), (38, 56, 56), (22, 42, 42), (50, 90, 88), (80, 210, 170)),
    ((38, 50, 82), (32, 43, 72), (20, 28, 56), (50, 70, 118), (90, 140, 250)),
    ((74, 58, 48), (64, 50, 42), (46, 30, 26), (100, 66, 52), (255, 150, 60)),
    ((66, 44, 56), (56, 38, 48), (40, 22, 34), (92, 50, 70), (255, 80, 110)),
]

TEXTO_HISTORIA = (
    "Ano 2089. A Estação Submarina ACHERON-4, a 3.000 metros de profundidade, sofreu um colapso estrutural. "
    "Você é o único sobrevivente e acorda em meio ao alarme.\n"
    "Antes de morrer, a equipe anterior trancou cada setor com PROTOCOLOS CRIPTOGRÁFICOS baseados em "
    "Análise Combinatória para conter um organismo abissal. Resolva os desafios dos terminais, abra as "
    "portas hidráulicas e chegue à cápsula de fuga antes que o oxigênio, ou a paciência do organismo, acabe."
)

FINAIS = {
    "fugir": ("FINAL A: ASCENSÃO",
              "Você sela a escotilha e dispara a cápsula Cronos. Acheron-4 some nas trevas enquanto você sobe, "
              "levando os dados dos protocolos. O organismo permanece contido pelas travas que você destravou "
              "com Matemática. Você sobreviveu."),
    "sobrecarregar": ("FINAL B: PULSO CRONOS",
                      "Você redireciona toda a energia ao núcleo. O reator sobrecarrega e o pulso eletromagnético "
                      "aniquila o organismo e as portas que o prendiam. Na última contagem regressiva, a cápsula "
                      "escapa. Acheron-4 deixa de existir, e a ameaça também."),
}

# Legendas da cinemática final (uma a cada ~3,9 s)
LEGENDAS_FINAL = {
    "fugir": [
        "A escotilha se fecha. A cápsula Cronos se desprende da estação e começa a subir.",
        "Lá embaixo, as luzes de Acheron-4 se apagam uma a uma...",
        "...mas algo ainda observa da escuridão. As travas que você quebrou com Matemática agora o mantêm preso.",
        "3.000 metros acima, a luz do sol atravessa a água. Você chegou à superfície.",
    ],
    "sobrecarregar": [
        "Toda a energia flui para o núcleo. O reator começa a gritar.",
        "A cápsula dispara no exato instante em que o Pulso Cronos se forma.",
        "Uma onda de luz varre o abismo. O organismo e a estação deixam de existir.",
        "Na superfície, o mar se acalma. A ameaça acabou, e você sobreviveu.",
    ],
}

# Epílogo exibido na tela de vitória, depois da cinemática
EPILOGOS = {
    "fugir": "Os dados dos protocolos chegam à superfície. A Acheron-4 vira zona proibida, e o organismo "
             "continua lá embaixo, preso pelas mesmas contas que você resolveu.",
    "sobrecarregar": "Nenhum vestígio do organismo é encontrado. O seu relatório vira material de estudo: "
                     "contar possibilidades foi o que salvou a missão.",
}

CINEMA_TOTAL = 16.0       # duração da cinemática de vitória (segundos)


# ----------------------------------------------------------------------------
# UTILITÁRIOS DE TEXTO
# ----------------------------------------------------------------------------
# Caches: o mesmo texto/painel é desenhado em todo quadro; renderizar uma vez só alivia muito a CPU
# (no navegador isso evita que o áudio fique sem dados e "picote").
_CACHE_TEXTO = {}
_CACHE_QUEBRA = {}
_CACHE_PAINEL = {}


def _cache_limitado(cache, limite=800):
    if len(cache) > limite:
        cache.clear()
    return cache


def render_texto(texto, fonte, cor):
    """fonte.render com cache."""
    chave = (texto, id(fonte), cor)
    img = _CACHE_TEXTO.get(chave)
    if img is None:
        img = _cache_limitado(_CACHE_TEXTO)[chave] = fonte.render(texto, True, cor)
    return img


def quebrar_texto(texto, fonte, largura):
    """Quebra automática de linha (word wrap) respeitando '\\n' (com cache)."""
    chave = (texto, id(fonte), largura)
    if chave in _CACHE_QUEBRA:
        return _CACHE_QUEBRA[chave]
    _cache_limitado(_CACHE_QUEBRA, 300)[chave] = linhas = _quebrar(texto, fonte, largura)
    return linhas


def _quebrar(texto, fonte, largura):
    linhas = []
    for paragrafo in texto.split("\n"):
        atual = ""
        for palavra in paragrafo.split(" "):
            teste = palavra if not atual else atual + " " + palavra
            if fonte.size(teste)[0] <= largura:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                atual = palavra
        linhas.append(atual)
    return linhas


def desenhar_texto(surf, texto, fonte, cor, pos, centro=False, sombra=True):
    img = render_texto(texto, fonte, cor)
    r = img.get_rect()
    if centro:
        r.midtop = pos
    else:
        r.topleft = pos
    if sombra:
        surf.blit(render_texto(texto, fonte, (0, 0, 0)), r.move(1, 2))
    surf.blit(img, r)
    return r


def desenhar_paragrafo(surf, texto, fonte, cor, x, y, largura, espaco=4, centro=False):
    """Desenha texto com word wrap; devolve o y logo abaixo do bloco."""
    for linha in quebrar_texto(texto, fonte, largura):
        if centro:
            desenhar_texto(surf, linha, fonte, cor, (x + largura // 2, y), centro=True)
        else:
            desenhar_texto(surf, linha, fonte, cor, (x, y))
        y += fonte.get_linesize() + espaco
    return y


def painel(surf, rect, cor=(10, 20, 32), borda=CIANO, alfa=235, raio=12):
    chave = (rect.size, cor, borda, alfa, raio)
    s = _CACHE_PAINEL.get(chave)
    if s is None:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*cor, alfa), s.get_rect(), border_radius=raio)
        pygame.draw.rect(s, (*borda, 255), s.get_rect(), 2, border_radius=raio)
        _cache_limitado(_CACHE_PAINEL, 120)[chave] = s
    surf.blit(s, rect.topleft)


# ----------------------------------------------------------------------------
# CALCULADORA SEGURA DO BLOCO DE NOTAS (aritmética com fatorial)
# ----------------------------------------------------------------------------
class _Analisador:
    def __init__(self, texto):
        self.t, self.i = texto, 0

    def olhar(self):
        return self.t[self.i] if self.i < len(self.t) else ""

    def expr(self):
        v = self.termo()
        while self.olhar() in ("+", "-"):
            op = self.t[self.i]
            self.i += 1
            w = self.termo()
            v = v + w if op == "+" else v - w
        return v

    def termo(self):
        v = self.potencia()
        while self.olhar() in ("*", "/"):
            op = self.t[self.i]
            self.i += 1
            w = self.potencia()
            v = v * w if op == "*" else v / w
        return v

    def potencia(self):
        b = self.unario()
        if self.olhar() == "^":
            self.i += 1
            e = self.potencia()
            if e.denominator != 1 or abs(e) > 100:
                raise ValueError
            return b ** int(e)
        return b

    def unario(self):
        if self.olhar() == "-":
            self.i += 1
            return -self.unario()
        return self.pos_fixo()

    def pos_fixo(self):
        v = self.atomo()
        while self.olhar() == "!":
            self.i += 1
            if v.denominator != 1 or v < 0 or v > 60:
                raise ValueError
            v = Fraction(math.factorial(int(v)))
        return v

    def atomo(self):
        if self.olhar() == "(":
            self.i += 1
            v = self.expr()
            if self.olhar() != ")":
                raise ValueError
            self.i += 1
            return v
        ini = self.i
        while self.olhar() in tuple("0123456789."):
            self.i += 1
        if ini == self.i:
            raise ValueError
        return Fraction(self.t[ini:self.i])


def avaliar_expressao(texto):
    """Avalia uma expressão e devolve string (ou None se inválida)."""
    t = (texto.replace(" ", "").replace("×", "*").replace("x", "*").replace("X", "*")
         .replace("÷", "/").replace(",", ".").replace("·", "*"))
    if "=" in t:
        t = t.split("=")[0]
    if not t:
        return None
    try:
        p = _Analisador(t)
        v = p.expr()
        if p.i != len(t):
            return None
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    if v.denominator == 1:
        n = int(v)
        return str(n) if abs(n) < 10 ** 15 else f"{float(n):.4e}"
    return f"{float(v):.4f}".rstrip("0")


# ----------------------------------------------------------------------------
# ÁUDIO PROCEDURAL
# ----------------------------------------------------------------------------
class Som:
    """Gera todos os sons em memória (sem arquivos). Falha de forma silenciosa.

    A síntese é feita aos poucos (alguns milissegundos por quadro, via `preparar`),
    para o jogo abrir instantaneamente, inclusive no navegador/celular.
    """
    SR = FREQ_AUDIO
    VOL_MUSICA = 0.32

    def __init__(self):
        self.ativo = False
        self.mudo = False
        self.volume = 0.7            # volume geral escolhido no controle deslizante (0 a 1)
        self.sons = {}
        self.canais = 1
        self._gerador = None
        self._musica_tocando = False
        try:
            pygame.mixer.init(frequency=self.SR, size=-16, channels=1, buffer=BUFFER_AUDIO)
            ini = pygame.mixer.get_init()
            self.SR, self.canais = ini[0], ini[2]   # usa a taxa que o dispositivo aceitou
            self._gerador = self._gerar()
            self.ativo = True
        except Exception:
            self.ativo = False

    def preparar(self, orcamento_ms=6):
        """Avança a síntese pendente sem estourar o tempo de um quadro."""
        if not self._gerador:
            return
        limite = time.perf_counter() + orcamento_ms / 1000
        try:
            while time.perf_counter() < limite:
                next(self._gerador)
        except StopIteration:
            self._gerador = None
        except Exception:
            self._gerador = None
        if "sonar" in self.sons and not self._musica_tocando:
            self._iniciar_musica()

    def alternar_mudo(self):
        self.mudo = not self.mudo
        if self.ativo:
            try:
                if self.mudo:
                    pygame.mixer.stop()          # corta efeitos que estejam tocando
                    self._musica_tocando = False
                elif "sonar" in self.sons:
                    self._iniciar_musica()
            except Exception:
                pass
        return self.mudo

    def definir_volume(self, v):
        """Ajusta o volume geral (0 a 1) e aplica na música que já está tocando."""
        self.volume = max(0.0, min(1.0, v))
        if self.ativo and "sonar" in self.sons:
            try:
                self.sons["sonar"].set_volume(self.VOL_MUSICA * self.volume)
            except Exception:
                pass

    # --- geração ---
    GANHO = 0.42     # volume geral: deixa folga para música + efeitos somados não distorcerem
    PEDACO = 1500    # amostras sintetizadas por vez antes de devolver o controle ao jogo

    # Todas as funções de síntese são geradores: fazem um pedaço, dão `yield` (o jogo desenha
    # um quadro) e continuam depois. O resultado vem pelo `return` (usado com `yield from`).

    def _criar(self, amostras):
        # normaliza só se passar de 1.0 e aplica o ganho geral, depois converte para int16
        k = 32000 * self.GANHO / max(1.0, max(map(abs, amostras)))
        dados = array.array("h")
        p = self.PEDACO * 4
        for i in range(0, len(amostras), p):
            bloco = [int(a * k) for a in amostras[i:i + p]]
            if self.canais == 2:
                bloco = [v for v in bloco for _ in (0, 1)]
            dados.extend(bloco)
            yield
        return pygame.mixer.Sound(buffer=dados.tobytes())

    def _tom(self, f0, dur, vol=0.4, forma="sin", f1=None, decaimento=1.5):
        n = int(self.SR * dur)
        fase = 0.0
        out = []
        sin, tau, sr = math.sin, 2 * math.pi, self.SR
        f1 = f1 if f1 else f0
        for i in range(n):
            t = i / sr
            fase += tau * (f0 + (f1 - f0) * t / dur) / sr
            if forma == "sin":
                s = sin(fase)
            elif forma == "suave":       # timbre "metálico" sem a aspereza da onda serra
                s = sin(fase) * 0.8 + sin(fase * 2) * 0.25 + sin(fase * 3) * 0.12
            elif forma == "serra":
                s = 2 * ((fase / tau) % 1.0) - 1
            else:
                s = 1.0 if sin(fase) >= 0 else -1.0
            ataque = min(1.0, t / 0.008)                 # ataque suave evita "clique" no início
            out.append(s * vol * ataque * (1 - t / dur) ** decaimento)
            if i % self.PEDACO == 0:
                yield
        return out

    def _ruido(self, dur, vol=0.3, suav=0.5, decaimento=3.0):
        n = int(self.SR * dur)
        out, ant = [], 0.0
        for i in range(n):
            ant = ant * suav + random.uniform(-1, 1) * (1 - suav)
            out.append(ant * vol * (1 - i / n) ** decaimento)
            if i % self.PEDACO == 0:
                yield
        return out

    def _somar(self, *listas):
        n = max(len(l) for l in listas)
        out = [0.0] * n
        for l in listas:
            for i, v in enumerate(l):
                out[i] += v
                if i % (self.PEDACO * 4) == 0:
                    yield
        return out

    def _gerar(self):
        """Gera todos os sons aos poucos (efeitos primeiro, música, e por fim os sons do final)."""
        tom, ruido, somar, criar = self._tom, self._ruido, self._somar, self._criar
        self.sons["bipe"] = yield from criar((yield from tom(880, 0.09, 0.5, "sin", decaimento=1.2)))
        self.sons["passo"] = yield from criar((yield from ruido(0.07, 0.6, 0.9, 4.0)))
        acerto = []
        for f, d in ((523, 0.11), (659, 0.11), (784, 0.11)):
            acerto += yield from tom(f, d, 0.6)
        acerto += yield from tom(1047, 0.30, 0.6, decaimento=2.0)
        self.sons["acerto"] = yield from criar(acerto)
        alarme = []
        for k in range(4):
            alarme += yield from tom(330 if k % 2 == 0 else 247, 0.16, 0.7, "suave", decaimento=0.8)
        self.sons["erro"] = yield from criar(alarme)
        fase = (yield from tom(220, 0.5, 0.6, f1=440)) + (yield from tom(440, 0.4, 0.6, f1=660))
        self.sons["fase"] = yield from criar(fase)
        ronco = yield from tom(90, 1.4, 0.6, "sin", f1=38, decaimento=0.8)
        chiado = yield from ruido(1.4, 0.2, 0.93, 1.2)
        trava = [0.0] * 200 + (yield from tom(260, 0.12, 0.35, "suave", f1=120))
        self.sons["porta"] = yield from criar((yield from somar(ronco, chiado, trava)))
        self.sons["derrota"] = yield from criar((yield from tom(220, 1.2, 0.7, "suave", f1=55, decaimento=0.7)))
        vit = []
        for f, d in ((392, 0.15), (523, 0.15), (659, 0.15)):
            vit += yield from tom(f, d, 0.6)
        vit += yield from tom(784, 0.5, 0.6, decaimento=1.2)
        self.sons["vitoria"] = yield from criar(vit)
        # Música de fundo: drone de sonar em loop (4 s = ciclos inteiros de 55 Hz, 82,5 Hz e 0,5 Hz).
        # O pulso (ping + batida grave) é somado nos instantes 0 s e 2 s.
        sr, sin, tau, exp = self.SR, math.sin, 2 * math.pi, math.exp
        n = sr * 4
        meio = n // 2
        pulso = []
        for i in range(meio):
            d = i / sr
            pulso.append(sin(tau * 900 * d) * 0.10 * exp(-d * 3.2) + sin(tau * 48 * d) * 0.30 * exp(-d * 6.0))
            if i % self.PEDACO == 0:
                yield
        sonar = []
        for i in range(n):
            t = i / sr
            s = (sin(tau * 55 * t) * 0.30 + sin(tau * 82.5 * t) * 0.14) * (0.75 + 0.25 * sin(tau * 0.5 * t))
            sonar.append(s + pulso[i % meio])
            if i % self.PEDACO == 0:
                yield
        self.sons["sonar"] = yield from criar(sonar)
        # Sons do final (gerados por último: só são usados no fim da partida)
        estrondo = yield from tom(70, 2.2, 0.8, "sin", f1=25, decaimento=1.4)
        ruido_exp = yield from ruido(2.2, 0.55, 0.97, 2.0)
        self.sons["explosao"] = yield from criar((yield from somar(estrondo, ruido_exp)))
        notas = [(523, .18), (659, .18), (784, .18), (1047, .36), (988, .18), (784, .18), (880, .45), (1047, .9)]
        melodia = []
        for f, d in notas:
            melodia += yield from tom(f, d, 0.55, "suave", decaimento=0.9)
        base = yield from tom(131, len(melodia) / sr, 0.35, "sin", decaimento=0.6)
        self.sons["tema"] = yield from criar((yield from somar(melodia, base)))

    # --- uso ---
    def tocar(self, nome, volume=0.55):
        if self.ativo and not self.mudo and self.volume > 0 and nome in self.sons:
            try:
                self.sons[nome].set_volume(volume * self.volume)
                self.sons[nome].play()
            except Exception:
                pass

    def _iniciar_musica(self):
        if self.mudo or not self.ativo:
            return
        try:
            self.sons["sonar"].set_volume(self.VOL_MUSICA * self.volume)
            self.sons["sonar"].play(loops=-1)
            self._musica_tocando = True
        except Exception:
            self._musica_tocando = True   # não tenta de novo a cada quadro


# ----------------------------------------------------------------------------
# QUESTÕES
# ----------------------------------------------------------------------------
class Baralho:
    """Sorteio aleatório SEM repetição das questões de uma fase."""

    def __init__(self, numero_fase):
        self.numero = numero_fase
        self.restantes = []
        self._reabastecer()

    def _reabastecer(self, excluir=()):
        self.restantes = [q for q in BANCO_QUESTOES[self.numero] if q["id"] not in excluir]
        random.shuffle(self.restantes)

    def sortear(self, em_uso=()):
        if not self.restantes:          # só ocorre se as 10 inéditas acabarem
            self._reabastecer(em_uso)
        return self.restantes.pop()


# ----------------------------------------------------------------------------
# OBJETOS DO CENÁRIO
# ----------------------------------------------------------------------------
class Terminal:
    _brilhos = {}   # cache das auréolas (criadas uma única vez)

    @classmethod
    def brilho(cls, cor):
        if cor not in cls._brilhos:
            s = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(s, (*cor, 90), (18, 18), 17)
            pygame.draw.circle(s, (*cor, 150), (18, 18), 10)
            cls._brilhos[cor] = s
        return cls._brilhos[cor]

    def __init__(self, nome, col, lin):
        self.nome = nome
        self.rect = pygame.Rect(col * TILE, lin * TILE, TILE * 2, TILE)
        self.feita = False
        self.questao = None

    def desenhar(self, surf, t):
        r = self.rect
        pygame.draw.rect(surf, (0, 0, 0), r.move(2, 3), border_radius=5)
        pygame.draw.rect(surf, (26, 32, 42), r, border_radius=5)
        pygame.draw.rect(surf, (88, 100, 118), r, 2, border_radius=5)
        tela = r.inflate(-14, -12)
        pygame.draw.rect(surf, (14, 70, 36) if self.feita else (14, 52, 66), tela, border_radius=3)
        cor_linha = (90, 240, 140) if self.feita else (80, 200, 225)
        for i in range(3):
            larg = tela.width - 6 - (i * 9 % 14)
            pygame.draw.line(surf, cor_linha, (tela.x + 3, tela.y + 3 + i * 4), (tela.x + 3 + larg, tela.y + 3 + i * 4), 1)
        pulso = 0.55 + 0.45 * math.sin(t * 4.5 + r.x)
        cor = (70, 255, 120) if self.feita else (255, 60, 50)
        luz = self.brilho(cor)
        luz.set_alpha(int(255 * pulso))
        surf.blit(luz, (r.right - 20, r.y - 12))
        pygame.draw.circle(surf, cor, (r.right - 2, r.y + 6), 4)
        pygame.draw.circle(surf, (255, 255, 255), (r.right - 3, r.y + 5), 1)


class Porta:
    """Porta hidráulica de duas folhas que se abre quando a meta da fase é atingida."""

    def __init__(self, linha):
        self.rect = pygame.Rect(COLS * TILE - TILE, linha * TILE, TILE, TILE * 2)
        self.aberta = False
        self.prog = 0.0

    def abrir(self):
        self.aberta = True

    def atualizar(self, dt):
        if self.aberta:
            self.prog = min(1.0, self.prog + dt / 1.2)

    @property
    def solida(self):
        return not (self.aberta and self.prog > 0.55)

    @property
    def passavel(self):
        return self.aberta and self.prog >= 0.55

    def desenhar(self, surf, t):
        r = self.rect
        pygame.draw.rect(surf, (8, 10, 14), r)
        if self.prog > 0:   # luz do corredor
            pygame.draw.rect(surf, (180, 255, 220), r.inflate(-6, -2))
        meia = TILE * (1 - self.prog)
        for topo in (True, False):
            if topo:
                p = pygame.Rect(r.x, r.y, TILE, int(meia))
            else:
                p = pygame.Rect(r.x, int(r.bottom - meia), TILE, int(meia))
            if p.height <= 0:
                continue
            pygame.draw.rect(surf, (96, 108, 122), p)
            for k in range(-TILE, TILE * 2, 10):      # listras de aviso
                pygame.draw.line(surf, (230, 190, 40), (p.x + k, p.bottom), (p.x + k + 10, p.top), 3)
            pygame.draw.rect(surf, (40, 48, 58), p, 2)
        pygame.draw.rect(surf, (60, 68, 80), r, 3)
        cor = (70, 255, 120) if self.aberta else (255, 60, 50)
        if not self.aberta and int(t * 2) % 2 == 0:
            cor = (140, 30, 30)
        pygame.draw.circle(surf, cor, (r.x - 4, r.centery), 4)


class Fase:
    """Mapa de uma fase: grade, objetos, colisões e render estático."""

    def __init__(self, idx):
        self.idx = idx
        self.cfg = MAPAS[idx]
        self.info = FASES[idx]
        self.pal = PALETAS[idx]
        g = [["#" if r in (0, ROWS - 1) or c in (0, COLS - 1) else "." for c in range(COLS)] for r in range(ROWS)]
        self.objetos = []
        for ch, c, r, w, h in self.cfg["solidos"]:
            if ch == "#":
                for rr in range(r, r + h):
                    for cc in range(c, c + w):
                        g[rr][cc] = "#"
            else:
                self.objetos.append((ch, pygame.Rect(c * TILE, r * TILE, w * TILE, h * TILE)))
        self.porta = Porta(self.cfg["porta"])
        for dr in (0, 1):
            g[self.cfg["porta"] + dr][COLS - 1] = "D"
        self.grade = g
        self.terminais = [Terminal(n, c, r) for n, c, r in self.cfg["terminais"]]
        self.solidos = [pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                        for r in range(ROWS) for c in range(COLS) if g[r][c] == "#"]
        self.solidos += [r for _, r in self.objetos]
        self.solidos += [t.rect for t in self.terminais]
        ic, ir = self.cfg["inicio"]
        self.inicio = (ic * TILE + TILE // 2, ir * TILE + TILE // 2)
        self.estatico = self._renderizar()

    @property
    def acertos(self):
        return sum(1 for t in self.terminais if t.feita)

    @property
    def meta(self):
        return self.info["meta"]

    def colisores(self):
        return self.solidos + ([self.porta.rect] if self.porta.solida else [])

    # --- render estático ---
    def _renderizar(self):
        s = pygame.Surface((LARGURA, ROWS * TILE))
        rng = random.Random(self.idx * 131 + 7)
        piso, piso2, parede, parede_luz, destaque = self.pal
        g = self.grade
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c * TILE, r * TILE
                if g[r][c] == "#":
                    pygame.draw.rect(s, parede, (x, y, TILE, TILE))
                    pygame.draw.rect(s, parede_luz, (x + 1, y + 1, TILE - 2, TILE - 2), 1)
                    if r + 1 < ROWS and g[r + 1][c] != "#":
                        pygame.draw.rect(s, parede_luz, (x, y + TILE - 6, TILE, 6))
                        pygame.draw.line(s, destaque, (x, y + TILE - 1), (x + TILE, y + TILE - 1), 1)
                    for dx, dy in ((4, 4), (TILE - 5, 4), (4, TILE - 12), (TILE - 5, TILE - 12)):
                        pygame.draw.circle(s, (parede[0] + 18, parede[1] + 18, parede[2] + 18), (x + dx, y + dy), 1)
                else:
                    v = rng.randint(-5, 5)
                    base = piso if (r + c) % 2 == 0 else piso2
                    pygame.draw.rect(s, (base[0] + v, base[1] + v, base[2] + v), (x, y, TILE, TILE))
                    pygame.draw.rect(s, (base[0] - 12, base[1] - 12, base[2] - 12), (x, y, TILE, TILE), 1)
                    for dx, dy in ((3, 3), (TILE - 4, 3), (3, TILE - 4), (TILE - 4, TILE - 4)):
                        pygame.draw.circle(s, (base[0] + 22, base[1] + 22, base[2] + 22), (x + dx, y + dy), 1)
                    if rng.random() < 0.08:                         # grade de ventilação
                        for k in range(6, TILE - 4, 5):
                            pygame.draw.line(s, (base[0] - 22, base[1] - 22, base[2] - 22), (x + 6, y + k), (x + TILE - 7, y + k), 2)
                    if rng.random() < 0.05:                         # arranhões
                        pygame.draw.line(s, (base[0] + 14, base[1] + 14, base[2] + 14),
                                         (x + rng.randint(2, 28), y + rng.randint(2, 28)),
                                         (x + rng.randint(2, 28), y + rng.randint(2, 28)), 1)
                    if r > 0 and g[r - 1][c] == "#":                # sombra sob a parede
                        sombra = pygame.Surface((TILE, 8), pygame.SRCALPHA)
                        sombra.fill((0, 0, 0, 70))
                        s.blit(sombra, (x, y))
        # faixa de aviso diante da porta
        pl = self.cfg["porta"]
        for dr in range(2):
            for c in (COLS - 3, COLS - 2):
                for k in range(0, TILE, 8):
                    pygame.draw.line(s, (200, 160, 30), (c * TILE + k, (pl + dr) * TILE + TILE),
                                     (c * TILE + k + 8, (pl + dr) * TILE), 3)
                pygame.draw.rect(s, (30, 30, 30), (c * TILE, (pl + dr) * TILE, TILE, TILE), 1)
        for ch, rect in self.objetos:
            self._desenhar_objeto(s, ch, rect, rng)
        return s

    def _desenhar_objeto(self, s, ch, r, rng):
        destaque = self.pal[4]
        pygame.draw.rect(s, (0, 0, 0), r.move(3, 4), border_radius=4)
        if ch == "M":                                                  # mesa de laboratório
            pygame.draw.rect(s, (84, 78, 72), r, border_radius=4)
            pygame.draw.rect(s, (112, 106, 98), r.inflate(-6, -6), border_radius=3)
            pygame.draw.rect(s, (50, 46, 42), r, 2, border_radius=4)
            for i in range(max(1, r.width // 40)):
                bx = r.x + 12 + i * 38
                pygame.draw.circle(s, rng.choice([(90, 220, 200), (240, 190, 70), (230, 90, 110)]), (bx, r.y + 14), 6)
                pygame.draw.circle(s, (240, 250, 255), (bx - 2, r.y + 12), 2)
            mon = pygame.Rect(r.right - 30, r.bottom - 20, 20, 12)
            pygame.draw.rect(s, (20, 30, 40), mon)
            pygame.draw.rect(s, destaque, mon.inflate(-4, -4))
        elif ch == "B":                                                # tanque cilíndrico
            c, raio = r.center, min(r.width, r.height) // 2 - 2
            pygame.draw.circle(s, (70, 80, 92), c, raio)
            pygame.draw.circle(s, (40, 130, 150), c, raio - 4)
            pygame.draw.circle(s, (90, 200, 215), c, raio - 9)
            pygame.draw.circle(s, (210, 250, 255), (c[0] - raio // 3, c[1] - raio // 3), max(2, raio // 5))
            for _ in range(4):
                pygame.draw.circle(s, (200, 245, 255), (c[0] + rng.randint(-raio // 2, raio // 2),
                                                        c[1] + rng.randint(-raio // 2, raio // 2)), 1)
        elif ch == "K":                                                # caixote
            pygame.draw.rect(s, (118, 88, 52), r, border_radius=3)
            pygame.draw.rect(s, (86, 62, 34), r, 3, border_radius=3)
            pygame.draw.line(s, (86, 62, 34), r.topleft, r.bottomright, 3)
            pygame.draw.line(s, (86, 62, 34), r.topright, r.bottomleft, 3)
        elif ch == "R":                                                # núcleo do reator
            pygame.draw.rect(s, (46, 40, 40), r, border_radius=10)
            pygame.draw.rect(s, (200, 150, 40), r, 3, border_radius=10)
            c = r.center
            for raio, cor in ((54, (90, 50, 20)), (42, (180, 80, 20)), (28, (255, 140, 40)), (14, (255, 230, 150))):
                pygame.draw.circle(s, cor, c, raio)
            for k in range(0, TILE * 5, 10):
                pygame.draw.line(s, (230, 190, 40), (r.x + k, r.y), (r.x + k + 6, r.y), 3)
                pygame.draw.line(s, (230, 190, 40), (r.x + k, r.bottom - 1), (r.x + k + 6, r.bottom - 1), 3)


# ----------------------------------------------------------------------------
# JOGADOR
# ----------------------------------------------------------------------------
class Jogador:
    def __init__(self, pos):
        self.rect = pygame.Rect(0, 0, 22, 22)
        self.rect.center = pos
        self.px, self.py = float(self.rect.centerx), float(self.rect.centery)
        self.dir = (1.0, 0.0)
        self.anim = 0.0
        self.movendo = False

    def atualizar(self, dt, teclas, colisores, pode_mover=True, analogico=(0.0, 0.0)):
        """teclas: estado do teclado; analogico: vetor do joystick virtual (toque), de -1 a 1."""
        dx = dy = 0.0
        if pode_mover:
            dx = (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT])
            dy = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP])
            dx += analogico[0]
            dy += analogico[1]
        n = math.hypot(dx, dy)
        self.movendo = n > 0.15
        if not self.movendo:
            self.anim *= 0.8
            return
        forca = min(1.0, n)
        dx, dy = dx / n, dy / n
        self.dir = (dx, dy)
        self.anim += dt * 11 * forca
        vel = VEL_JOGADOR * forca
        # eixo X e Y separados para deslizar nas paredes
        self.px += dx * vel * dt
        self.rect.centerx = round(self.px)
        for s in colisores:
            if self.rect.colliderect(s):
                if dx > 0:
                    self.rect.right = s.left
                elif dx < 0:
                    self.rect.left = s.right
                self.px = float(self.rect.centerx)   # só ressincroniza ao bater (preserva subpixel)
        self.py += dy * vel * dt
        self.rect.centery = round(self.py)
        for s in colisores:
            if self.rect.colliderect(s):
                if dy > 0:
                    self.rect.bottom = s.top
                elif dy < 0:
                    self.rect.top = s.bottom
                self.py = float(self.rect.centery)

    def desenhar(self, surf):
        cx, cy = self.rect.center
        fx, fy = self.dir
        px, py = -fy, fx
        balanco = math.sin(self.anim) if self.movendo else 0.0
        pygame.draw.ellipse(surf, (0, 0, 0), (cx - 13, cy - 6, 26, 20))               # sombra
        for lado in (-1, 1):                                                           # pernas
            o = balanco * lado * 5
            pygame.draw.circle(surf, (210, 120, 20),
                               (int(cx + px * lado * 6 + fx * o), int(cy + py * lado * 6 + fy * o)), 5)
        pygame.draw.circle(surf, (60, 70, 82), (int(cx - fx * 9), int(cy - fy * 9)), 7)   # cilindro de ar
        pygame.draw.circle(surf, (110, 125, 140), (int(cx - fx * 9), int(cy - fy * 9)), 7, 1)
        for lado in (-1, 1):                                                           # braços
            o = -balanco * lado * 5
            pygame.draw.circle(surf, (235, 140, 30),
                               (int(cx + px * lado * 11 + fx * o), int(cy + py * lado * 11 + fy * o)), 4)
        pygame.draw.circle(surf, (250, 150, 30), (cx, cy), 11)                         # torso
        pygame.draw.circle(surf, (170, 90, 10), (cx, cy), 11, 2)
        hx, hy = int(cx + fx * 3), int(cy + fy * 3)
        pygame.draw.circle(surf, (205, 215, 225), (hx, hy), 8)                         # capacete
        pygame.draw.circle(surf, (60, 200, 230), (int(hx + fx * 4), int(hy + fy * 4)), 5)  # visor
        pygame.draw.circle(surf, (230, 255, 255), (int(hx + fx * 5 - px * 1.5), int(hy + fy * 5 - py * 1.5)), 1)


# ----------------------------------------------------------------------------
# ILUMINAÇÃO
# ----------------------------------------------------------------------------
def criar_luz(raio, alfa_max=240):
    s = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    passos = max(6, raio // 3)
    for i in range(passos, 0, -1):
        r = int(raio * i / passos)
        a = int(alfa_max * (1 - (r / raio) ** 2) ** 0.9)
        pygame.draw.circle(s, (0, 0, 0, max(0, a)), (raio, raio), r)
    return s


class Iluminacao:
    def __init__(self):
        self.escuro = pygame.Surface((LARGURA, ROWS * TILE), pygame.SRCALPHA)
        self.lanterna = criar_luz(250)
        self.ambiente = criar_luz(70)
        self.brilho = criar_luz(64, 220)
        self.alfa = 238

    def aplicar(self, mundo, jogador, fase):
        self.escuro.fill((0, 4, 10, self.alfa))
        cx, cy = jogador.rect.center
        fx, fy = jogador.dir
        # lanterna (círculo deslocado para a frente = cone aproximado) + luz ambiente do capacete
        self.escuro.blit(self.lanterna, (cx + fx * 60 - 250, cy + fy * 60 - 250), special_flags=pygame.BLEND_RGBA_SUB)
        self.escuro.blit(self.ambiente, (cx - 70, cy - 70), special_flags=pygame.BLEND_RGBA_SUB)
        for t in fase.terminais:
            self.escuro.blit(self.brilho, (t.rect.centerx - 64, t.rect.centery - 64), special_flags=pygame.BLEND_RGBA_SUB)
        self.escuro.blit(self.brilho, (fase.porta.rect.centerx - 64, fase.porta.rect.centery - 64),
                         special_flags=pygame.BLEND_RGBA_SUB)
        mundo.blit(self.escuro, (0, 0))


# ----------------------------------------------------------------------------
# TECLADO VIRTUAL (toque ou mouse)
# ----------------------------------------------------------------------------
class TecladoTela:
    """Grade de teclas clicáveis. `linhas` = [[(rotulo, valor, colunas_ocupadas), ...], ...]."""

    def __init__(self, linhas, tecla=(44, 38), espaco=4):
        self.linhas = linhas
        self.tw, self.th = tecla
        self.espaco = espaco
        self.teclas = []          # [(rect, rotulo, valor)]
        self.apertada = (None, 0.0)

    @property
    def tamanho(self):
        cols = max(sum(c for *_, c in l) for l in self.linhas)
        return (cols * self.tw + (cols - 1) * self.espaco,
                len(self.linhas) * self.th + (len(self.linhas) - 1) * self.espaco)

    def posicionar(self, x, y):
        self.teclas = []
        for i, linha in enumerate(self.linhas):
            cx = x
            for rotulo, valor, cols in linha:
                w = cols * self.tw + (cols - 1) * self.espaco
                self.teclas.append((pygame.Rect(cx, y + i * (self.th + self.espaco), w, self.th), rotulo, valor))
                cx += w + self.espaco

    def tocar(self, pos):
        for rect, _, valor in self.teclas:
            if rect.collidepoint(pos):
                self.apertada = (valor, time.perf_counter())
                return valor
        return None

    def desenhar(self, surf, fonte, fundo, borda, texto, apagadas=()):
        valor_ap, quando = self.apertada
        recente = time.perf_counter() - quando < 0.15
        for rect, rotulo, valor in self.teclas:
            cor = tuple(min(255, c + 60) for c in fundo) if (recente and valor == valor_ap) else fundo
            desligada = valor in apagadas
            if desligada:
                cor = tuple((c + 200) // 2 for c in fundo)
            pygame.draw.rect(surf, cor, rect, border_radius=6)
            pygame.draw.rect(surf, borda, rect, 2, border_radius=6)
            img = render_texto(rotulo, fonte, (150, 140, 120) if desligada else texto)
            surf.blit(img, img.get_rect(center=rect.center))


def _k(*rotulos):
    """Atalho: cada tecla ocupa 1 coluna e envia o próprio rótulo."""
    return [(r, r, 1) for r in rotulos]


# ----------------------------------------------------------------------------
# BLOCO DE NOTAS
# ----------------------------------------------------------------------------
class BlocoNotas:
    RECT = pygame.Rect(LARGURA - 276, 72, 260, 500)
    LINHAS_VISIVEIS = 7
    OPERADORES = "+-*/^!x×"

    def __init__(self, fonte):
        self.fonte = fonte
        self.aberto = False
        self.pode_responder = False      # o Jogo liga quando há um terminal aguardando resposta
        self.teclado = TecladoTela([
            _k("7", "8", "9", "/", "("),
            _k("4", "5", "6", "*", ")"),
            _k("1", "2", "3", "-", "!"),
            _k("0", ".", "^", "+") + [("<-", "APAGAR", 1)],
            [("CE", "LIMPAR", 1), ("=", "CALCULAR", 2), ("Fechar", "FECHAR", 2)],
            [("Usar na resposta", "RESPOSTA", 5)],
        ])
        w, h = self.teclado.tamanho
        self.teclado.posicionar(self.RECT.centerx - w // 2, self.RECT.bottom - h - 12)
        self.reiniciar()

    def reiniciar(self):
        self.linhas = [("", 0)]      # (texto, tipo)  tipo 0 = digitado, 1 = resultado

    @property
    def ultimo_resultado(self):
        """Valor do último '= resultado' (ou None)."""
        for texto, tipo in reversed(self.linhas):
            if tipo == 1:
                return texto[2:]
        return None

    @property
    def resultado_inteiro(self):
        """Último resultado, se for inteiro não negativo (o formato aceito pelos terminais)."""
        r = self.ultimo_resultado
        return r if r is not None and r.isdigit() else None

    # --- ações (compartilhadas por teclado físico e virtual) ---
    def calcular(self):
        if not self.linhas[-1][0].strip():
            return                       # '=' numa linha vazia não cria linhas em branco
        res = avaliar_expressao(self.linhas[-1][0])
        self.linhas.append(("= " + res, 1) if res is not None else ("= erro na expressão", 2))
        self.linhas.append(("", 0))
        self.linhas = self.linhas[-40:]

    def apagar(self):
        texto, _ = self.linhas[-1]
        if texto:
            self.linhas[-1] = (texto[:-1], 0)
        elif len(self.linhas) > 1:
            self.linhas.pop()
            if self.linhas[-1][1] != 0:
                self.linhas.pop()

    def digitar(self, ch):
        atual = self.linhas[-1][0]
        # Continuar a conta: operador logo após um resultado usa o resultado (como numa calculadora).
        if not atual and ch in self.OPERADORES and len(self.linhas) >= 2 and self.linhas[-2][1] == 1:
            atual = self.linhas[-2][0][2:]
        texto = atual + ch
        if self.fonte.size(texto)[0] <= self.RECT.width - 34:
            self.linhas[-1] = (texto, 0)

    def evento(self, e):
        """Trata o evento. Devolve 'RESPOSTA' quando o jogador pede para usar o resultado no terminal."""
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            v = self.teclado.tocar(e.pos)
            if v == "FECHAR":
                self.aberto = False
            elif v == "CALCULAR":
                self.calcular()
            elif v == "APAGAR":
                self.apagar()
            elif v == "LIMPAR":
                self.linhas[-1] = ("", 0)
            elif v == "RESPOSTA":
                return "RESPOSTA" if self.pode_responder and self.resultado_inteiro else None
            elif v:
                self.digitar(v)
            return None
        if e.type != pygame.KEYDOWN:
            return None
        if e.key in (pygame.K_n, pygame.K_ESCAPE):
            self.aberto = False
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.calcular()
        elif e.key == pygame.K_BACKSPACE:
            self.apagar()
        elif e.unicode and e.unicode.isprintable() and e.unicode not in "nN":
            self.digitar(e.unicode)
        return None

    def desenhar(self, surf, t):
        r = self.RECT
        painel(surf, r, cor=(238, 228, 190), borda=(120, 90, 40), alfa=245, raio=8)
        tinta = (40, 36, 30)
        desenhar_texto(surf, "BLOCO DE NOTAS", self.fonte, (120, 60, 20), (r.centerx, r.y + 8), centro=True, sombra=False)
        pygame.draw.line(surf, (190, 120, 90), (r.x + 12, r.y + 34), (r.right - 12, r.y + 34), 2)
        y = r.y + 42
        visiveis = self.linhas[-self.LINHAS_VISIVEIS:]
        cores = {0: tinta, 1: (20, 110, 60), 2: (170, 40, 30)}
        for texto, tipo in visiveis:
            desenhar_texto(surf, texto, self.fonte, cores[tipo], (r.x + 14, y), sombra=False)
            y += 23
        if int(t * 2) % 2 == 0:
            cx = r.x + 14 + self.fonte.size(self.linhas[-1][0])[0] + 1
            yy = r.y + 42 + (len(visiveis) - 1) * 23
            pygame.draw.line(surf, tinta, (cx, yy + 2), (cx, yy + 19), 2)
        dica = "Após o =, use * + - /" if self.ultimo_resultado else "Ex: 8!/(3!*5!) e ="
        desenhar_texto(surf, dica, self.fonte, (110, 90, 60),
                       (r.x + 14, self.teclado.teclas[0][0].y - 26), sombra=False)
        apagadas = set() if (self.pode_responder and self.resultado_inteiro) else {"RESPOSTA"}
        self.teclado.desenhar(surf, self.fonte, (214, 200, 160), (140, 110, 60), tinta, apagadas)
        # destaque verde no botão "Usar na resposta" quando ele pode ser usado
        if not apagadas:
            rect = [r_ for r_, _, v in self.teclado.teclas if v == "RESPOSTA"][0]
            pygame.draw.rect(surf, (30, 140, 70), rect, 3, border_radius=6)


# ----------------------------------------------------------------------------
# INTERFACE DO DESAFIO (terminal)
# ----------------------------------------------------------------------------
class Desafio:
    def __init__(self, jogo, terminal):
        self.jogo = jogo
        self.terminal = terminal
        self.entrada = ""
        self.estado = "pergunta"        # "pergunta" | "feedback"
        self.acertou = False
        self.questao_resolvida = None
        self.btn = pygame.Rect(0, 0, 240, 48)
        self.btn_notas = pygame.Rect(0, 0, 150, 42)
        self.btn_sair = pygame.Rect(0, 0, 150, 42)
        self.teclado = TecladoTela([_k("7", "8", "9"), _k("4", "5", "6"), _k("1", "2", "3"),
                                    [("<-", "APAGAR", 1), ("0", "0", 1), ("OK", "OK", 1)]],
                                   tecla=(66, 50), espaco=6)
        self.layout()

    @property
    def questao(self):
        return self.terminal.questao

    def painel_rect(self):
        w = 720
        x = 16 if self.jogo.notas.aberto else (LARGURA - w) // 2
        return pygame.Rect(x, 46, w, 548)

    def layout(self):
        """Posiciona teclado e botões (o painel muda de lugar quando o bloco de notas abre)."""
        r = self.painel_rect()
        w, h = self.teclado.tamanho
        self.teclado.posicionar(r.right - 30 - w, r.bottom - 30 - h)
        self.btn_notas.topleft = (r.x + 30, r.bottom - 108)
        self.btn_sair.topleft = (r.x + 192, r.bottom - 108)
        self.btn.midbottom = (r.centerx, r.bottom - 18)

    def digitar(self, ch):
        if len(self.entrada) < 9:
            self.entrada += ch

    def evento(self, e):
        self.layout()
        clique = e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
        if self.estado == "pergunta":
            if clique:
                v = self.teclado.tocar(e.pos)
                if v == "APAGAR":
                    self.entrada = self.entrada[:-1]
                elif v == "OK":
                    if self.entrada:
                        self.enviar()
                elif v:
                    self.digitar(v)
                elif self.btn_notas.collidepoint(e.pos):
                    self.jogo.notas.aberto = not self.jogo.notas.aberto
                elif self.btn_sair.collidepoint(e.pos):
                    self.jogo.desafio = None
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.jogo.desafio = None
                elif e.key == pygame.K_BACKSPACE:
                    self.entrada = self.entrada[:-1]
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.entrada:
                        self.enviar()
                elif e.unicode and e.unicode in "0123456789":
                    self.digitar(e.unicode)
        else:
            ok = (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)) or \
                 (clique and self.btn.collidepoint(e.pos))
            if ok:
                self.jogo.continuar_desafio(self)

    def enviar(self):
        self.jogo.notas.aberto = False       # respondeu: o bloco de notas fecha sozinho
        self.questao_resolvida = self.questao
        self.acertou = self.entrada.strip() == self.questao["resposta"]
        self.estado = "feedback"
        self.jogo.processar_resposta(self.terminal, self.acertou)

    def novo_enunciado(self):
        self.entrada = ""
        self.estado = "pergunta"

    def _botao(self, surf, rect, texto, cor):
        sobre = rect.collidepoint(mouse_jogo())
        pygame.draw.rect(surf, (30, 110, 140) if sobre else (20, 70, 100), rect, border_radius=8)
        pygame.draw.rect(surf, cor, rect, 2, border_radius=8)
        desenhar_texto(surf, texto, self.jogo.fontes["texto"], BRANCO,
                       (rect.centerx, rect.centery - self.jogo.fontes["texto"].get_height() // 2), centro=True)

    def desenhar(self, surf, t):
        self.layout()
        surf.blit(self.jogo.veu(170), (0, 0))
        r = self.painel_rect()
        cor = CIANO if self.estado == "pergunta" else (VERDE if self.acertou else VERMELHO)
        painel(surf, r, borda=cor)
        f = self.jogo.fontes
        x, larg = r.x + 30, r.width - 60
        fase = self.jogo.fase
        q = self.questao_resolvida if self.estado == "feedback" else self.questao
        desenhar_texto(surf, f"TERMINAL: {self.terminal.nome.upper()}", f["titulo"], cor, (x, r.y + 16))
        desenhar_texto(surf, f"Fase {fase.idx + 1} · {fase.info['conteudo']} · Questão {q['id']}",
                       f["peq"], CINZA, (x, r.y + 52))
        pygame.draw.line(surf, (50, 80, 100), (x, r.y + 78), (r.right - 30, r.y + 78), 1)
        if self.estado == "pergunta":
            desenhar_paragrafo(surf, q["enunciado"], f["texto"], BRANCO, x, r.y + 92, larg, espaco=5)
            caixa = pygame.Rect(x, r.bottom - 178, 312, 54)
            desenhar_texto(surf, "Sua resposta (apenas números):", f["peq"], CINZA, (x, caixa.y - 24))
            pygame.draw.rect(surf, (4, 10, 16), caixa, border_radius=6)
            pygame.draw.rect(surf, cor, caixa, 2, border_radius=6)
            cursor = "_" if int(t * 2) % 2 == 0 else " "
            desenhar_texto(surf, self.entrada + cursor, f["grande"], BRANCO, (caixa.x + 14, caixa.y + 6))
            self._botao(surf, self.btn_notas, "Notas [N]", CIANO)
            self._botao(surf, self.btn_sair, "Sair [Esc]", CIANO)
            erros = f"Erros: {self.jogo.erros}/{MAX_ERROS}  (cada erro: +1 falha e -{PENALIDADE_ERRO}s)"
            desenhar_texto(surf, erros, f["peq"], AMARELO, (x, r.bottom - 50))
            self.teclado.desenhar(surf, f["grande"], (16, 44, 60), cor, BRANCO)
        else:
            if self.acertou:
                desenhar_texto(surf, "ACESSO CONCEDIDO", f["grande"], VERDE, (x, r.y + 90))
                msg = "Protocolo quebrado. O terminal ficou VERDE."
            else:
                desenhar_texto(surf, "SOBRECARGA NO TERMINAL!", f["grande"], VERMELHO, (x, r.y + 90))
                msg = (f"Você respondeu {self.entrada}. A resposta correta era {q['resposta']}. "
                       f"+1 falha crítica e -{PENALIDADE_ERRO}s. Uma nova questão foi sorteada.")
            y = desenhar_paragrafo(surf, msg, f["texto"], BRANCO, x, r.y + 136, larg, espaco=4)
            desenhar_texto(surf, "Resolução:", f["texto"], AMARELO, (x, y + 8))
            desenhar_paragrafo(surf, q["resolucao"], f["texto"], (210, 230, 240), x, y + 38, larg, espaco=4)
            self._botao(surf, self.btn, "Continuar [Enter]", cor)


# ----------------------------------------------------------------------------
# CONTROLES DE TOQUE (celular / tablet)
# ----------------------------------------------------------------------------
class ControlesToque:
    """Joystick virtual + botões de ação. Aceita vários dedos ao mesmo tempo.

    Usa coordenadas da TELA real (não do jogo). Com faixas laterais largas (celular
    deitado) os controles ficam nelas; sem faixas, ficam por cima dos cantos do mapa.
    """

    def __init__(self):
        self.ativo = False
        self.dedo_joy = None
        self.vetor = (0.0, 0.0)
        self.layout(LARGURA, 0)

    def layout(self, larg_tela, margem):
        self.lateral = margem >= 150
        if self.lateral:
            meio_esq, meio_dir = margem // 2, larg_tela - margem // 2
            self.raio = min(80, margem // 2 - 14)
            self.base = (meio_esq, ALTURA - 190)
            self.btn_e = ((meio_dir, ALTURA - 250), min(64, margem // 2 - 12))
            self.btn_n = ((meio_dir, ALTURA - 100), 44)
        else:
            self.raio = 74
            self.base = (margem + 130, ALTURA - 130)
            self.btn_e = ((margem + LARGURA - 120, ALTURA - 130), 58)
            self.btn_n = ((margem + LARGURA - 250, ALTURA - 80), 38)
        self.camada = pygame.Surface((larg_tela, ALTURA), pygame.SRCALPHA)
        self.soltar_tudo()

    def soltar_tudo(self):
        self.dedo_joy = None
        self.vetor = (0.0, 0.0)
        self.knob = self.base

    @staticmethod
    def _dentro(pos, centro, raio):
        return math.hypot(pos[0] - centro[0], pos[1] - centro[1]) <= raio

    def apertar(self, dedo, pos):
        """Devolve 'E', 'N', 'JOY' ou None (toque fora dos controles)."""
        if self._dentro(pos, *self.btn_e):
            return "E"
        if self._dentro(pos, *self.btn_n):
            return "N"
        if self._dentro(pos, self.base, self.raio * 1.6):
            self.dedo_joy = dedo
            self.mover(dedo, pos)
            return "JOY"
        return None

    def mover(self, dedo, pos):
        if dedo != self.dedo_joy:
            return
        dx, dy = pos[0] - self.base[0], pos[1] - self.base[1]
        d = math.hypot(dx, dy)
        if d > self.raio:
            dx, dy = dx / d * self.raio, dy / d * self.raio
        self.knob = (self.base[0] + dx, self.base[1] + dy)
        self.vetor = (dx / self.raio, dy / self.raio)

    def soltar(self, dedo):
        if dedo == self.dedo_joy:
            self.soltar_tudo()

    def desenhar(self, surf, fontes, perto_terminal):
        camada = self.camada
        camada.fill((0, 0, 0, 0))
        forte = 90 if self.lateral else 50          # nas faixas não cobre o mapa: pode ser mais visível
        pygame.draw.circle(camada, (70, 220, 235, forte), self.base, self.raio)
        pygame.draw.circle(camada, (70, 220, 235, 160), self.base, self.raio, 3)
        pygame.draw.circle(camada, (200, 245, 255, 190), (int(self.knob[0]), int(self.knob[1])), int(self.raio * 0.4))
        (ce, re), (cn, rn) = self.btn_e, self.btn_n
        cor_e = (250, 200, 60, 220) if perto_terminal else (120, 140, 160, 150)
        pygame.draw.circle(camada, cor_e, ce, re)
        pygame.draw.circle(camada, (255, 255, 255, 190), ce, re, 3)
        pygame.draw.circle(camada, (238, 228, 190, 170), cn, rn)
        pygame.draw.circle(camada, (255, 255, 255, 190), cn, rn, 3)
        surf.blit(camada, (0, 0))
        img = render_texto("E", fontes["grande"], (20, 20, 20))
        surf.blit(img, img.get_rect(center=(ce[0], ce[1] - 8)))
        img = render_texto("ACESSAR", fontes["peq"], (20, 20, 20))
        surf.blit(img, img.get_rect(center=(ce[0], ce[1] + 22)))
        img = render_texto("N", fontes["titulo"], (60, 40, 20))
        surf.blit(img, img.get_rect(center=(cn[0], cn[1] - 6)))
        img = render_texto("NOTAS", fontes["hud_l"], (60, 40, 20))
        surf.blit(img, img.get_rect(center=(cn[0], cn[1] + 16)))


# ----------------------------------------------------------------------------
# BOTÃO SIMPLES
# ----------------------------------------------------------------------------
class Botao:
    def __init__(self, rect, texto, cor=(20, 90, 120)):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.cor = cor

    def clicado(self, e):
        return e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos)

    def desenhar(self, surf, fonte, subtexto=None):
        sobre = self.rect.collidepoint(mouse_jogo())
        c = tuple(min(255, v + 40) for v in self.cor) if sobre else self.cor
        pygame.draw.rect(surf, c, self.rect, border_radius=10)
        pygame.draw.rect(surf, CIANO, self.rect, 2, border_radius=10)
        desenhar_texto(surf, self.texto, fonte, BRANCO, (self.rect.centerx, self.rect.y + (10 if not subtexto else 8)), centro=True)


# ----------------------------------------------------------------------------
# JOGO
# ----------------------------------------------------------------------------
class Jogo:
    INTRO_TOTAL = 3.8

    def __init__(self):
        pygame.mixer.pre_init(FREQ_AUDIO, -16, 1, BUFFER_AUDIO)
        pygame.init()
        pygame.display.set_caption("Protocolo Cronos: O Bunker Submerso")
        # self.display = janela/canvas real (pode ser mais larga que o jogo no celular deitado)
        # self.tela    = superfície 1024x640 onde todo o jogo é desenhado
        # No navegador o pygbag já escala o canvas; SCALED ali distorce as coordenadas do toque.
        self._flags = 0 if EH_WEB else (pygame.SCALED | pygame.RESIZABLE)
        self.larg_tela = LARGURA
        self.ox = 0
        self.retrato = False
        self._checar_tela_t = 0.0
        try:
            self.display = pygame.display.set_mode((LARGURA, ALTURA), self._flags)
        except pygame.error:
            self._flags = 0
            self.display = pygame.display.set_mode((LARGURA, ALTURA))
        self.tela = pygame.Surface((LARGURA, ALTURA))
        pygame.display.set_icon(self._icone())
        self.relogio = pygame.time.Clock()
        # superfícies reutilizadas a cada frame (evita alocar telas inteiras por quadro)
        self.tela_jogo = pygame.Surface((LARGURA, ALTURA))
        self.mundo = pygame.Surface((LARGURA, ROWS * TILE))
        self.camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self.aneis = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self._veus = {}
        self.fundo_menu = pygame.Surface((LARGURA, ALTURA))
        for y in range(0, ALTURA, 4):
            k = y / ALTURA
            pygame.draw.rect(self.fundo_menu, (int(4 + 8 * k), int(14 + 28 * k), int(26 + 40 * k)), (0, y, LARGURA, 4))
        self.pausado = False
        nomes = "segoeui,calibri,dejavusans,arial"
        self.fontes = {
            "peq": pygame.font.SysFont(nomes, 16),
            "texto": pygame.font.SysFont(nomes, 21),
            "grande": pygame.font.SysFont(nomes, 32, bold=True),
            "titulo": pygame.font.SysFont(nomes, 24, bold=True),
            "gigante": pygame.font.SysFont(nomes, 56, bold=True),
            "hud_l": pygame.font.SysFont(nomes, 12, bold=True),
            "hud_v": pygame.font.SysFont(nomes, 24, bold=True),
            "mono": pygame.font.SysFont("consolas,couriernew,dejavusansmono", 17),
        }
        self.som = Som()
        self.luz = Iluminacao()
        self.notas = BlocoNotas(self.fontes["mono"])
        self.bolhas = [[random.uniform(0, LARGURA), random.uniform(0, ALTURA), random.uniform(2, 7),
                        random.uniform(10, 40)] for _ in range(40)]
        self.estado = MENU
        self.t = 0.0
        self.rodando = True
        self.btn_iniciar = Botao((LARGURA // 2 - 150, 560, 300, 56), "INICIAR MISSÃO")
        self.btn_novo = Botao((LARGURA // 2 - 170, 526, 340, 56), "INICIAR NOVA PARTIDA")
        self.btn_fugir = Botao((90, 360, 400, 120), "1 · FUGIR NA CÁPSULA", (20, 80, 60))
        self.btn_sobrecarga = Botao((534, 360, 400, 120), "2 · SOBRECARREGAR O REATOR", (110, 40, 30))
        self.btn_continuar = Botao((LARGURA // 2 - 230, 400, 220, 56), "CONTINUAR")
        self.btn_menu = Botao((LARGURA // 2 + 10, 400, 220, 56), "MENU", (90, 50, 30))
        self.r_som = pygame.Rect(LARGURA - 48, 12, 40, 40)      # botão de som (todas as telas)
        self.r_pausa = pygame.Rect(LARGURA - 94, 12, 40, 40)    # botão de pausa (durante o jogo)
        self.final_escolhido = None
        self.arrastando_vol = None      # dedo/mouse que está arrastando o controle de volume
        self.toque = ControlesToque()
        self.toque.ativo = self._eh_celular()
        if self.toque.ativo:
            self._instalar_tela_cheia()
            self.checar_tela(forcar=True)
        self.novo_jogo(iniciar=False)

    # ------------------------------------------------------------ tela (celular)
    @staticmethod
    def _instalar_tela_cheia():
        """No navegador do celular: a cada toque, entra em tela cheia e trava na horizontal.

        O pedido roda dentro do próprio evento de toque do navegador (exigência dos browsers).
        No iPhone o Safari não permite tela cheia em páginas; lá a saída é 'Adicionar à Tela de Início'.
        """
        js = """
        (function(){
          function cheia(){
            var d=document, e=d.documentElement;
            if (d.fullscreenElement || d.webkitFullscreenElement) return;
            var pedir = e.requestFullscreen || e.webkitRequestFullscreen;
            if (!pedir) return;
            try {
              var p = pedir.call(e, {navigationUI: "hide"});
              if (p && p.then) p.then(function(){
                if (screen.orientation && screen.orientation.lock)
                  screen.orientation.lock("landscape").catch(function(){});
              }).catch(function(){});
            } catch(err) {}
          }
          window.addEventListener("touchend", cheia, true);
          window.addEventListener("click", cheia, true);
        })();
        """
        try:
            import platform
            platform.window.eval(js)
        except Exception:
            pass

    def checar_tela(self, forcar=False):
        """Ajusta a largura do canvas à proporção da tela do aparelho (só no navegador)."""
        if not EH_WEB:
            return
        try:
            import platform
            w, h = float(platform.window.innerWidth), float(platform.window.innerHeight)
        except Exception:
            return
        if w <= 0 or h <= 0:
            return
        self.retrato = h > w
        alvo = LARGURA if self.retrato else int(ALTURA * w / h)
        self.ajustar_largura(alvo, forcar)

    def ajustar_largura(self, larg, forcar=False):
        """Redimensiona a tela real; o jogo fica centralizado e as faixas laterais recebem os controles."""
        global DESLOCAMENTO_X
        larg = max(LARGURA, min(int(larg), LARGURA * 2))
        larg -= larg % 2
        if not forcar and abs(larg - self.larg_tela) < 8:
            return
        try:
            self.display = pygame.display.set_mode((larg, ALTURA), self._flags)
        except pygame.error:
            try:    # o modo SCALED (desktop) não aceita trocar de tamanho; usa o modo simples
                self._flags = 0
                self.display = pygame.display.set_mode((larg, ALTURA))
            except pygame.error:
                return
        self.larg_tela = larg
        self.ox = DESLOCAMENTO_X = (larg - LARGURA) // 2
        self.toque.layout(larg, self.ox)
        if EH_WEB:
            try:
                import platform
                platform.window.window_resize()     # o pygbag reajusta o tamanho do canvas na página
            except Exception:
                pass

    def para_jogo(self, pos):
        """Converte coordenadas da tela real para as do jogo."""
        return (int(pos[0]) - self.ox, int(pos[1]))

    @staticmethod
    def _eh_celular():
        """No navegador, liga os controles de toque se o aparelho for celular/tablet."""
        if not EH_WEB:
            return False
        try:
            import platform
            ua = str(platform.window.navigator.userAgent).lower()
            return any(k in ua for k in ("android", "iphone", "ipad", "mobile", "tablet"))
        except Exception:
            return False

    @staticmethod
    def _icone():
        """Ícone da janela desenhado por código (capacete de mergulho)."""
        s = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(s, (250, 150, 30), (16, 16), 15)
        pygame.draw.circle(s, (205, 215, 225), (16, 16), 11)
        pygame.draw.circle(s, (60, 200, 230), (19, 15), 6)
        return s

    def veu(self, alfa):
        """Película preta translúcida em tela cheia (criada uma vez por nível de alfa)."""
        if alfa not in self._veus:
            v = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            v.fill((0, 0, 0, alfa))
            self._veus[alfa] = v
        return self._veus[alfa]

    # ------------------------------------------------------------ partida
    def novo_jogo(self, iniciar=True):
        """Reseta tempo, erros, acertos, bancos embaralhados e notas."""
        self.tempo = float(TEMPO_TOTAL)
        self.erros = 0
        self.acertos_total = 0
        self.baralhos = {n: Baralho(n) for n in BANCO_QUESTOES}
        self.fase_idx = 0
        self.desafio = None
        self.notas.reiniciar()
        self.notas.aberto = False
        self.flash_verm = self.flash_verde = self.tremor = 0.0
        self.aviso = ("", 0.0)
        self.derrota_pendente = None
        self.motivo_derrota = ""
        self.final_escolhido = None
        self.passo_t = 0.0
        self.pausado = False
        self.fogos = []
        self.cinema_t = 0.0
        self.carregar_fase(0)
        if iniciar:
            self.estado = INTRO
            self.intro_t = 0.0
            self.som.tocar("fase")

    def carregar_fase(self, idx):
        self.fase_idx = idx
        self.fase = Fase(idx)
        self.jogador = Jogador(self.fase.inicio)
        self.desafio = None

    def avisar(self, texto, dur=3.0):
        self.aviso = (texto, dur)

    # ------------------------------------------------------------ regras
    def processar_resposta(self, terminal, acertou):
        if acertou:
            terminal.feita = True
            self.acertos_total += 1
            self.flash_verde = 0.6
            self.som.tocar("acerto")
            if self.fase.acertos >= self.fase.meta and not self.fase.porta.aberta:
                self.fase.porta.abrir()
                self.som.tocar("porta", 0.6)
                self.avisar("Meta cumprida! A porta hidráulica está se abrindo.", 4.0)
        else:
            self.erros += 1
            self.tempo -= PENALIDADE_ERRO
            self.flash_verm = 0.7
            self.tremor = 0.6
            self.som.tocar("erro")
            terminal.questao = self.baralhos[self.fase_idx + 1].sortear(
                em_uso=[t.questao["id"] for t in self.fase.terminais if t.questao])
            if self.erros >= MAX_ERROS:
                self.derrota_pendente = "Falhas críticas demais: o sistema do bunker colapsou."
            elif self.tempo <= 0:
                self.derrota_pendente = "O tempo acabou: o oxigênio da estação se esgotou."

    def continuar_desafio(self, desafio):
        if self.derrota_pendente:
            self.encerrar(DERROTA, self.derrota_pendente)
        elif desafio.acertou:
            self.desafio = None
        else:
            desafio.novo_enunciado()

    def encerrar(self, estado, motivo=""):
        self.estado = estado
        self.motivo_derrota = motivo
        self.desafio = None
        self.notas.aberto = False
        self.tremor = 0.0
        if estado == DERROTA:
            self.som.tocar("derrota")
        else:
            self.fogos = []
            self.som.tocar("tema" if "tema" in self.som.sons else "vitoria", 0.6)

    def interagir(self):
        for t in self.fase.terminais:
            if not t.feita and t.rect.inflate(34, 34).colliderect(self.jogador.rect):
                if t.questao is None:
                    t.questao = self.baralhos[self.fase_idx + 1].sortear(
                        em_uso=[x.questao["id"] for x in self.fase.terminais if x.questao])
                self.desafio = Desafio(self, t)
                self.som.tocar("bipe")
                return

    def terminal_proximo(self):
        for t in self.fase.terminais:
            if not t.feita and t.rect.inflate(34, 34).colliderect(self.jogador.rect):
                return t
        return None

    # ------------------------------------------------------------ eventos
    def apertar(self, dedo, pos):
        """Botões de sistema e controles de toque (pos em coordenadas da tela real).
        Devolve True se o toque/clique foi consumido."""
        pj = self.para_jogo(pos)
        if self.r_som.collidepoint(pj):
            self.som.alternar_mudo()
            return True
        rv = self.r_volume()
        if rv and rv.inflate(24, 20).collidepoint(pj):          # começa a arrastar o volume
            self.arrastando_vol = dedo
            self._ajustar_volume(pj[0])
            return True
        if self.estado != JOGANDO or self.pausado:
            return False
        if self.r_pausa.collidepoint(pj):
            self.pausado = True
            self.toque.soltar_tudo()
            return True
        if self.toque.ativo and not self.desafio and not self.notas.aberto:
            acao = self.toque.apertar(dedo, pos)
            if acao == "E":
                self.interagir()
            elif acao == "N":
                self.notas.aberto = True
                self.toque.soltar_tudo()
            return acao is not None
        return False

    def tratar_evento(self, e):
        if e.type == pygame.QUIT:
            self.rodando = False
            return
        # --- toque (celular): cada dedo é rastreado; toques fora dos controles viram clique ---
        if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            self.toque.ativo = True
            self._viu_dedo = True
            pos = (int(e.x * self.larg_tela), int(e.y * ALTURA))     # coordenadas da tela real
            dedo = ("dedo", e.finger_id)
            if e.type == pygame.FINGERDOWN:
                if not self.apertar(dedo, pos):
                    self.tratar_evento(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=self.para_jogo(pos),
                                                          button=1, sintetico=True))
            elif e.type == pygame.FINGERMOTION:
                if self.arrastando_vol == dedo:
                    self._ajustar_volume(self.para_jogo(pos)[0])
                self.toque.mover(dedo, pos)
            else:
                if self.arrastando_vol == dedo:
                    self.arrastando_vol = None
                self.toque.soltar(dedo)
            return
        if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if getattr(e, "touch", False) and getattr(self, "_viu_dedo", False):
                return      # o SDL duplica cada toque como mouse; ele já foi tratado acima
            if not getattr(e, "sintetico", False):
                # e.pos vem na tela real: controles usam ela; o resto do jogo recebe a posição convertida
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self.apertar("mouse", e.pos):
                        return
                elif e.type == pygame.MOUSEMOTION:
                    if self.arrastando_vol == "mouse":
                        self._ajustar_volume(self.para_jogo(e.pos)[0])
                    self.toque.mover("mouse", e.pos)
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.arrastando_vol == "mouse":
                        self.arrastando_vol = None
                    self.toque.soltar("mouse")
                e = pygame.event.Event(e.type, {**e.dict, "pos": self.para_jogo(e.pos), "sintetico": True})
        # --- atalhos globais ---
        if e.type == pygame.KEYDOWN and not self.notas.aberto:
            if e.key == pygame.K_m:
                self.som.alternar_mudo()
                return
            if e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.som.definir_volume(self.som.volume - 0.1)
                return
            if e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.som.definir_volume(self.som.volume + 0.1)
                if self.som.mudo:
                    self.som.alternar_mudo()
                return
            if e.key == pygame.K_t and not self.desafio:
                self.toque.ativo = not self.toque.ativo
                self.toque.soltar_tudo()
                return
        if self.estado == MENU:
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)) or self.btn_iniciar.clicado(e):
                self.novo_jogo()
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.rodando = False
        elif self.estado == INTRO:
            pular = (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)) or \
                    (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
            if pular and self.intro_t > 0.7:
                self.intro_t = max(self.intro_t, self.INTRO_TOTAL - 0.7)
        elif self.estado == JOGANDO:
            if self.pausado:
                if (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN)) \
                        or self.btn_continuar.clicado(e):
                    self.pausado = False
                elif (e.type == pygame.KEYDOWN and e.key == pygame.K_q) or self.btn_menu.clicado(e):
                    self.pausado = False
                    self.estado = MENU
            elif self.notas.aberto:
                if (self.desafio and e.type == pygame.MOUSEBUTTONDOWN
                        and not BlocoNotas.RECT.collidepoint(e.pos)):
                    self.desafio.evento(e)      # toque no terminal com as notas abertas (teclado, OK...)
                elif self.notas.evento(e) == "RESPOSTA" and self.desafio:
                    self.desafio.entrada = self.notas.resultado_inteiro[:9]
                    self.notas.aberto = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                self.pausado = True
            elif not self.desafio and e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.pausado = True
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_n:
                self.notas.aberto = True
            elif self.desafio:
                self.desafio.evento(e)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_e:
                self.interagir()
        elif self.estado == ESCOLHA_FINAL:
            if (e.type == pygame.KEYDOWN and e.key == pygame.K_1) or self.btn_fugir.clicado(e):
                self.iniciar_cinema("fugir")
            elif (e.type == pygame.KEYDOWN and e.key == pygame.K_2) or self.btn_sobrecarga.clicado(e):
                self.iniciar_cinema("sobrecarregar")
        elif self.estado == CINEMA:
            pular = (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE)) or \
                    (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
            if pular and self.cinema_t > 1.0:
                self.encerrar(VITORIA)
        elif self.estado in (VITORIA, DERROTA):
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_r)) or self.btn_novo.clicado(e):
                self.novo_jogo()

    # ------------------------------------------------------------ atualização
    def atualizar(self, dt):
        self.t += dt
        self.som.preparar()
        self.notas.pode_responder = bool(self.desafio and self.desafio.estado == "pergunta")
        if self.toque.ativo and EH_WEB:              # celular girou / entrou em tela cheia?
            self._checar_tela_t += dt
            if self._checar_tela_t > 0.5:
                self._checar_tela_t = 0.0
                self.checar_tela()
        for b in self.bolhas:
            b[1] -= b[3] * dt
            b[0] += math.sin(self.t + b[2]) * 8 * dt
            if b[1] < -10:
                b[0], b[1] = random.uniform(0, LARGURA), ALTURA + 10
        if self.estado == INTRO:
            self.intro_t += dt
            if self.intro_t >= self.INTRO_TOTAL:
                self.estado = JOGANDO
        elif self.estado == JOGANDO and not self.pausado:
            self.atualizar_jogo(dt)
        elif self.estado == CINEMA:
            self.atualizar_cinema(dt)
        elif self.estado == VITORIA:
            for f in self.fogos:
                f[0] += f[2] * dt
                f[1] += f[3] * dt
                f[3] += 40 * dt
                f[4] -= dt
            self.fogos = [f for f in self.fogos if f[4] > 0]
            if random.random() < 0.08:          # brilhos subindo na tela de vitória
                cx = random.uniform(120, LARGURA - 120)
                cor = random.choice([VERDE, AMARELO, CIANO, (255, 140, 200)])
                for _ in range(18):
                    ang = random.uniform(0, math.tau)
                    v = random.uniform(40, 130)
                    self.fogos.append([cx, random.uniform(40, 200), math.cos(ang) * v, math.sin(ang) * v,
                                       random.uniform(0.8, 1.6), cor])

    # ------------------------------------------------------------ cinemática de vitória
    def iniciar_cinema(self, final):
        self.final_escolhido = final
        self.estado = CINEMA
        self.cinema_t = 0.0
        self.cinema_eventos = set()
        self.cinema_bolhas = []
        self.destrocos = []
        self.tremor = 0.0
        self.desafio = None
        self.notas.aberto = False
        self.som.tocar("porta", 0.45)

    def _estacao_y(self):
        return 430 + self.cinema_t * 15           # a câmera sobe: a estação "desce" na tela

    def _capsula_pos(self):
        t = self.cinema_t
        y0 = 430 - 40
        k = 1 - (1 - min(1.0, t / 5.0)) ** 3      # sai rápido e desacelera
        return 512, y0 + (250 - y0) * k + math.sin(t * 2.2) * 4

    def atualizar_cinema(self, dt):
        self.cinema_t += dt
        t = self.cinema_t
        sobrecarga = self.final_escolhido == "sobrecarregar"
        if sobrecarga and t >= 4.5 and "boom" not in self.cinema_eventos:
            self.cinema_eventos.add("boom")
            self.som.tocar("explosao", 0.7)
            self.tremor = 1.3
            sy = self._estacao_y()
            self.destrocos = [[512 + random.uniform(-160, 160), sy + random.uniform(0, 80),
                               random.uniform(-260, 260), random.uniform(-220, 40),
                               random.randint(8, 26), random.randint(5, 14), random.uniform(0, 6)]
                              for _ in range(26)]
        if not sobrecarga and t >= 6.5 and "ping" not in self.cinema_eventos:
            self.cinema_eventos.add("ping")
            self.som.tocar("bipe", 0.25)
        if t >= 11.5 and "sol" not in self.cinema_eventos:
            self.cinema_eventos.add("sol")
            self.som.tocar("fase", 0.4)
        self.tremor = max(0.0, self.tremor - dt)
        for d in self.destrocos:
            d[0] += d[2] * dt
            d[1] += d[3] * dt + 26 * dt            # cai e acompanha a "descida" da câmera
            d[3] += 90 * dt
            d[6] += dt * 3
        cx, cy = self._capsula_pos()
        if random.random() < 0.7:
            self.cinema_bolhas.append([cx + random.uniform(-7, 7), cy + 34, random.uniform(2, 5)])
        for b in self.cinema_bolhas:
            b[1] += 95 * dt
            b[0] += math.sin(t * 3 + b[2]) * 10 * dt
        self.cinema_bolhas = [b for b in self.cinema_bolhas if b[1] < ALTURA + 10][-140:]
        if t >= CINEMA_TOTAL:
            self.encerrar(VITORIA)

    def _desenhar_estacao(self, s, sy, luzes, brilho):
        """Silhueta da Acheron-4 vista de lado."""
        for x in (360, 512, 664):                                  # pilares até o fundo
            pygame.draw.rect(s, (14, 20, 30), (x - 9, sy + 90, 18, 400))
        for x in (402, 622):                                       # cúpulas
            pygame.draw.circle(s, (30, 40, 54), (x, sy + 8), 44)
            pygame.draw.circle(s, (46, 60, 78), (x, sy + 8), 44, 2)
        corpo = pygame.Rect(0, 0, 440, 110)
        corpo.midtop = (512, sy)
        pygame.draw.rect(s, (26, 34, 46), corpo, border_radius=20)
        pygame.draw.rect(s, (52, 68, 88), corpo, 2, border_radius=20)
        for i in range(12):                                        # janelas
            jx = corpo.x + 28 + i * 33
            cor = (250, 214, 120) if i < luzes else (16, 22, 30)
            pygame.draw.rect(s, cor, (jx, sy + 34, 16, 10), border_radius=2)
        if brilho > 0:                                             # núcleo do reator
            r = int(16 + 10 * brilho)
            pygame.draw.circle(s, (255, int(120 + 100 * brilho), 40), (512, sy + 74), r)
            pygame.draw.circle(s, (255, 240, 200), (512, sy + 74), max(4, r // 2))

    def _desenhar_capsula(self, s, cx, cy, t):
        chama = 10 + int(6 * abs(math.sin(t * 30)))
        pygame.draw.polygon(s, (255, 170, 60), [(cx - 8, cy + 30), (cx + 8, cy + 30), (cx, cy + 30 + chama)])
        pygame.draw.ellipse(s, (210, 220, 232), (cx - 18, cy - 32, 36, 64))
        pygame.draw.ellipse(s, (120, 135, 150), (cx - 18, cy - 32, 36, 64), 2)
        pygame.draw.rect(s, (250, 150, 30), (cx - 18, cy + 4, 36, 6))
        pygame.draw.circle(s, (60, 200, 230), (cx, cy - 10), 8)
        pygame.draw.circle(s, (220, 255, 255), (cx - 3, cy - 13), 2)

    def desenhar_cinema(self, surf):
        t = self.cinema_t
        s = self.tela_jogo
        sobrecarga = self.final_escolhido == "sobrecarregar"
        sup = max(0.0, min(1.0, (t - 9.0) / 6.0))                 # aproximação da superfície
        lerp = lambda a, b, k: tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))
        topo = lerp((6, 16, 32), (70, 160, 210), sup)
        fundo = lerp((1, 4, 10), (16, 60, 110), sup)
        for i in range(0, ALTURA, 20):
            pygame.draw.rect(s, lerp(topo, fundo, i / ALTURA), (0, i, LARGURA, 20))
        if sup > 0:                                                # raios de sol
            self.aneis.fill((0, 0, 0, 0))
            for k in range(6):
                x = 120 + k * 170 + math.sin(t * 0.6 + k) * 30
                pygame.draw.polygon(self.aneis, (255, 255, 230, int(38 * sup)),
                                    [(x - 30, 0), (x + 30, 0), (x + 140, ALTURA), (x + 40, ALTURA)])
            s.blit(self.aneis, (0, 0))
        sy = self._estacao_y()
        explodiu = sobrecarga and t >= 4.5
        if not explodiu and sy < ALTURA + 120:
            luzes = 12 if sobrecarga else max(0, 12 - int(max(0.0, t - 3.0) * 2.2))
            brilho = min(1.0, t / 4.5) * (0.6 + 0.4 * abs(math.sin(t * (4 + 6 * t / 4.5)))) if sobrecarga else 0
            self._desenhar_estacao(s, sy, luzes, brilho)
        if not sobrecarga and 6.0 <= t <= 12.0:                   # olhos do organismo no escuro
            a = math.sin((t - 6.0) / 6.0 * math.pi)
            if int(t * 3) % 7 != 0:                                 # pisca de vez em quando
                self.camada.fill((0, 0, 0, 0))
                for ex, ey in ((150, 470), (178, 466), (860, 500), (884, 504)):
                    pygame.draw.circle(self.camada, (255, 40, 40, int(90 * a)), (ex, ey), 12)
                    pygame.draw.circle(self.camada, (255, 120, 90, int(230 * a)), (ex, ey), 4)
                s.blit(self.camada, (0, 0))
        for x, y, r in self.cinema_bolhas:
            pygame.draw.circle(s, (170, 220, 240), (int(x), int(y)), int(r), 1)
        if explodiu:
            te = t - 4.5
            for d in self.destrocos:
                p = pygame.Surface((d[4], d[5]), pygame.SRCALPHA)
                p.fill((60, 66, 78))
                p = pygame.transform.rotate(p, d[6] * 57)
                s.blit(p, (d[0], d[1]))
            if te < 3.0:
                self.camada.fill((0, 0, 0, 0))
                for k, cor in ((1.0, (255, 220, 160)), (0.7, (255, 140, 60))):
                    raio = int(te * 620 * k)
                    if raio > 4:
                        pygame.draw.circle(self.camada, (*cor, int(200 * max(0, 1 - te / 3))), (512, int(sy + 60)), raio, 10)
                brilho = max(0.0, 1 - te / 2.0)
                if brilho > 0:
                    pygame.draw.circle(self.camada, (255, 190, 90, int(160 * brilho)), (512, int(sy + 60)), int(60 + 220 * te))
                s.blit(self.camada, (0, 0))
            if te < 0.9:                                           # clarão branco
                self.camada.fill((255, 255, 255, int(255 * (1 - te / 0.9))))
                s.blit(self.camada, (0, 0))
        cx, cy = self._capsula_pos()
        self._desenhar_capsula(s, cx, int(cy), t)
        # legenda com efeito de máquina de escrever
        legendas = LEGENDAS_FINAL[self.final_escolhido]
        idx = min(len(legendas) - 1, int(t / 3.9))
        local = t - idx * 3.9
        texto = legendas[idx][:int(local * 48)]
        r = pygame.Rect(90, 56, LARGURA - 180, 84)
        painel(s, r, borda=AMARELO if sobrecarga else CIANO, alfa=200)
        desenhar_paragrafo(s, texto, self.fontes["texto"], BRANCO, r.x + 24, r.y + 12, r.width - 48, espaco=3)
        titulo = FINAIS[self.final_escolhido][0]
        desenhar_texto(s, titulo, self.fontes["titulo"], AMARELO, (LARGURA // 2, 14), centro=True)
        if t > 1.0:
            desenhar_texto(s, "[Enter] ou toque para pular", self.fontes["peq"], CINZA, (LARGURA // 2, ALTURA - 30), centro=True)
        if t > CINEMA_TOTAL - 1.2:                                 # fade para a tela de vitória
            s.blit(self.veu(int(255 * min(1.0, (t - (CINEMA_TOTAL - 1.2)) / 1.2)) // 8 * 8), (0, 0))
        ox = oy = 0
        if self.tremor > 0:
            amp = int(14 * self.tremor)
            ox, oy = random.randint(-amp, amp), random.randint(-amp, amp)
        surf.fill((0, 0, 0))
        surf.blit(s, (ox, oy))

    def classificacao(self):
        """Classificação final: (letra, título, cor, pontos)."""
        t = max(0, int(self.tempo))
        e = self.erros
        pontos = max(0, TOTAL_ACERTOS * 100 + t * 2 - e * 150)
        if e == 0 and t >= 300:
            return "S", "Mestre(a) da Combinatória", AMARELO, pontos
        if e <= 1 and t >= 180:
            return "A", "Engenheiro(a) do Protocolo", VERDE, pontos
        if e <= 3:
            return "B", "Sobrevivente Calculista", CIANO, pontos
        return "C", "Escapou por um triz", (200, 160, 255), pontos

    def atualizar_jogo(self, dt):
        self.tempo -= dt
        if self.tempo <= 0 and not self.derrota_pendente:
            self.tempo = 0
            self.encerrar(DERROTA, "O tempo acabou: o oxigênio da estação se esgotou.")
            return
        f = self.fase
        bloqueado = self.desafio is not None or self.notas.aberto
        analog = self.toque.vetor if self.toque.ativo else (0.0, 0.0)
        self.jogador.atualizar(dt, pygame.key.get_pressed(), f.colisores(), pode_mover=not bloqueado, analogico=analog)
        if self.jogador.movendo and not bloqueado:
            self.passo_t += dt
            if self.passo_t > 0.3:
                self.passo_t = 0
                self.som.tocar("passo", 0.3)
        f.porta.atualizar(dt)
        self.flash_verm = max(0, self.flash_verm - dt)
        self.flash_verde = max(0, self.flash_verde - dt)
        self.tremor = max(0, self.tremor - dt)
        txt, d = self.aviso
        self.aviso = (txt, max(0, d - dt))
        if f.porta.passavel and self.jogador.rect.colliderect(f.porta.rect):
            if self.fase_idx == len(FASES) - 1:
                self.estado = ESCOLHA_FINAL
                self.som.tocar("fase")
            else:
                self.carregar_fase(self.fase_idx + 1)
                self.estado = INTRO
                self.intro_t = 0.0
                self.som.tocar("fase")
        elif not f.porta.aberta and self.jogador.rect.inflate(10, 10).colliderect(f.porta.rect) and self.aviso[1] <= 0:
            self.avisar(f"Porta selada. Terminais restantes: {f.meta - f.acertos}.", 2.0)

    # ------------------------------------------------------------ desenho
    def desenhar_fundo_menu(self, surf):
        surf.blit(self.fundo_menu, (0, 0))
        self.aneis.fill((0, 0, 0, 0))
        for i in range(4):                                       # anéis de sonar (uma superfície só)
            raio = ((self.t * 90 + i * 160) % 640)
            alfa = max(0, 90 - int(raio / 7))
            if raio > 2:
                pygame.draw.circle(self.aneis, (70, 220, 235, alfa), (LARGURA // 2, ALTURA + 40), int(raio), 2)
        surf.blit(self.aneis, (0, 0))
        for x, y, r, _ in self.bolhas:
            pygame.draw.circle(surf, (120, 200, 230), (int(x), int(y)), int(r), 1)

    def desenhar_menu(self, surf):
        self.desenhar_fundo_menu(surf)
        f = self.fontes
        desenhar_texto(surf, "PROTOCOLO CRONOS", f["gigante"], CIANO, (LARGURA // 2, 24), centro=True)
        desenhar_texto(surf, "O Bunker Submerso", f["grande"], BRANCO, (LARGURA // 2, 90), centro=True)
        desenhar_texto(surf, "Escape Room de Análise Combinatória", f["texto"], CINZA, (LARGURA // 2, 132), centro=True)
        r = pygame.Rect(60, 170, LARGURA - 120, 210)
        painel(surf, r)
        desenhar_paragrafo(surf, TEXTO_HISTORIA, f["texto"], BRANCO, r.x + 20, r.y + 14, r.width - 40, espaco=3)
        c = pygame.Rect(60, 388, LARGURA - 120, 150)
        painel(surf, c, borda=(60, 100, 130))
        desenhar_texto(surf, "CONTROLES", f["titulo"], AMARELO, (c.x + 20, c.y + 10))
        linhas = ["WASD / Setas: mover   E: terminal   N: bloco de notas   P / Esc: pausar   M: mudo   - / +: volume",
                  "Meta: 12 acertos nas 5 fases (1 + 2 + 2 + 3 + 4).  Tempo: 12:00.  Limite: 5 falhas críticas.",
                  "Errou? Você mantém seus acertos, perde 20 s e o terminal sorteia OUTRA questão da mesma fase."]
        for i, l in enumerate(linhas):
            desenhar_texto(surf, l, f["peq"], BRANCO, (c.x + 20, c.y + 46 + i * 28))
        self.btn_iniciar.desenhar(surf, f["titulo"])

    def desenhar_intro(self, surf):
        surf.fill(FUNDO)
        for x, y, r, _ in self.bolhas:
            pygame.draw.circle(surf, (50, 100, 130), (int(x), int(y)), int(r), 1)
        f = self.fontes
        info = self.fase.info
        desenhar_texto(surf, f"FASE {self.fase_idx + 1} DE {len(FASES)}", f["grande"], AMARELO, (LARGURA // 2, 120), centro=True)
        desenhar_texto(surf, info["nome"].upper(), f["gigante"], CIANO, (LARGURA // 2, 168), centro=True)
        desenhar_texto(surf, f"Nível {info['nivel']}  ·  {info['conteudo']}", f["titulo"], BRANCO, (LARGURA // 2, 246), centro=True)
        desenhar_paragrafo(surf, info["historia"], f["texto"], CINZA, 180, 310, LARGURA - 360, centro=True)
        desenhar_texto(surf, f"Acertos necessários para abrir a porta: {info['meta']}", f["titulo"], VERDE, (LARGURA // 2, 440), centro=True)
        restante = sum(FASES[i]["meta"] for i in range(self.fase_idx))
        desenhar_texto(surf, f"Progresso global: {restante}/{TOTAL_ACERTOS}", f["texto"], CINZA, (LARGURA // 2, 480), centro=True)
        if self.intro_t > 0.7:
            desenhar_texto(surf, "[Enter] ou toque na tela para continuar", f["peq"], CINZA, (LARGURA // 2, 580), centro=True)
        # fade
        a = 255
        if self.intro_t < 0.7:
            a = int(255 * (1 - self.intro_t / 0.7))
        elif self.intro_t > self.INTRO_TOTAL - 0.7:
            a = int(255 * (self.intro_t - (self.INTRO_TOTAL - 0.7)) / 0.7)
        else:
            a = 0
        if a > 0:
            surf.blit(self.veu(min(255, a // 8 * 8)), (0, 0))

    def desenhar_hud(self, surf):
        pygame.draw.rect(surf, (8, 16, 26), (0, 0, LARGURA, HUD_H))
        pygame.draw.line(surf, CIANO, (0, HUD_H - 1), (LARGURA, HUD_H - 1), 2)
        f = self.fontes
        t = max(0, int(math.ceil(self.tempo)))
        cor_tempo = VERMELHO if (t <= 60 and int(self.t * 2) % 2 == 0) else (AMARELO if t <= 120 else BRANCO)
        campos = [
            (18, "FASE ATUAL", f"{self.fase_idx + 1}/{len(FASES)}  {self.fase.info['nome']}", BRANCO),
            (340, "ACERTOS NA FASE", f"{self.fase.acertos}/{self.fase.meta}", VERDE),
            (500, "PROGRESSO TOTAL", f"{self.acertos_total}/{TOTAL_ACERTOS}", CIANO),
            (680, "TEMPO", f"{t // 60:02d}:{t % 60:02d}", cor_tempo),
            (800, "ERROS", f"{self.erros}/{MAX_ERROS}", VERMELHO if self.erros >= MAX_ERROS - 1 else AMARELO),
        ]
        for x, rotulo, valor, cor in campos:
            desenhar_texto(surf, rotulo, f["hud_l"], CINZA, (x, 8), sombra=False)
            desenhar_texto(surf, valor, f["hud_v"], cor, (x, 26))
        for i in range(MAX_ERROS):                              # luzes de falha crítica
            pygame.draw.circle(surf, VERMELHO if i < self.erros else (50, 30, 30), (862 + i * 14, 42), 5)

    def desenhar_jogo(self):
        mundo = self.mundo
        f = self.fase
        mundo.blit(f.estatico, (0, 0))
        for t in f.terminais:
            t.desenhar(mundo, self.t)
        f.porta.desenhar(mundo, self.t)
        # bolhas/poeira flutuando
        for x, y, r, _ in self.bolhas[:25]:
            pygame.draw.circle(mundo, (150, 210, 235), (int(x), int(y - HUD_H)), max(1, int(r / 3)))
        self.jogador.desenhar(mundo)
        self.luz.aplicar(mundo, self.jogador, f)
        # prompts (acima da escuridão para ficarem legíveis)
        prox = self.terminal_proximo() if (not self.desafio and not self.notas.aberto) else None
        if prox:
            self.rotulo(mundo, f"{prox.nome}", prox.rect.centerx, prox.rect.y - 46, AMARELO)
            dica = "Toque em E para acessar" if self.toque.ativo else "[E] Acessar Terminal"
            self.rotulo(mundo, dica, prox.rect.centerx, prox.rect.y - 26, BRANCO)
        for t in f.terminais:
            if t.feita:
                self.rotulo(mundo, "CONCLUÍDO", t.rect.centerx, t.rect.y - 22, VERDE, pequeno=True)
        if f.porta.aberta:
            self.rotulo(mundo, "PORTA ABERTA >>", f.porta.rect.x - 50, f.porta.rect.y - 22, VERDE, pequeno=True)

        c = self.tela_jogo
        c.fill(FUNDO)
        ox = oy = 0
        if self.tremor > 0:
            amp = 9 * self.tremor
            ox, oy = random.randint(-int(amp), int(amp)), random.randint(-int(amp), int(amp))
        c.blit(mundo, (ox, HUD_H + oy))
        if self.flash_verm > 0:
            self.camada.fill((255, 20, 20, int(150 * self.flash_verm / 0.7)))
            c.blit(self.camada, (0, 0))
        if self.flash_verde > 0:
            self.camada.fill((30, 255, 120, int(110 * self.flash_verde / 0.6)))
            c.blit(self.camada, (0, 0))
        self.desenhar_hud(c)
        txt, d = self.aviso
        if d > 0:
            r = pygame.Rect(0, 0, 640, 40)
            r.midtop = (LARGURA // 2, HUD_H + 10)
            painel(c, r, borda=AMARELO)
            desenhar_texto(c, txt, self.fontes["texto"], AMARELO, (r.centerx, r.y + 7), centro=True)
        self.tela.blit(c, (0, 0))
        self._perto_terminal = prox is not None
        if self.desafio:
            self.desafio.desenhar(self.tela, self.t)
        if self.notas.aberto:
            self.notas.desenhar(self.tela, self.t)
        if self.pausado:
            self.tela.blit(self.veu(190), (0, 0))
            fo = self.fontes
            desenhar_texto(self.tela, "PAUSADO", fo["gigante"], CIANO, (LARGURA // 2, 210), centro=True)
            desenhar_texto(self.tela, "O cronômetro está parado.", fo["texto"], BRANCO, (LARGURA // 2, 290), centro=True)
            desenhar_texto(self.tela, "[Esc / P] Continuar     [Q] Menu     [M] Mudo     [- / +] Volume", fo["peq"], CINZA,
                           (LARGURA // 2, 340), centro=True)
            self.btn_continuar.desenhar(self.tela, fo["titulo"])
            self.btn_menu.desenhar(self.tela, fo["titulo"])

    def desenhar_botoes_sistema(self, surf):
        """Botão de som (sempre) e de pausa (durante o jogo), clicáveis por mouse ou toque."""
        botoes = [self.r_som] + ([self.r_pausa] if self.estado == JOGANDO and not self.pausado else [])
        for r in botoes:
            pygame.draw.rect(surf, (16, 32, 46), r, border_radius=8)
            pygame.draw.rect(surf, CIANO, r, 2, border_radius=8)
        cx, cy = self.r_som.centerx - 5, self.r_som.centery
        pygame.draw.rect(surf, BRANCO, (cx - 9, cy - 5, 6, 10))
        pygame.draw.polygon(surf, BRANCO, [(cx - 3, cy - 5), (cx + 4, cy - 11), (cx + 4, cy + 11), (cx - 3, cy + 5)])
        if self.som.mudo:
            pygame.draw.line(surf, VERMELHO, (cx + 8, cy - 6), (cx + 16, cy + 6), 3)
            pygame.draw.line(surf, VERMELHO, (cx + 16, cy - 6), (cx + 8, cy + 6), 3)
        else:                                   # "ondas" do alto-falante conforme o volume
            if self.som.volume > 0.02:
                pygame.draw.arc(surf, BRANCO, (cx + 2, cy - 6, 10, 12), -1.1, 1.1, 2)
            if self.som.volume > 0.5:
                pygame.draw.arc(surf, BRANCO, (cx + 2, cy - 11, 18, 22), -1.1, 1.1, 2)
        if self.r_pausa in botoes:
            for dx in (-6, 3):
                pygame.draw.rect(surf, BRANCO, (self.r_pausa.centerx + dx, self.r_pausa.centery - 9, 4, 18))
        self.desenhar_volume(surf)

    # ------------------------------------------------------------ controle de volume
    def r_volume(self):
        """Área do controle deslizante na tela atual (coordenadas do jogo) ou None se não aparece."""
        if self.estado == JOGANDO:
            return pygame.Rect(LARGURA // 2 - 200, 486, 400, 44) if self.pausado else None
        if self.estado in (INTRO, CINEMA):
            return None
        return pygame.Rect(LARGURA - 8 - 160, 58, 160, 38)        # menu, escolha, vitória, derrota

    def _ajustar_volume(self, x):
        r = self.r_volume()
        if not r:
            return
        self.som.definir_volume((x - (r.x + 14)) / (r.width - 28))
        if self.som.mudo and self.som.volume > 0:
            self.som.alternar_mudo()        # mexer no volume tira do mudo

    def desenhar_volume(self, surf):
        r = self.r_volume()
        if not r:
            return
        grande = r.width > 300
        f = self.fontes["texto" if grande else "hud_l"]
        v = self.som.volume
        ativo = not self.som.mudo
        cor = CIANO if ativo else CINZA
        x0, x1 = r.x + 14, r.right - 14
        y = r.bottom - (14 if grande else 10)
        texto = f"Volume: {round(v * 100)}%" + ("" if ativo else "  (mudo)")
        desenhar_texto(surf, texto, f, BRANCO if grande else CINZA,
                       (r.centerx, r.y - (22 if grande else -2)), centro=True, sombra=grande)
        pygame.draw.line(surf, (40, 56, 72), (x0, y), (x1, y), 8 if grande else 6)
        xk = int(x0 + (x1 - x0) * v)
        if xk > x0:
            pygame.draw.line(surf, cor, (x0, y), (xk, y), 8 if grande else 6)
        pygame.draw.circle(surf, BRANCO, (xk, y), 14 if grande else 9)
        pygame.draw.circle(surf, cor, (xk, y), 14 if grande else 9, 3)

    def rotulo(self, surf, texto, cx, cy, cor, pequeno=False):
        fonte = self.fontes["hud_l"] if pequeno else self.fontes["peq"]
        img = render_texto(texto, fonte, cor)
        r = img.get_rect(center=(cx, cy))
        fundo = r.inflate(10, 4)
        painel(surf, fundo, cor=(0, 0, 0), borda=(0, 0, 0), alfa=170, raio=4)
        surf.blit(img, r)

    def desenhar_escolha(self, surf):
        self.desenhar_fundo_menu(surf)
        f = self.fontes
        desenhar_texto(surf, "A CÁPSULA ESTÁ PRONTA", f["gigante"], VERDE, (LARGURA // 2, 40), centro=True)
        desenhar_paragrafo(surf, "Todos os protocolos foram quebrados. O reator de Acheron-4 está instável e o organismo "
                                 "ainda se agita do outro lado das paredes. Você tem apenas uma decisão a tomar:",
                           f["texto"], BRANCO, 120, 150, LARGURA - 240, centro=True)
        self.btn_fugir.desenhar(surf, f["titulo"])
        self.btn_sobrecarga.desenhar(surf, f["titulo"])
        desenhar_paragrafo(surf, "Lançar a cápsula agora e deixar a estação para trás, com o organismo lacrado.",
                           f["peq"], CINZA, self.btn_fugir.rect.x + 20, self.btn_fugir.rect.y + 60, 360, centro=True)
        desenhar_paragrafo(surf, "Aplicar toda a energia ao núcleo para destruir o organismo, e fugir no último segundo.",
                           f["peq"], CINZA, self.btn_sobrecarga.rect.x + 20, self.btn_sobrecarga.rect.y + 60, 360, centro=True)
        desenhar_texto(surf, "Escolha com [1] ou [2], ou clique em uma opção", f["peq"], CINZA, (LARGURA // 2, 520), centro=True)

    def desenhar_vitoria(self, surf):
        self.desenhar_fundo_menu(surf)
        f = self.fontes
        self.aneis.fill((0, 0, 0, 0))                               # raios de luz
        for k in range(5):
            x = 140 + k * 190 + math.sin(self.t * 0.5 + k) * 25
            pygame.draw.polygon(self.aneis, (255, 255, 220, 22),
                                [(x - 25, 0), (x + 25, 0), (x + 120, ALTURA), (x + 30, ALTURA)])
        surf.blit(self.aneis, (0, 0))
        for x, y, vx, vy, vida, cor in self.fogos:                  # brilhos
            pygame.draw.circle(surf, cor, (int(x), int(y)), 3 if vida > 0.5 else 2)
        titulo, corpo = FINAIS[self.final_escolhido]
        pulso = 1 + 0.04 * math.sin(self.t * 3)
        img = render_texto("VITÓRIA!", f["gigante"], VERDE)
        img = pygame.transform.smoothscale(img, (int(img.get_width() * pulso), int(img.get_height() * pulso)))
        surf.blit(img, img.get_rect(midtop=(LARGURA // 2, 12)))
        desenhar_texto(surf, titulo, f["grande"], AMARELO, (LARGURA // 2, 80), centro=True)
        y = desenhar_paragrafo(surf, corpo, f["texto"], BRANCO, 110, 128, LARGURA - 220, espaco=2, centro=True)
        desenhar_paragrafo(surf, EPILOGOS[self.final_escolhido], f["peq"], (180, 205, 220), 150, y + 6,
                           LARGURA - 300, espaco=2, centro=True)
        # estatísticas
        letra, rotulo, cor, pontos = self.classificacao()
        r = pygame.Rect(80, 296, 540, 210)
        painel(surf, r, borda=VERDE)
        t = max(0, int(self.tempo))
        gasto = TEMPO_TOTAL - t
        linhas = [("Acertos", f"{self.acertos_total}/{TOTAL_ACERTOS}"),
                  ("Falhas críticas", f"{self.erros}/{MAX_ERROS}"),
                  ("Tempo restante", f"{t // 60:02d}:{t % 60:02d}"),
                  ("Tempo usado", f"{gasto // 60:02d}:{gasto % 60:02d}"),
                  ("Pontuação", f"{pontos}")]
        for i, (k, v) in enumerate(linhas):
            yy = r.y + 16 + i * 37
            desenhar_texto(surf, k, f["titulo"], CINZA, (r.x + 30, yy))
            img = render_texto(v, f["titulo"], AMARELO if k == "Pontuação" else BRANCO)
            surf.blit(img, img.get_rect(topright=(r.right - 30, yy)))
        # classificação
        rc = pygame.Rect(644, 296, 300, 210)
        painel(surf, rc, borda=cor)
        desenhar_texto(surf, "CLASSIFICAÇÃO", f["hud_l"], CINZA, (rc.centerx, rc.y + 14), centro=True)
        centro = (rc.centerx, rc.y + 94)
        pygame.draw.circle(surf, (10, 20, 32), centro, 52)
        pygame.draw.circle(surf, cor, centro, 52, 4)
        img = render_texto(letra, f["gigante"], cor)
        surf.blit(img, img.get_rect(center=centro))
        desenhar_paragrafo(surf, rotulo, f["titulo"], BRANCO, rc.x + 10, rc.y + 156, rc.width - 20, espaco=0, centro=True)
        self.btn_novo.desenhar(surf, f["titulo"])
        desenhar_texto(surf, "Protocolo Cronos · Projeto 2 - Escape Room de Análise Combinatória · Obrigado por jogar!",
                       f["peq"], CINZA, (LARGURA // 2, 604), centro=True)

    def desenhar_fim(self, surf):
        if self.estado == VITORIA:
            self.desenhar_vitoria(surf)
            return
        self.desenhar_fundo_menu(surf)
        f = self.fontes
        venceu = self.estado == VITORIA
        if venceu:
            titulo, corpo = FINAIS[self.final_escolhido]
            desenhar_texto(surf, "VITÓRIA!", f["gigante"], VERDE, (LARGURA // 2, 36), centro=True)
            desenhar_texto(surf, titulo, f["grande"], AMARELO, (LARGURA // 2, 106), centro=True)
        else:
            corpo = self.motivo_derrota
            desenhar_texto(surf, "DERROTA", f["gigante"], VERMELHO, (LARGURA // 2, 36), centro=True)
            desenhar_texto(surf, "Protocolo Cronos falhou", f["grande"], AMARELO, (LARGURA // 2, 106), centro=True)
        desenhar_paragrafo(surf, corpo, f["texto"], BRANCO, 130, 170, LARGURA - 260, centro=True)
        r = pygame.Rect(LARGURA // 2 - 260, 330, 520, 170)
        painel(surf, r, borda=VERDE if venceu else VERMELHO)
        t = max(0, int(self.tempo))
        gasto = TEMPO_TOTAL - t
        linhas = [f"Acertos: {self.acertos_total}/{TOTAL_ACERTOS}",
                  f"Fase alcançada: {self.fase_idx + 1}/{len(FASES)}",
                  f"Erros: {self.erros}/{MAX_ERROS}",
                  f"Tempo restante: {t // 60:02d}:{t % 60:02d}   (usado: {gasto // 60:02d}:{gasto % 60:02d})"]
        for i, l in enumerate(linhas):
            desenhar_texto(surf, l, f["titulo"], BRANCO, (r.x + 30, r.y + 18 + i * 36))
        self.btn_novo.desenhar(surf, f["titulo"])

    def desenhar(self):
        if self.estado == MENU:
            self.desenhar_menu(self.tela)
        elif self.estado == INTRO:
            self.desenhar_intro(self.tela)
        elif self.estado == JOGANDO:
            self.desenhar_jogo()
        elif self.estado == ESCOLHA_FINAL:
            self.desenhar_escolha(self.tela)
        elif self.estado == CINEMA:
            self.desenhar_cinema(self.tela)
        else:
            self.desenhar_fim(self.tela)
        self.desenhar_botoes_sistema(self.tela)
        self.compor_tela()
        pygame.display.flip()

    def compor_tela(self):
        """Põe o jogo (1024x640) no centro da tela real e desenha os controles de toque por cima/ao lado."""
        d = self.display
        if self.ox:
            d.fill((4, 9, 16))
            pygame.draw.line(d, (30, 70, 90), (self.ox - 1, 0), (self.ox - 1, ALTURA), 2)
            pygame.draw.line(d, (30, 70, 90), (self.ox + LARGURA, 0), (self.ox + LARGURA, ALTURA), 2)
        d.blit(self.tela, (self.ox, 0))
        jogando_livre = self.estado == JOGANDO and not (self.desafio or self.notas.aberto or self.pausado)
        if self.toque.ativo and jogando_livre:
            self.toque.desenhar(d, self.fontes, getattr(self, "_perto_terminal", False))
        if self.retrato and self.toque.ativo:
            d.blit(self.veu(200), (self.ox, 0))
            desenhar_texto(d, "Gire o celular", self.fontes["gigante"], CIANO, (d.get_width() // 2, 230), centro=True)
            desenhar_texto(d, "O jogo funciona na horizontal.", self.fontes["titulo"], BRANCO,
                           (d.get_width() // 2, 310), centro=True)

    # ------------------------------------------------------------ laço principal
    async def executar(self):
        """Laço assíncrono: o mesmo código roda no PC e no navegador (pygbag/WebAssembly)."""
        while self.rodando:
            inicio = time.perf_counter()
            if EH_WEB:
                # No navegador, tick(FPS) espera "girando" a CPU na mesma thread que alimenta o
                # áudio, e o som picota. Aqui só medimos o tempo; quem espera é o asyncio, abaixo.
                dt = min(self.relogio.tick() / 1000.0, 0.1)
            else:
                dt = min(self.relogio.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                self.tratar_evento(e)
            self.atualizar(dt)
            self.desenhar()
            if EH_WEB:
                # devolve o controle ao navegador pelo resto do quadro (o áudio roda nesse intervalo)
                sobra = 1.0 / FPS - (time.perf_counter() - inicio)
                await asyncio.sleep(max(0.0, sobra))
            else:
                await asyncio.sleep(0)
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(Jogo().executar())
