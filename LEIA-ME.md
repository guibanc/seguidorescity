# A Cidade dos Seguidores — projeto

Manda este zip de volta em cada episódio novo, junto com o número de seguidores (e o nome da vila, se já tiver).

**Episódio 5: leia primeiro o `RELATORIO_PARA_EP5.md`** (577 seguidores, prefeitura, mapa lota em 610, 32 moradores com nome, Dona Joana em destaque).

**Ep. 5 pronto** (577 seguidores): casas 47–58 na rua D, PREFEITURA + ruas calçadas (marco 500, vira cidadezinha), teaser do prefeito e do nome, domingo à noite com show na praça. Próximo: casa 58 (575→580). Só sobram lotes das casas 59–61 (lota em 610) e o marco 600 ainda não tem lote: decidir pra onde o mapa cresce.

## Pastas
- `codigo/` — motor do vídeo (Python + Pillow + ffmpeg).
  - `scene.py` — **linha do tempo do episódio** (dicionário `T`), contador, câmera, morador em destaque.
  - `world16.py` — sprites 16 bits (chão, rio, casas, mercadinho, igreja, árvores) e o **gerador de moradores** (`npc_look(id)`: aparência fixa por id).
  - `vila16.py` — monta a vila 16 bits a cada quadro (máx. 50 moradores desenhados, dia/noite).
  - `fp.py` — visão em primeira pessoa (pseudo-3D) usada no ep. 4.
  - `vila8.py`, `world.py` — vila em 8 bits (eps. 1 e 2).
  - `render.py` — textos na tela, transições e o quadro final 1080x1920.
  - `audio.py` — música chiptune + efeitos. `make.py` — gera o vídeo.
  - `exportar_site.py` — gera `site/img` e `site/dados` com a vila atual.
- `site/` — tudo pro site: `SITE_ESPEC.md` (como programar + SQL do Supabase), mapa, atlas dos moradores, JSONs.
- `estado_vila.json` — números atuais, construções e próximos marcos.
- `arquivo_ep1/`, `arquivo_ep2/`, `arquivo_ep3/`, `arquivo_ep4/` — código dos episódios anteriores (só consulta).
- `dados_do_site/registrados.json` — nomes e visuais escolhidos no site (o vídeo usa).
- `ROTEIRO_EP*.md`, `referencia_*.png` — roteiros e como a vila ficou em cada episódio.

## Gerar um episódio
```
cd codigo
python3 audio.py bg.wav
python3 make.py 0 <segundos*30> video_mudo.mp4
ffmpeg -i video_mudo.mp4 -i bg.wav -i ../narracao_ep5.wav -filter_complex "[2:a]aresample=44100,volume=1.5,asplit=2[n1][n2];[1:a]volume=0.8[bg];[bg][n1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[bgd];[bgd][n2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k final.mp4
python3 exportar_site.py ../site
```
