# A Cidade dos Seguidores — Episódio 5 (roteiro)
~88 s · 460 → 577 seguidores · marco 500: PREFEITURA + RUAS CALÇADAS (vira cidadezinha) · casas 47–57 na rua D · domingo de show na praça

| # | Tempo | Narração (IA de voz) | Na tela |
|---|---|---|---|
| 1 | 0–4 | A Cidade dos Seguidores... episódio 5! | Título, vila como terminou no ep. 4 |
| 2 | 4–9 | Da última vez, eram 460 moradores, 46 casas... e uma rua nova esperando gente. | "ATÉ AGORA: 460 / 46 CASAS", câmera na rua D vazia com as estacas |
| 3 | 9–14 | E a rua D encheu rapidinho: casa 47, 48, 49... uma atrás da outra. | Contador 460 → 495, casas 47–49 subindo na rua D |
| 4 | 14–18 | Até que o contador chegou em 500... | "QUASE..." 495 → 500 · "500!" + "NOVO MARCO DESBLOQUEADO" |
| 5 | 18–27 | ...e a vila ganhou a PREFEITURA! Fundação, colunas, o relógio lá no alto... e as bandeiras na frente. | Obra nos 2 lotes reservados da rua D, ao lado da entrada · chips FUNDAÇÃO / COLUNAS / RELÓGIO / BANDEIRAS |
| 6 | 27–33 | E não parou por aí: as ruas de terra viraram paralelepípedo, com calçada e tudo! | Calçamento varrendo as ruas a partir da prefeitura (terra → pedra), poeira |
| 7 | 33–37 | A vila agora é oficialmente uma cidadezinha! | Câmera abre no mapa inteiro calçado · "CIDADEZINHA!" com confete |
| 8 | 37–43 | Depois disso, mais sete casas na rua D... e a casa 58 já tá em obra. | Contador 500 → 577, casas 51–57 · casa 58 com pedreiros ("575 → 580") |
| 9 | 43–51 | E a prefeitura não vai ficar vazia: em breve a cidade vai ter prefeito... e o nome da cidade também sai logo. Fica atento! | Zoom na prefeitura, cadeira vazia/porta com "?" · "EM BREVE: PREFEITO" · placa da entrada "???" · "FICA ATENTO!" |
| 10 | 51–55 | E hoje é domingo... e domingo é dia de show na praça! | Céu escurecendo, relógio "DOM 19:00", luzes acendendo |
| 11 | 55–64 | Palco montado, banda tocando, luz colorida... e a cidade inteira dançando até o fim do show. | Palco na praça com banda (16 bits), holofotes coloridos, multidão pulando, notas musicais |
| 12 | 64–70 | Resultado: 577 moradores, 57 casas, prefeitura e ruas calçadas. | Resumo em 4 banners |
| 13 | 70–75 | Faltam só 23 pra 600: segundo mercadinho e posto de saúde! | "FALTAM SÓ 23" · prévia dos 2 prédios |
| 14 | 75–80 | Só que a rua D tá quase cheia... e a cidade vai ter que crescer pra fora do mapa. | Lotes livres piscando (só 3) · câmera "esbarra" na borda do mapa · "???" |
| 15 | 80–88 | Entra no link da bio e escolhe o teu morador... quem sabe o primeiro prefeito não é você? | "LINK NA BIO!" · "VIRA MORADOR" · faixa "PREFEITO: VOCÊ?" |

**Se no dia de gravar já tiver passado de 600**, troca as falas 12 e 13 por:
> Resultado: [N] moradores, [N/10] casas, prefeitura, ruas calçadas... e passou de 600: vem aí o segundo mercadinho e o posto de saúde!

**Opcional (morador em destaque do relatório)** — entra depois da fala 11, se quiser citar alguém:
> E no meio do show, a Dona Joana já tinha mandado pedido de amizade pra 58 vizinhos... pra ela, a cidade inteira é neto.

## Texto corrido (pra colar na IA de voz)
A Cidade dos Seguidores... episódio 5!
Da última vez, eram 460 moradores, 46 casas... e uma rua nova esperando gente.
E a rua D encheu rapidinho: casa 47, 48, 49... uma atrás da outra.
Até que o contador chegou em 500...
...e a vila ganhou a PREFEITURA! Fundação, colunas, o relógio lá no alto... e as bandeiras na frente.
E não parou por aí: as ruas de terra viraram paralelepípedo, com calçada e tudo!
A vila agora é oficialmente uma cidadezinha!
Depois disso, mais sete casas na rua D... e a casa 58 já tá em obra.
E a prefeitura não vai ficar vazia: em breve a cidade vai ter prefeito... e o nome da cidade também sai logo. Fica atento!
E hoje é domingo... e domingo é dia de show na praça!
Palco montado, banda tocando, luz colorida... e a cidade inteira dançando até o fim do show.
Resultado: 577 moradores, 57 casas, prefeitura e ruas calçadas.
Faltam só 23 pra 600: segundo mercadinho e posto de saúde!
Só que a rua D tá quase cheia... e a cidade vai ter que crescer pra fora do mapa.
Entra no link da bio e escolhe o teu morador... quem sabe o primeiro prefeito não é você?

## Notas de produção
- **Prefeitura:** `prefeitura16()` em `world16.py` (2 lotes: `140,420,a` + `162,420,a`). Prédio branco com telhado de ardósia, frontão com relógio, 4 colunas, escadaria e 2 mastros com bandeira.
- **Ruas calçadas:** `make_ground16(..., paved=True)` — paralelepípedo + calçada + meio-fio. **As coordenadas das ruas não mudam** (só o desenho), então o site continua funcionando.
- **Contador:** 460 → 500 nas falas 3–4 (casas 47–50), 500 → 577 na fala 8 (casas 51–57, casa 58 em obra).
- **Show (domingo à noite):** palco na praça, moradores do site com o nome em cima na multidão (só o nome, nunca o @; "Dona Joana" sem o ♥︎). A narração não cita ninguém.
- **Moradores novos #461–#577:** `npc_look(id)` normal, `chegou_no_ep = 5`.
- **Mapa:** depois da casa 61 não tem mais lote. O marco 600 também precisa de lote → decidir pra onde a cidade cresce antes do ep. 6.
