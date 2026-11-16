# Gera site/js/formas32.js: a forma EXATA (pixels) de cada elipse/arco/corda/polígono/linha/
# retângulo arredondado que o char32.py pode desenhar, pra o site desenhar os moradores 32 bits
# pixel por pixel igual ao vídeo (o desenho dessas formas no Pillow é difícil de copiar no JS).
#   python3 gerar_formas32.py ../site/js/formas32.js
# Rode de novo sempre que mexer no desenho do char32.py.
import sys, json, random
from PIL import Image, ImageDraw
import char32
from world16 import npc_look

saida = sys.argv[1] if len(sys.argv) > 1 else '../site/js/formas32.js'
W, H = char32.W32, char32.H32
FORMAS = {}

def chave(tipo, nums):
    return tipo + ':' + ','.join(str(int(n)) for n in nums)
def achata(xy):
    out = []
    for p in xy:
        if isinstance(p, (tuple, list)): out += list(p)
        else: out.append(p)
    return out
def mascara(fn):
    m = Image.new('L', (W, H), 0); fn(_draw_original(m))      # o Draw original (o do char32 está trocado pelo Gravador)
    px = m.load(); idx = [y*W+x for y in range(H) for x in range(W) if px[x, y]]
    runs = []                                   # [início, tamanho, início, tamanho, ...]
    for i in idx:
        if runs and runs[-2] + runs[-1] == i: runs[-1] += 1
        else: runs += [i, 1]
    return runs
def registra(k, fn):
    if k not in FORMAS: FORMAS[k] = mascara(fn)

class Gravador:
    """Desenha de verdade (pro char32 funcionar igual) e grava a forma de cada chamada."""
    def __init__(self, real): self.r = real
    def point(self, xy, fill=None): return self.r.point(xy, fill=fill)
    def rectangle(self, xy, fill=None, outline=None, width=1):
        if outline is not None and fill is None:
            registra(chave('o', achata(xy)), lambda d: d.rectangle(xy, outline=255))
        return self.r.rectangle(xy, fill=fill, outline=outline)
    def ellipse(self, xy, fill=None):
        registra(chave('e', achata(xy)), lambda d: d.ellipse(xy, fill=255)); return self.r.ellipse(xy, fill=fill)
    def chord(self, xy, start, end, fill=None):
        registra(chave('c', achata(xy) + [start, end]), lambda d: d.chord(xy, start, end, fill=255)); return self.r.chord(xy, start, end, fill=fill)
    def arc(self, xy, start, end, fill=None):
        registra(chave('a', achata(xy) + [start, end]), lambda d: d.arc(xy, start, end, fill=255)); return self.r.arc(xy, start, end, fill=fill)
    def rounded_rectangle(self, xy, radius=0, fill=None):
        registra(chave('r', achata(xy) + [radius]), lambda d: d.rounded_rectangle(xy, radius=radius, fill=255)); return self.r.rounded_rectangle(xy, radius=radius, fill=fill)
    def polygon(self, xy, fill=None):
        registra(chave('p', achata(xy)), lambda d: d.polygon(xy, fill=255)); return self.r.polygon(xy, fill=fill)
    def line(self, xy, fill=None, width=1):
        registra(chave('l', achata(xy)), lambda d: d.line(xy, fill=255)); return self.r.line(xy, fill=fill)

_draw_original = ImageDraw.Draw
char32.ImageDraw.Draw = lambda im, *a, **k: Gravador(_draw_original(im, *a, **k))

OPCOES = {
    'cabelo': ['curto', 'raspado', 'longo', 'rabo', 'coque', 'afro', 'careca', 'franja', 'moicano', 'trancas', 'cacheado', 'topete'],
    'chapeu': [None, 'bone', 'palha', 'gorro', 'boina', 'coroa', 'bandana'],
    'estampa': ['lisa', 'listrada', 'regata', 'duas_cores', 'xadrez', 'time'],
    'baixo': ['calca', 'bermuda', 'saia', 'vestido'],
    'acessorio': [None, 'mochila', 'cachecol', 'colar', 'fone', 'oculos_sol'],
    'oculos': [False, True], 'barba': [False, True],
}
base = dict(npc_look(1)); base.update(acessorio=None, cor_acessorio=0)
vistos = 0
def roda(lk):
    global vistos
    for d in ('down', 'right', 'up'):
        for fr in range(4): char32.npc32(lk, d, fr); vistos += 1
for campo, vals in OPCOES.items():                 # uma opção de cada vez
    for v in vals: roda(dict(base, **{campo: v}))
r = random.Random(7)                               # e combinações sorteadas, pra garantir
for _ in range(1500):
    lk = dict(base)
    for campo, vals in OPCOES.items(): lk[campo] = r.choice(vals)
    roda(lk)

with open(saida, 'w', encoding='utf-8') as f:
    f.write('// Gerado por codigo/gerar_formas32.py — não edite à mão. Formas exatas do char32.py (Pillow)\n')
    f.write('// chave "tipo:números" -> pixels em pares [início, tamanho] (índice = y*32 + x)\n')
    f.write('(function (r) { const F = ' + json.dumps(FORMAS, separators=(',', ':')) + ';\n')
    f.write("  if (typeof module !== 'undefined') module.exports = F; else r.FORMAS32 = F; })(this);\n")
print(len(FORMAS), 'formas,', vistos, 'desenhos ->', saida)
