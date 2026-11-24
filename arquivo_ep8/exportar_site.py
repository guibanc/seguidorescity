# Gera os arquivos que o site usa (rodar a cada episódio):
#   python3 exportar_site.py ../site
# Saída:
#   img/vila_dia.png, img/vila_noite.png   mapa 16 bits sem moradores (540x960, 2x o mapa lógico)
#   img/moradores.png                      atlas: 1 linha por morador? não: grade 10 por linha, 16 quadros 12x18 cada
#   dados/vila.json                        estado da vila, lotes, pontos (mercadinho, praça...), ruas
#   dados/moradores.json                   aparência + casa + agenda de cada morador
#   dados/novos_moradores.sql              INSERT dos moradores novos pro Supabase
import sys, os, json, random, math
from PIL import Image
from world import W, H, ROADA, ROADB, ROADC, MAINX0, MAINX1
from world16 import npc_sprite, npc_look, S
import vila16 as V
from scene import house_lots, house_var, house_p, NH, VENDA, MERCADO, ESCOLA, PREFEITURA, ROADD, ROADE, ROADF, MERCADO2, POSTO, CAMPO, MH6, lot, C1, EP, NOME_CIDADE, PLACA_X0, PLACA_X1, PLACA_Y

out = sys.argv[1] if len(sys.argv) > 1 else '../site'
os.makedirs(f'{out}/img', exist_ok=True); os.makedirs(f'{out}/dados', exist_ok=True)
N = C1

# ---------- mapa sem moradores ----------
def mapa(lit):
    base, _ = V.static_big(lit)                              # mapa de 680 (ep. 6), ruas calçadas
    img = base.copy(); objs = []
    from PIL import ImageDraw
    from world16 import posto16
    from font import draw_text
    dd = ImageDraw.Draw(img)
    # campo de futebol (marco 700, ep. 8)
    cx0, cy0 = V.L2(*lot(*CAMPO[0])); cx1 = cx0+42*4
    gx0, gy0, gx1, gy1 = cx0+6, cy0+8, cx1-6, cy0+88
    for k, fx in enumerate(range(gx0, gx1, 12)):
        dd.rectangle([fx, gy0, min(fx+11, gx1), gy1], fill=(86, 170, 70) if k % 2 == 0 else (72, 150, 58))
    W_ = (245, 245, 240); xm, ym = (gx0+gx1)//2, (gy0+gy1)//2
    dd.rectangle([gx0, gy0, gx1, gy1], outline=W_, width=2); dd.line([xm, gy0, xm, gy1], fill=W_, width=2)
    dd.ellipse([xm-16, ym-16, xm+16, ym+16], outline=W_, width=2)
    for xs, sg in ((gx0, 1), (gx1, -1)):
        dd.rectangle([min(xs, xs+sg*22), ym-22, max(xs, xs+sg*22), ym+22], outline=W_, width=2)
    for xs in (gx0-4, gx1): dd.rectangle([xs, ym-8, xs+4, ym+8], fill=(250, 250, 250))
    for r_ in range(3): dd.rectangle([gx0+8, gy1+4+r_*3, gx1-8, gy1+5+r_*3], fill=(160-r_*12, 160-r_*12, 168-r_*12))
    # pórtico PINDAMONHANGABA sobre a rua principal (ep. 7)
    px0, py0 = V.L2(110, PLACA_Y-4); px1 = px0+92
    for xx in (V.L2(PLACA_X0, 0)[0], V.L2(PLACA_X1, 0)[0]): dd.rectangle([xx-2, py0-2, xx+1, py0+14], fill=(110, 72, 40))
    dd.rectangle([px0, py0, px1, py0+11], fill=(40, 26, 16)); dd.rectangle([px0+1, py0+1, px1-1, py0+10], fill=(176, 122, 70))
    draw_text(dd, NOME_CIDADE, (px0+px1)//2+1, py0+2, 1, (255, 236, 140, 255), outline=None)
    x, y = V.L2(*lot(*POSTO[0])); objs.append((y, posto16(lit), x))                     # posto de saúde (600)
    x, y = V.L2(*lot(*MERCADO2)); objs.append((y, V.MERC(lit), x))                      # 2º mercadinho (600)
    for i, l in enumerate(house_lots):                       # lotes livres (estacas)
        if house_p(i, C1) <= 0: V.draw_stakes(dd, l)
    x, y = V.L2(*lot(*PREFEITURA[0])); objs.append((y, V.PREF(1, lit, 0), x))   # prefeitura (500)
    x, y = V.L2(*lot(*ESCOLA[0])); objs.append((y, V.ESC(1, lit, 0, 0), x))
    for i, l in enumerate(house_lots):
        p = house_p(i, C1)
        if p <= 0: continue
        x, y = V.L2(*lot(*l)); hi = V.HOUSE(house_var[i], p, lit and p >= 1)
        objs.append((y, hi, x))
    x, y = V.L2(*lot(*VENDA)); objs.append((y, V.HOUSE(5, 1, lit, True), x))
    x, y = V.L2(*lot(*MERCADO)); objs.append((y, V.MERC(lit), x))
    for y, im, x in sorted(objs, key=lambda o: o[0]): img.paste(im, (x, y), im)
    ti, (ax, ay) = V.TREE16(6, 0, 0); img.paste(ti, (153*S-ax, 231*S-ay), ti)
    return img.convert('RGB')
mapa(False).save(f'{out}/img/vila_dia.png')
# noite: mesma tinta do vídeo, janelas e postes acesos
import numpy as np
n = np.array(mapa(True)).astype(np.float32)
lm = np.zeros(n.shape[:2], bool)
from world16 import LITW
for c in LITW+[(255, 226, 130)]: lm |= (n[:, :, 0] == c[0]) & (n[:, :, 1] == c[1]) & (n[:, :, 2] == c[2])
o = n.copy(); n *= np.array([0.38, 0.45, 0.72]); n[lm] = o[lm]
Image.fromarray(np.clip(n, 0, 255).astype(np.uint8)).save(f'{out}/img/vila_noite.png')

# ---------- atlas dos moradores ----------
# cada morador ocupa uma célula de 4 direções x 4 quadros (48x72); 10 moradores por linha
DIRS = ['down', 'left', 'right', 'up']
CW, CH = 12*4, 18*4
cols = 10; rows = (N+cols-1)//cols
atlas = Image.new('RGBA', (cols*CW, rows*CH), (0, 0, 0, 0))
for k in range(N):
    look = npc_look(k+1)
    ox, oy = (k % cols)*CW, (k//cols)*CH
    for di, dr in enumerate(DIRS):
        for fr in range(4):
            s = npc_sprite(look, dr, fr)
            atlas.paste(s, (ox+fr*12, oy+di*18), s)
atlas.save(f'{out}/img/moradores.png')

# ---------- pontos da vila (coordenadas em pixels do mapa 540x960) ----------
def P(x, y): return [round(x*S), round(y*S)]
mx, my = lot(*MERCADO); vx, vy = lot(*VENDA)
pontos = {
    'mercadinho': {'porta': P(mx+10, ROADB+3), 'rua': P(mx+10, ROADB+6)},
    'vendinha': {'porta': P(vx+10, ROADB+3), 'rua': P(vx+10, ROADB+6)},
    'praca': {'centro': P(132, 245), 'bancos': [P(111, 265), P(151, 265), P(111, 221)], 'area': [P(104, 216), P(160, 274)]},
    'igreja': {'porta': P(130, 105)},
    'entrada': {'placa': P(149, 446), 'rua': P(131.5, 470)},
    'portal': {'centro': P((PLACA_X0+PLACA_X1)/2, PLACA_Y), 'de': P(PLACA_X0, PLACA_Y), 'ate': P(PLACA_X1, PLACA_Y), 'texto': NOME_CIDADE},
    'escola': {'porta': P(lot(*ESCOLA[0])[0]+21, ROADC+3), 'rua': P(lot(*ESCOLA[0])[0]+21, ROADC+6), 'lotes': [P(*lot(*l)) for l in ESCOLA]},
    'prefeitura': {'porta': P(lot(*PREFEITURA[0])[0]+21, ROADD+3), 'rua': P(lot(*PREFEITURA[0])[0]+21, ROADD+6), 'lotes': [P(*lot(*l)) for l in PREFEITURA]},
    'mercadinho2': {'porta': P(lot(*MERCADO2)[0]+9.5, ROADE+3), 'rua': P(lot(*MERCADO2)[0]+9.5, ROADE+6), 'lote': P(*lot(*MERCADO2))},
    'posto': {'porta': P(lot(*POSTO[0])[0]+21, ROADE+3), 'rua': P(lot(*POSTO[0])[0]+21, ROADE+6), 'lotes': [P(*lot(*l)) for l in POSTO]},
    'campo': {'lotes': [P(*lot(*l)) for l in CAMPO], 'marco': 700, 'gramado': [P(lot(*CAMPO[0])[0]+3, lot(*CAMPO[0])[1]+3), P(lot(*CAMPO[0])[0]+87, lot(*CAMPO[0])[1]+43)],
              'centro': P(lot(*CAMPO[0])[0]+45, lot(*CAMPO[0])[1]+23), 'gols': [P(lot(*CAMPO[0])[0]+3, lot(*CAMPO[0])[1]+23), P(lot(*CAMPO[0])[0]+87, lot(*CAMPO[0])[1]+23)],
              'arquibancada': [P(lot(*CAMPO[0])[0]+7, lot(*CAMPO[0])[1]+45), P(lot(*CAMPO[0])[0]+83, lot(*CAMPO[0])[1]+50)], 'entrada': P(lot(*CAMPO[0])[0]+45, ROADF+5)},
}
ruas = {
    'principal': {'de': P(131.5, 104), 'ate': P(131.5, 480)},
    'A': {'de': P(16, ROADA+5), 'ate': P(217, ROADA+5)},
    'B': {'de': P(16, ROADB+5), 'ate': P(217, ROADB+5)},
    'C': {'de': P(16, ROADC+5), 'ate': P(217, ROADC+5)},
    'D': {'de': P(16, ROADD+5), 'ate': P(217, ROADD+5)},
    'E': {'de': P(16, ROADE+5), 'ate': P(217, ROADE+5)},
    'F': {'de': P(16, ROADF+5), 'ate': P(217, ROADF+5)},
}
RUAS = {ROADA: 'A', ROADB: 'B', ROADC: 'C', ROADD: 'D', ROADE: 'E', ROADF: 'F'}
casas = []
for i, l in enumerate(house_lots[:NH]):
    x, y = lot(*l)
    casas.append({'casa': i+1, 'lote': P(x, y), 'tamanho': [42, 50], 'porta': P(x+10, y+22), 'rua': RUAS[l[1]],
                  'ponto_na_rua': P(x+10, l[1]+5), 'moradores': list(range(i*10+1, min(N, i*10+10)+1))})
lotes_livres = [{'casa': NH+k+1, 'lote': P(*lot(*l)), 'rua': RUAS[l[1]], 'comeca_em': 10*(NH+k)+5, 'pronta_em': 10*(NH+k+1)}
                for k, l in enumerate(house_lots[NH:])]
vila = {'episodio': EP, 'seguidores': N, 'casas': NH, 'estilo': '16 bits', 'mapa': {'largura': W*S, 'altura': MH6*S, 'escala_logica': S},
        'proximo_marco': {'seguidores': 800, 'construcao': 'padaria/lanchonete'}, 'nome_vila': 'Pindamonhangaba',
        'pontos': pontos, 'ruas': ruas, 'lista_casas': casas, 'lotes_livres': lotes_livres,
        'atlas': {'arquivo': 'img/moradores.png', 'por_linha': cols, 'celula': [CW, CH], 'quadro': [12, 18],
                  'direcoes': DIRS, 'quadros_por_direcao': 4, 'ancora_pes': [6, 14]}}
# regras e marcos (vêm do estado_vila.json) — o site mostra na tela "Como a vila cresce"
_est = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'estado_vila.json'), encoding='utf-8'))
vila['regras'] = ['1 seguidor = 1 morador', '10 seguidores = 1 casa nova (10 moradores por casa)',
                  'a obra da casa começa 5 seguidores antes de ela ficar pronta']
vila['marcos'] = [{'seguidores': int(k), 'construcao': c} for k, c in _est.get('marcos_feitos', {'300': 'mercadinho'}).items()] + \
                 [{'seguidores': int(s), 'construcao': c} for s, c in _est['proximos_marcos'].items()]
vila['proxima_casa'] = _est.get('proxima_casa')
_prox = next((m for m in vila['marcos'] if m['seguidores'] > N), None)
if _prox: vila['proximo_marco'] = {'seguidores': _prox['seguidores'], 'construcao': _prox['construcao']}
json.dump(vila, open(f'{out}/dados/vila.json', 'w'), ensure_ascii=False, indent=1)

# ---------- agenda de cada morador ----------
def hm(h):
    m = int(round(max(0, min(23.99, h))*60/5))*5
    m = min(m, 23*60+55); return f"{m//60:02d}:{m%60:02d}"
def agenda(mid):
    r = random.Random(mid*104729)
    acorda = r.uniform(5.5, 8.0)
    ag = [{'de': '00:00', 'ate': hm(acorda), 'onde': 'casa', 'faz': 'dormindo'}]
    t = acorda
    blocos = []
    # manhã: rua / praça / vendinha
    for nome, dur in (('passeio_rua', r.uniform(0.6, 2.0)), ('mercadinho', r.uniform(0.3, 0.7)), ('praca', r.uniform(0.8, 2.5))):
        blocos.append((nome, dur))
    r.shuffle(blocos)
    for nome, dur in blocos:
        t += r.uniform(0.2, 1.2)
        ag.append({'de': hm(t), 'ate': hm(t+dur), 'onde': nome, 'faz': {'passeio_rua': 'passeando', 'mercadinho': 'fazendo compras', 'praca': 'na praça'}[nome]})
        t += dur
    almoco = max(t+0.2, r.uniform(11.5, 12.8))
    ag.append({'de': hm(almoco), 'ate': hm(almoco+r.uniform(0.8, 1.5)), 'onde': 'casa', 'faz': 'almoçando'})
    t = almoco+1.6
    for nome in r.sample(['praca', 'passeio_rua', 'vendinha', 'mercadinho'], 2):
        t += r.uniform(0.3, 1.5); dur = r.uniform(0.5, 2.2)
        ag.append({'de': hm(t), 'ate': hm(t+dur), 'onde': nome, 'faz': {'passeio_rua': 'passeando', 'mercadinho': 'fazendo compras', 'praca': 'na praça', 'vendinha': 'na vendinha'}[nome]})
        t += dur
    volta = max(t+0.3, r.uniform(17.5, 20.0))
    dorme = r.uniform(21.0, 23.5)
    ag.append({'de': hm(volta), 'ate': hm(dorme), 'onde': 'casa', 'faz': 'em casa (luz acesa)'})
    ag.append({'de': hm(dorme), 'ate': '23:59', 'onde': 'casa', 'faz': 'dormindo'})
    domingo = {'de': hm(r.choice([8.5, 9.0, 18.5])), 'duracao_min': 60, 'onde': 'igreja'} if r.random() < 0.45 else None
    return ag, domingo
moradores = []
for k in range(N):
    mid = k+1
    ag, dom = agenda(mid)
    moradores.append({'id': mid, 'casa': k//10+1, 'chegou_no_ep': 1 if mid <= 267 else 2 if mid <= 320 else 3 if mid <= 370 else 4 if mid <= 460 else 5 if mid <= 577 else 6 if mid <= 617 else 7 if mid <= 647 else 8,
                      'aparencia': npc_look(mid), 'atlas': {'col': k % cols, 'lin': k//cols},
                      'velocidade': round(random.Random(mid).uniform(0.85, 1.15), 2), 'agenda': ag, 'domingo': dom})
json.dump(moradores, open(f'{out}/dados/moradores.json', 'w'), ensure_ascii=False)

# ---------- SQL dos moradores (Supabase) ----------
with open(f'{out}/dados/novos_moradores.sql', 'w') as f:
    f.write(f"-- moradores até o ep. {EP} (pode rodar de novo: ignora quem já existe)\n")
    f.write("insert into moradores (id, casa, chegou_no_ep) values\n")
    f.write(",\n".join(f"({m['id']}, {m['casa']}, {m['chegou_no_ep']})" for m in moradores))
    f.write("\non conflict (id) do nothing;\n")
print('ok', N, 'moradores', NH, 'casas')

# ---------- isométrico (ep. 6): imagem da cidade + fórmula pra posicionar moradores ----------
import iso
from scene import DUR
iso.K = 1
img_iso, (iox, ioy) = iso.imagem_completa(DUR)
img_iso.save(f'{out}/img/vila_iso.png')
iso.K = 2                                                     # ep. 7: versão 32 bits
img32, (o32x, o32y) = iso.imagem_completa(DUR)
img32.save(f'{out}/img/vila_iso_32.webp', 'WEBP', quality=92, method=6)   # 17 MB em PNG -> ~4 MB (site)
iso.K = 1
v = json.load(open(f'{out}/dados/vila.json'))
v['estilo'] = 'isométrico (ep. 6) — vila_dia.png continua valendo como mapa de cima'
v['iso'] = {'imagem': 'img/vila_iso.png', 'largura': img_iso.width, 'altura': img_iso.height,
            'origem': [iox, ioy],
            'formula': 'com (x, y) LÓGICOS (os do vila.json divididos por escala_logica): tela_x = origem[0] + (x - y) * 2 ; tela_y = origem[1] + (x + y). O pé do boneco fica nesse ponto; desenhe primeiro quem tem (x + y) menor.',
            'obs': 'imagem em pixel art: escale por inteiro (2x, 3x) com image-rendering: pixelated'}
v['iso32'] = {'imagem': 'img/vila_iso_32.webp', 'largura': img32.width, 'altura': img32.height, 'origem': [o32x, o32y], 'escala': 2,
              'formula': 'igual ao iso, com tudo vezes 2: tela_x = origem[0] + (x - y) * 4 ; tela_y = origem[1] + (x + y) * 2',
              'obs': 'visual 32 bits (ep. 7). O bloco "iso" (16 bits) continua igual pro site atual.'}
v['nome_vila'] = 'Pindamonhangaba'
json.dump(v, open(f'{out}/dados/vila.json', 'w'), ensure_ascii=False)
print('iso', img_iso.size, (iox, ioy), 'iso32', img32.size, (o32x, o32y))

# formas dos moradores 32 bits pro site (o site desenha igual ao char32.py)
import subprocess
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gerar_formas32.py'), f'{out}/js/formas32.js'], check=True)
