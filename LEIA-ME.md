# A Cidade dos Seguidores — projeto

Manda este zip de volta em cada episódio novo, junto com o número de seguidores (e o nome da vila, se já tiver).

## Pastas
- `codigo/` — motor do vídeo (Python + Pillow + ffmpeg).
  - `scene.py` — **linha do tempo do episódio** (dicionário `T`), contador, câmera, morador em destaque.
  - `world16.py` — sprites 16 bits (chão, rio, casas, mercadinho, igreja, árvores) e o **gerador de moradores** (`npc_look(id)`: aparência fixa por id).
  - `vila16.py` — monta a vila 16 bits a cada quadro (máx. 50 moradores desenhados, dia/noite).
  - `vila8.py`, `world.py` — vila em 8 bits (eps. 1 e 2, usada no recap).
  - `render.py` — textos na tela, transições e o quadro final 1080x1920.
  - `audio.py` — música chiptune + efeitos. `make.py` — gera o vídeo.
  - `exportar_site.py` — gera `site/img` e `site/dados` com a vila atual.
- `site/` — tudo pro site: `SITE_ESPEC.md` (como programar + SQL do Supabase), mapa, atlas dos moradores, JSONs.
- `estado_vila.json` — números atuais, construções e próximos marcos.
- `arquivo_ep1/`, `arquivo_ep2/` — linhas do tempo dos episódios anteriores (só consulta).
- `ROTEIRO_EP*.md`, `referencia_*.png` — roteiros e como a vila ficou em cada episódio.

## Gerar um episódio
```
cd codigo
python3 audio.py bg.wav
python3 make.py 0 <segundos*30> video_mudo.mp4
# mixar com a narração (ffmpeg) — ver comando no histórico do ep. 3
python3 exportar_site.py ../site
```
