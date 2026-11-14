# Relatório para o Episódio 4 — A Cidade dos Seguidores

Levantado em **14/11/2026 às 18:52 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 3 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 370 | **460** |
| Casas prontas | 37 | **46** (casas 38 a 46 são novas) |
| Moradores novos | — | **#371 a #460** (90 moradores) |
| Próxima obra | casa 38 (375) | casa 47 começa com 465 e fica pronta com 470 |

- **Marco 400 — ESCOLA: atingido.** Lotes já reservados na rua C: `(162, ROADC, 'a')` e `(184, ROADC, 'a')` (ver `ESCOLA` em `codigo/scene.py`).
- **Próximo marco: 500 — prefeitura + ruas calçadas** (faltam 40). Depois: 600 = 2º mercadinho + posto de saúde.
- **Nome da vila:** ainda sem nome (placa da entrada vazia).

## 2. ⚠️ O mapa lota neste episódio

O mapa atual tem **50 lotes**: 4 já são vendinha, mercadinho e escola (2 lotes), sobrando **46 para casas**.
Com 460 inscritos as 46 casas ficam prontas → **não sobra lote para a casa 47** (obra em 465) nem para a
prefeitura (500) e o 2º mercadinho (600).

**O ep. 4 precisa abrir espaço** — sugestão: uma rua D nova (abaixo da rua A, entre ela e a entrada, ou acima
da rua C), com novos lotes no fim da lista `lots` de `scene.py`. Os lotes antigos **não podem mudar de ordem**:
a casa N e os moradores dela (10×N−9 a 10×N) ficam sempre no mesmo lugar, e o site depende disso.

## 3. O que aconteceu no site desde o ep. 3

O site entrou no ar com: mapa ao vivo, registro de morador, personalização do visual, amizades, contador de
inscritos ao vivo, bio de uma frase e pedidos de amizade.

**17 moradores já têm dono** (nome que aparece no boneco):

| # | Nome | Casa | Chegou no ep. | Visual personalizado |
|---|---|---|---|---|
| 6 | Luiz | 1 | 1 | sim |
| 11 | Isabely67 | 2 | 1 | sim |
| 24 | Alyce | 3 | 1 | sim |
| 34 | Gabrielplay | 4 | 1 | sim |
| 67 | Kira | 7 | 1 | sim |
| 83 | Poly | 9 | 1 | sim |
| 88 | Broch | 9 | 1 | sim |
| 150 | Joe Keffyler | 15 | 1 | sim |
| 154 | Wesley | 16 | 1 | sim |
| 171 | Greninjapok09 | 18 | 1 | sim |
| 181 | Victor | 19 | 1 | não |
| 193 | Guilherme | 20 | 1 | sim |
| 212 | Pietro | 22 | 1 | sim |
| 229 | Pedro | 23 | 1 | sim |
| 302 | Arthur | 31 | 2 | sim |
| 322 | Rafael | 33 | 3 | não |
| 347 | João Guilherme | 35 | 3 | sim |

O visual de cada um está em `dados_do_site/registrados.json`, **no mesmo formato do `npc_look()`** —
dá pra passar direto para `npc_sprite(look, dir, frame)` e desenhar no vídeo como a pessoa escolheu.
Mostrar só o **nome** (nunca o @).

**Amizades:**
- **Isabely67 ★ Guilherme** — amizade mútua
- **Alyce ★ Isabely67** — amizade mútua
- Pedro adicionou Guilherme · Victor adicionou Alyce
- **João Guilherme adicionou 10 vizinhos** (Luiz, Alyce, Gabrielplay, Broch, Joe Keffyler, Greninjapok09,
  Victor, Arthur, Rafael e o #349) — ninguém adicionou de volta ainda

**Pela rotina da vila:** Isabely67, Alyce e Guilherme se encontram **na praça por volta de 12h20 todos os dias**
(7 de 7 dias na semana) — é o "trio da praça".

## 4. Morador em destaque (1 frase)

> **João Guilherme (#347, casa 35):** "Chegou no episódio 3 e já mandou pedido de amizade pra 10 vizinhos… e
> ainda tá esperando alguém aceitar."

Alternativa: *"Todo dia, 12h20, Isabely67 encontra a Alyce e o Guilherme na praça — o trio mais fiel da vila."*

## 5. Regras pra não quebrar o site

1. Moradores #1 a #370 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #371 a #460 usam
   `npc_look(id)` normal e `chegou_no_ep = 4`.
2. Lotes antigos não mudam de lugar nem de ordem; lotes novos entram **no fim** da lista.
3. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`).
4. Atualizar `estado_vila.json` (seguidores, casas, construções, marcos, lotes novos, episódio).
5. Devolver a pasta inteira do projeto (com `codigo/`, `site/`, `estado_vila.json`, roteiro e referência).

## 6. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores. Lê o LEIA-ME, o estado_vila.json e o
> RELATORIO_PARA_EP4.md. Agora tenho **460 seguidores** e a vila ainda não tem nome. Quero o **episódio 4**:
> primeiro o roteiro, depois o vídeo. Tem que ter a **escola** (marco 400), as **casas 38 a 46**, a abertura
> de uma **rua nova** porque o mapa lotou, e o morador em destaque do relatório. No fim roda o
> exportar_site.py e me devolve o projeto inteiro.
