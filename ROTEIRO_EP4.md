# A Cidade dos Seguidores — Episódio 4 (roteiro)
~85 s · 370 → 460 seguidores · marco 400: ESCOLA · o mapa lota e a vila abre a rua D · sábado de mercadinho

| # | Tempo | Narração (IA de voz) | Na tela |
|---|---|---|---|
| 1 | 0–4 | A Cidade dos Seguidores... episódio 4! | Título, vila 16 bits como terminou no ep. 3 |
| 2 | 4–8,5 | Da última vez, a vila tinha 370 moradores e 37 casas. | "ATÉ AGORA: 370 MORADORES / 37 CASAS" |
| 3 | 8,5–13,5 | E vocês continuaram chegando: casa 38, casa 39, casa 40... | Contador 370 → 400, casas 38–40 subindo na rua C |
| 4 | 13,5–17 | Até que o contador bateu quatrocentos... | "QUASE..." 395 → 400 · "400!" + "NOVO MARCO DESBLOQUEADO" |
| 5 | 17–25 | ...e a vila ganhou a ESCOLA! Fundação, parede, telhado... o sino lá em cima e a bandeira na frente. | Obra nos 2 lotes reservados da rua C, etapas → "ABERTA!" |
| 6 | 25–29,5 | E todo dia de manhã, o sino toca e o pátio enche. | **Primeira pessoa (~4 s):** câmera desce do mapa pro chão e "anda" pela rua C em perspectiva (estilo jogo antigo de corrida), casas dos lados, a escola passa pela direita com o sino tocando ("DING!") e moradores entrando no pátio, relógio 07:30 → volta pra visão de cima |
| 7 | 29,5–36 | De 400 pra 460, não parou mais: seis casas novas, uma atrás da outra. | Contador 400 → 460, casas 41–46 nascendo, câmera percorrendo a rua C |
| 8 | 36–42 | Só que aí... a casa 46 ficou pronta, e não sobrou nenhum lote. | Lotes piscando até todos ocupados · "MAPA LOTADO!" |
| 9 | 42–51 | Então os pedreiros pegaram aquela pilha de madeira que tava na entrada desde o episódio 1... e abriram uma rua nova! | Pilha de madeira encolhendo, rua D traçada abaixo da rua A, estacas nos lotes · "RUA NOVA!" |
| 10 | 51–55 | É lá que vai nascer a casa 47. | Primeiro lote da rua D com "465 → 470" |
| 11 | 55–59,5 | E hoje é sábado... e sábado na vila é dia de quê? | Relógio "SÁB 09:00", portas das casas abrindo |
| 12 | 59,5–68 | De mercadinho! A vila inteira desce pra lá: fila no caixa, sacola cheia... e a vendinha do lado tentando pegar algum cliente. | Moradores (com os nomes do site em cima, se aparecerem) indo pro mercadinho, fila na porta, saindo com sacola · vendinha vazia com "PROMOÇÃO!" |
| 13 | 68–73 | Resultado: 460 moradores, 46 casas, uma escola e uma rua nova. | Resumo em 4 banners |
| 14 | 73–77 | Faltam só 40 pra 500... e aí a vila ganha a prefeitura e as ruas calçadas! | Lote cercado com "500" + prévia de rua calçada |
| 15 | 77–81 | E a placa da entrada continua em branco. Qual vai ser o nome da vila? Comenta aí! | Placa vazia "???" · "COMENTA O NOME!" |
| 16 | 81–85 | Entra no link da bio, escolhe o teu morador, e vira parte da vila! | "LINK NA BIO! VIRA MORADOR" |

**Se a vila já tiver nome na hora de gravar**, troca a fala 15 por:
> E a vila finalmente tem nome: [NOME], escolhido por vocês nos comentários!

## Texto corrido (pra colar na IA de voz)
A Cidade dos Seguidores... episódio 4!
Da última vez, a vila tinha 370 moradores e 37 casas.
E vocês continuaram chegando: casa 38, casa 39, casa 40...
Até que o contador bateu quatrocentos...
...e a vila ganhou a ESCOLA! Fundação, parede, telhado... o sino lá em cima e a bandeira na frente.
E todo dia de manhã, o sino toca e o pátio enche.
De 400 pra 460, não parou mais: seis casas novas, uma atrás da outra.
Só que aí... a casa 46 ficou pronta, e não sobrou nenhum lote.
Então os pedreiros pegaram aquela pilha de madeira que tava na entrada desde o episódio 1... e abriram uma rua nova!
É lá que vai nascer a casa 47.
E hoje é sábado... e sábado na vila é dia de quê?
De mercadinho! A vila inteira desce pra lá: fila no caixa, sacola cheia... e a vendinha do lado tentando pegar algum cliente.
Resultado: 460 moradores, 46 casas, uma escola e uma rua nova.
Faltam só 40 pra 500... e aí a vila ganha a prefeitura e as ruas calçadas!
E a placa da entrada continua em branco. Qual vai ser o nome da vila? Comenta aí!
Entra no link da bio, escolhe o teu morador, e vira parte da vila!

## Notas de produção
- **Nenhum morador citado na narração.** Os nomes registrados no site podem aparecer em cima dos bonecos na cena do mercadinho (só o nome, nunca o @, visual do `registrados.json`).
- **Contador:** 370 → 400 nas falas 3–4, 400 → 460 na fala 7. Termina em 460.
- **Escola:** lotes `(162, ROADC, 'a')` e `(184, ROADC, 'a')`.
- **Rua D:** abaixo da rua A, onde hoje fica a pilha de madeira. Lotes novos no fim da lista `lots`; lotes antigos não mudam de ordem.
- **Sábado:** todos os moradores desenhados seguem pro mercadinho (lote `162, ROADB, 'a'`), fila na porta, saem com sacola.
- **Moradores novos #371–#460:** `npc_look(id)` normal, `chegou_no_ep = 4`.
