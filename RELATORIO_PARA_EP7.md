# Relatório para o Episódio 7 — A Cidade dos Seguidores

Levantado em **16/11/2026 às 12:40 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 6 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 617 | **647** |
| Casas prontas | 61 | **64** (casas 62, 63 e 64, todas na rua E) |
| Moradores novos | — | **#618 a #647** (30 moradores) |
| Próxima obra | casa 62 (615 → 620) | **casa 65** (começou com 645, fica pronta com 650) |

- **Próximo marco: 700 — CAMPO DE FUTEBOL** (faltam 53). O terreno já está reservado na rua F (4 lotes).
- Depois: 800 = padaria/lanchonete · 900 = torre de internet · 1000 = ponte.
- **Espaço no mapa: tranquilo.** Os lotes livres das ruas E e F vão até a casa 90 (900 inscritos).
- **Ganchos ainda abertos:** prefeito e nome da cidade (a placa da entrada continua vazia).

## 2. O que aconteceu no site desde o ep. 6

O site ganhou muita coisa nova — vale mostrar no vídeo:
- **Visão isométrica**, igual à do vídeo (com botão pra trocar pra visão de cima).
- **Chat ao vivo** estilo live, no canto da tela: **70 mensagens de 20 pessoas** só no primeiro dia.
- **Quem está online** aparece com bolinha verde, e **quem move o boneco aparece andando pra todo mundo** ao vivo.
- **Entrar nas casas e no mercadinho**: cada casa tem um interior próprio (beliches, TV, geladeira, fogão, sofá, mesa…).
- **Barra de vida**: andar cansa; lanche na geladeira, compras no mercadinho e dormir na cama recuperam.
  Na praça dá pra **sentar no banco** e **jogar uma moeda na fonte** (sorte do dia).
- **Mudar de casa**: a pessoa escolhe a casa e troca de lugar com um morador sem nome de lá.

**53 moradores têm nome** (eram 39). Os 14 novos: João Pedro (#4), JoãoCurado, Thales, Briel, GLEYDSON,
cabeludo👽, Batudinho, Albert aisten, Darrylzin, Antini, Artur, **DEUS**, BachiraPro e Enzo Mildana.
A lista completa, com o visual de cada um, está em `dados_do_site/registrados.json`
(**mesmo formato do `npc_look()`**: dá pra passar direto pro `npc_sprite`). Mostrar só o **nome**, nunca o @.

**Bios que rendem cena:**
| Morador | Bio |
|---|---|
| C4rmin (#258) | "Oi eu sou um player real e sera que algum dia o adm me nota?" |
| BLUE (#26) | "Quem é campeão também pode ser prefeito, vote blue para uma cidade melhor" |
| DEUS (#473) | "DEUS melhor do Fut" |
| Theogoleiro (#441) | "Melho goleiro da cidade 👍👍👍" |
| cristiano Ronaldo (#281) | "melhor jogador de bola na cidade pena que não tem campo" |
| João Pedro (#4) | "Tem fome. E Gosta de comer tudo!" |
| ♥︎Dona Joana♥︎ (#290) | "Amiga de quase todos e considera todo mundo como neto♥︎" |
| Kira (#67) | "O que posso dizer além de six seven (67)? Objetivo: ser o maior farmador de aura da vila" |
| Guilherme (#193) | "Jesus Saves - Fundador da Vila" |

**Chat:** quem mais falou foi **C4rmin (15 mensagens)**, depois João Pedro (13) e DEUS (10).
O Thales chegou e perguntou no chat "Onde fica a casa 2" — ele mora lá.

**Amizades: 123 pedidos, 34 amizades mútuas** (eram 22).
- **Dona Joana** agora tem **13 vizinhos** que adicionaram ela de volta (eram 9). Novos amigos mútuos dela:
  Isabely67, Poly, Darrylzin e Rafael.
- **O time de futebol cresceu**: Mesi, Neymar, cristiano Ronaldo e Ronaldo gaucho (todos amigos entre si),
  mais o **DEUS** ("melhor do Fut") e o **Theogoleiro** ("melhor goleiro") — o time já tem goleiro, só falta o campo.
- **Rafael** virou o "enturmado" da semana: amigo mútuo de João Pedro, Dona Joana e João Guilherme.

## 3. Morador em destaque (1 frase)

> **C4rmin (#258, casa 26):** "Foi quem mais falou no chat e escreveu na bio: 'será que algum dia o adm me
> nota?'… notamos, C4rmin!"

Alternativas:
- *"BLUE já está em campanha na bio: 'vote blue para uma cidade melhor' — a cidade ainda nem tem eleição."*
- *"O time de futebol já tem até goleiro: Theogoleiro e DEUS esperam o campo… faltam 53."*

## 4. Regras pra não quebrar o site

1. Moradores #1 a #617 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #618 em diante usam
   `npc_look(id)` normal e `chegou_no_ep = 7`.
2. Casas, lotes, ruas e pontos antigos não mudam de lugar; lotes novos entram **no fim** da lista.
3. O mapa só cresce **pra baixo ou pra direita**, com `mapa.largura`/`mapa.altura` atualizados.
4. Se gerar a imagem isométrica de novo, manter a mesma fórmula e atualizar `iso.origem`, `iso.largura`
   e `iso.altura` no `vila.json` (o site já lê daí).
5. Obs.: no site a pessoa pode **mudar de casa** — isso só troca qual número tem dono; o `moradores.json`
   (casa e visual original de cada número) continua igual. O `registrados.json` já mostra quem está onde hoje.
6. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`).
7. Atualizar `estado_vila.json` e devolver a pasta inteira do projeto num zip.

## 5. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores. Lê o LEIA-ME, o estado_vila.json e o
> RELATORIO_PARA_EP7.md. Agora tenho **647 seguidores** (troca pelo número do dia) e a cidade ainda não tem nome.
> Quero o **episódio 7**: primeiro o roteiro, depois o vídeo, em isométrico. Tem que ter as **casas 62 a 64**
> (e a 65 em obra), o **morador em destaque** (C4rmin), as **novidades do site** (chat ao vivo, entrar nas
> casas, mudar de casa) e o gancho do **campo de futebol** (faltam 53, e o time já tem goleiro). Se quiser,
> usa a campanha do BLUE pra prefeito. No fim roda o exportar_site.py e me devolve o projeto inteiro.
