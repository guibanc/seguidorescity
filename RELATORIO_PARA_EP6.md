# Relatório para o Episódio 6 — A Cidade dos Seguidores

Levantado em **15/11/2026 às 16:11 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 5 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 577 | **617** |
| Casas prontas | 57 | **61** (casas 58 a 61; a 58 era a que estava em obra) |
| Moradores novos | — | **#578 a #617** (40 moradores) |
| Próxima obra | casa 58 (575 → 580) | **casa 62** (começou com 615, fica pronta com 620) — **sem lote!** |

- **Marco 600 — 2º MERCADINHO + POSTO DE SAÚDE: atingido.** Ainda **não tem lote reservado** pra eles.
- **Próximo marco: 700 — campo de futebol** (faltam 83). Depois: 800 = padaria/lanchonete.
- **Ganchos que o ep. 5 deixou:** "em breve a cidade vai ter **prefeito**", "o **nome da cidade** sai logo" e
  "a cidade vai ter que **crescer pra fora do mapa**".
- **Nome da cidade:** ainda sem nome (placa da entrada vazia).

## 2. ⚠️ O mapa está lotado — este episódio precisa aumentar o mapa

Com 617 inscritos, as casas 58 a 61 ocupam **os últimos 4 lotes** da rua D. Agora falta lugar para:
- a **casa 62** (já em obra) e as próximas (uma a cada 10 inscritos);
- o **2º mercadinho** e o **posto de saúde** (marco 600);
- o **campo de futebol** (marco 700, que ocupa bem mais que um lote).

**Regra de ouro pra crescer o mapa:** as coordenadas são medidas a partir do **canto de cima à esquerda**.
Então o mapa só pode crescer **pra baixo ou pra direita**. Se crescer pra cima ou pra esquerda, todas as
coordenadas antigas mudam e os 617 moradores do site ficam fora do lugar.
- Se o mapa mudar de tamanho, atualizar `mapa.largura` e `mapa.altura` no `vila.json` (o site já lê daí).
- Hoje o boneco controlado no site **não atravessa o rio**. Se o mapa ganhar terra do outro lado do rio, me
  avisa pra eu liberar a passagem (a **ponte** é o marco 1000).
- Lotes antigos não mudam de ordem nem de lugar; lotes novos entram **no fim** da lista.

## 3. O que aconteceu no site desde o ep. 5

**39 moradores têm dono** (eram 32). Os novos são Mounjaro (Teófilo), BLUE, Robert_LNS, Fabrício#251, C4rmin,
Miguel e **Dante (#577)**, o último morador do ep. 5, que chegou morando na casa 58 ainda em obra.

| # | Nome | Casa | Chegou no ep. | Bio |
|---|---|---|---|---|
| 1 | Heitox | 1 | 1 | |
| 2 | Didi | 1 | 1 | |
| 3 | João Pedro | 1 | 1 | |
| 6 | Luiz | 1 | 1 | |
| 7 | Mounjaro (Teófilo) | 1 | 1 | *novo* |
| 11 | Isabely67 | 2 | 1 | |
| 23 | INGRID DO GRAU | 3 | 1 | |
| 24 | Alyce | 3 | 1 | |
| 26 | BLUE | 3 | 1 | *novo* |
| 34 | Gabrielplay | 4 | 1 | |
| 45 | Gazinho | 5 | 1 | |
| 67 | Kira | 7 | 1 | "O que posso dizer além de six seven (67)? Objetivo: ser o maior farmador de aura da vila" |
| 83 | Poly | 9 | 1 | |
| 88 | Broch | 9 | 1 | |
| 150 | Joe Keffyler | 15 | 1 | |
| 154 | Wesley | 16 | 1 | |
| 168 | Mesi | 17 | 1 | |
| 171 | Greninjapok09 | 18 | 1 | |
| 181 | Victor | 19 | 1 | |
| 193 | Guilherme | 20 | 1 | "Jesus Saves - Fundador da Vila" |
| 212 | Pietro | 22 | 1 | |
| 223 | BSF_gamer01 | 23 | 1 | |
| 229 | Pedro | 23 | 1 | |
| 235 | Robert_LNS | 24 | 1 | *novo* |
| 236 | Ronaldo gaucho | 24 | 1 | |
| 251 | Fabrício#251 | 26 | 1 | *novo* — "Lugar favorito da vila: casa" |
| 258 | C4rmin | 26 | 1 | *novo* |
| 272 | Zé | 28 | 2 | |
| 281 | cristiano Ronaldo | 29 | 2 | "melhor jogador de bola na cidade pena que não tem campo" |
| 290 | ♥︎Dona Joana♥︎ | 29 | 2 | "Amiga de quase todos e considera todo mundo como neto♥︎" |
| 302 | Arthur | 31 | 2 | |
| 322 | Rafael | 33 | 3 | |
| 325 | Jean | 33 | 3 | |
| 347 | João Guilherme | 35 | 3 | |
| 348 | Neymar | 35 | 3 | |
| 412 | Dudu | 42 | 4 | |
| 441 | Theogoleiro | 45 | 4 | |
| 442 | Miguel | 45 | 4 | *novo* |
| 577 | Dante | 58 | 5 | *novo* |

Todos têm visual personalizado, menos o Rafael. O visual de cada um está em `dados_do_site/registrados.json`,
**no mesmo formato do `npc_look()`** — dá pra passar direto para `npc_sprite(look, dir, frame)`.
Mostrar só o **nome** (nunca o @). Se a fonte do vídeo não tiver ♥︎ ou #, escrever **Dona Joana** e **Fabrício**.

**Amizades: 106 pedidos enviados (eram 95), 22 amizades mútuas (eram 14).**
- A **Dona Joana** continua campeã: adicionou 58 vizinhos, e agora **9 já adicionaram ela de volta** (eram 5).
  Novos amigos mútuos dela: Heitox, Gabrielplay, Victor e Fabrício#251.
- O **time de futebol** continua unido: Mesi, Neymar, cristiano Ronaldo e Ronaldo gaucho são todos amigos
  entre si. O Theogoleiro (casa 45) virou amigo do Heitox.
- **Heitox** ganhou 3 amigos mútuos de uma vez: Dona Joana, Theogoleiro e Fabrício#251.
- **João Guilherme** (destaque do ep. 4) finalmente teve amizade aceita: Gabrielplay e Victor.

## 4. Morador em destaque (1 frase)

> **cristiano Ronaldo (#281, casa 29):** "Escreveu na bio que é o melhor jogador de bola da cidade… pena que
> ainda não tem campo — faltam 83 inscritos."

Alternativa: *"O Dante chegou no último segundo do episódio 5, morando numa casa que ainda nem tinha
telhado."*

## 5. Regras pra não quebrar o site

1. Moradores #1 a #577 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #578 em diante usam
   `npc_look(id)` normal e `chegou_no_ep = 6`.
2. Casas, lotes, ruas e pontos antigos não mudam de lugar; lotes novos entram **no fim** da lista.
3. **O mapa só cresce pra baixo ou pra direita** (ver seção 2), com `mapa.largura`/`mapa.altura` atualizados.
4. Moradores de casa ainda em obra podem existir (o site já trata isso).
5. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`).
6. Atualizar `estado_vila.json` (seguidores, casas, construções, marcos feitos, lotes, episódio).
7. Devolver a pasta inteira do projeto num zip.

## 6. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores. Lê o LEIA-ME, o estado_vila.json e o
> RELATORIO_PARA_EP6.md. Agora tenho **617 seguidores** (troca pelo número do dia) e a cidade ainda não tem nome.
> Quero o **episódio 6**: primeiro o roteiro, depois o vídeo. O mapa lotou: a cidade tem que **crescer o mapa
> (só pra baixo ou pra direita)** e abrir rua nova. Tem que ter as **casas 58 a 61**, o **2º mercadinho e o
> posto de saúde** (marco 600) e o morador em destaque do relatório (cristiano Ronaldo, que quer um campo de
> futebol — marco 700). Se quiser, retoma os ganchos do ep. 5 (prefeito e nome da cidade). No fim roda o
> exportar_site.py e me devolve o projeto inteiro.
