# A Cidade dos Seguidores — projeto

Manda este zip de volta em cada episódio novo, junto com o número de seguidores (e o nome da vila, se já tiver).

**Episódio 9: leia primeiro o `RELATORIO_PARA_EP9.md`** (780 seguidores, casas 73–78, rua F começa, padaria/lanchonete no 800 faltando 20, 68 moradores com nome, 14 candidatos a prefeito, Enzo Mildana em destaque).

**Ep. 9 pronto** (780 seguidores, 32 bits): o mercadinho do centro pegou fogo (e foi reformado) → fundado o **CORPO DE BOMBEIROS** (lote 206,600,a); casas 73–78 (rua E fechou, rua F começou); **PETSHOP** (lote 16,600,a) e bicharada solta; campeonato no campo; eleição com 14 candidatos e **votação aberta**; destaque Enzo Mildana; **terreno da padaria reservado** (marco 800, lote 16,600,b, ponto `padaria`). Tempos da narração em `codigo/tempos_ep9.py`. Código do ep. 8 em `arquivo_ep8/`. Próxima: casa 79 (785→790, lote 140,600,a). ⚠️ Casas 88+ precisam de lotes novos.

**Ep. 8 pronto** (721 seguidores), em 32 bits: casas 65–72 na rua E, **MARCO 700: CAMPO DE FUTEBOL** (lotes 140|162|184|206,600,b, ponto `campo` no `vila.json`), o time (cristiano Ronaldo, Mesi, Neymar, Ronaldo gaucho, DEUS, Theogoleiro, Murilo mbappe), gol, vira-lata, o fazendeiro vizinho (fora do mapa, oeste), mural dos 11 candidatos, debate no chat. Próxima: casa 73 (725→730, lote 206,510,a). Próximo marco: 800 (padaria/lanchonete). Código do ep. 7 em `arquivo_ep7/`. O teste "tudo em blocos" (cancelado) ficou em `arquivo_ep8_blocos/vox.py` (o `codigo/vox.py` só é usado pra medida do campo). A narração final é mais rápida que a linha do tempo de trabalho: `scene.TMAP` / `new2old()` convertem os tempos.

**Ep. 7 pronto** (647 seguidores): a cidade se chama **PINDAMONHANGABA** (pórtico sobre a rua principal, feito em mutirão), EVOLUÇÃO 32 BITS (`iso.K = 2`, casas com varanda/jardim/varal, árvores detalhadas, moradores novos em 32x48 no `char32.py`), casas 62–64, montagem das novidades do site, candidaturas a prefeito, teaser de profissões/dinheiro. Próxima: casa 65 (645→650). Próximo marco: 700 (campo).

## Pastas
- `codigo/` — motor do vídeo (Python + Pillow + ffmpeg).
  - `scene.py` — **linha do tempo do episódio** (dicionário `T`), contador, câmera, morador em destaque.
  - `world16.py` — sprites 16 bits (chão, rio, casas, mercadinho, igreja, árvores) e o **gerador de moradores** (`npc_look(id)`: aparência fixa por id).
  - `vila16.py` — monta a vila 16 bits a cada quadro (máx. 50 moradores desenhados, dia/noite).
  - `iso.py` — motor ISOMÉTRICO (ep. 6+): sprites em cache, terreno infinito em volta, `render_view(t, cam, moradores)`. `iso.K = 2` = 32 bits (ep. 7+).
  - `char32.py` — moradores 32 bits (32x48): `npc32(look, direção, quadro)` com o mesmo `look` do site.
    Ep. 7 (site): opções novas no `look` — cabelo moicano/trancas/cacheado/topete, chapéu boina/coroa/bandana,
    estampa xadrez/time, `acessorio` (mochila, cachecol, colar, fone, oculos_sol) + `cor_acessorio`. Corrigido: o cabelo
    'longo' cobria o rosto. Se mexer no desenho, rode `gerar_formas32.py` (o `exportar_site.py` já roda no fim).
  - `gerar_formas32.py` — grava as formas do char32 em `site/js/formas32.js` (o site desenha os moradores igual ao vídeo).
  - `fp.py` — visão em primeira pessoa (pseudo-3D) usada no ep. 4.
  - `vila8.py`, `world.py` — vila em 8 bits (eps. 1 e 2).
  - `render.py` — textos na tela, transições e o quadro final 1080x1920.
  - `audio.py` — música chiptune + efeitos. `make.py` — gera o vídeo.
  - `exportar_site.py` — gera `site/img` e `site/dados` com a vila atual.
- `site/` — tudo pro site: `SITE_ESPEC.md` (como programar + SQL do Supabase), mapa, atlas dos moradores, JSONs.
- `estado_vila.json` — números atuais, construções e próximos marcos.
- `arquivo_ep1/` … `arquivo_ep6/` — código dos episódios anteriores (só consulta).
- `dados_do_site/registrados.json` — nomes e visuais escolhidos no site (o vídeo usa).
- `ROTEIRO_EP*.md`, `referencia_*.png` — roteiros e como a vila ficou em cada episódio.

## Gerar um episódio
```
cd codigo
python3 audio.py bg.wav
python3 make.py 0 <segundos*30> video_mudo.mp4
ffmpeg -i video_mudo.mp4 -i bg.wav -i ../narracao_ep7.wav -filter_complex "[2:a]aresample=44100,volume=1.5,asplit=2[n1][n2];[1:a]volume=0.8[bg];[bg][n1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[bgd];[bgd][n2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k final.mp4
python3 exportar_site.py ../site
```
