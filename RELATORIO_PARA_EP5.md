# Relatório para o Episódio 5 — A Cidade dos Seguidores

Levantado em **15/11/2026 às 11:37 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 4 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 460 | **577** |
| Casas prontas | 46 | **57** (casas 47 a 57 são novas, todas na rua D) |
| Moradores novos | — | **#461 a #577** (117 moradores) |
| Próxima obra | casa 47 (465) | **casa 58 em obra** (começou com 575, fica pronta com 580) |

- **Marco 500 — PREFEITURA + RUAS CALÇADAS: atingido.** A vila **vira cidadezinha**. Lotes já reservados na
  rua D: `(140, 420, 'a')` e `(162, 420, 'a')` (`lote_reservado_prefeitura` no `estado_vila.json`).
- **Marco 600 — 2º MERCADINHO + POSTO DE SAÚDE: faltam só 23.** É bem provável que já tenha passado de 600
  no dia da gravação; se passou, entra neste episódio também.
- Depois: 700 = campo de futebol · 800 = padaria/lanchonete.
- **Nome da vila:** ainda sem nome (placa da entrada vazia).

## 2. ⚠️ Espaço no mapa: lota de novo em 610

A rua D tem lotes para as **casas 47 a 61**. Com 57 casas prontas, **sobram só 4 lotes** (casas 58 a 61):
o mapa lota de novo quando chegar a **610**.

E o **marco 600 ainda não tem lote reservado**: o 2º mercadinho e o posto de saúde precisam de 2 a 4 lotes.
Se eles ocuparem lotes de casa, o mapa lota antes.

**Sugestão para o ep. 5:** reservar os lotes do marco 600 e já deixar planejada uma **rua E** (como foi feito
com a rua D). Lotes antigos **nunca mudam de ordem nem de lugar**; lotes novos entram no fim da lista.

## 3. O que aconteceu no site desde o ep. 4

**32 moradores têm dono** (eram 17). Os novos: Heitox, Didi, João Pedro, INGRID DO GRAU, Gazinho, Mesi,
BSF_gamer01, Ronaldo gaucho, Zé, cristiano Ronaldo, ♥︎Dona Joana♥︎, Jean, Neymar, Dudu e Theogoleiro.
Dudu (#412) e Theogoleiro (#441) são moradores que chegaram no ep. 4.

| # | Nome | Casa | Chegou no ep. | Visual personalizado | Bio |
|---|---|---|---|---|---|
| 1 | Heitox | 1 | 1 | sim | |
| 2 | Didi | 1 | 1 | sim | |
| 3 | João Pedro | 1 | 1 | sim | |
| 6 | Luiz | 1 | 1 | sim | |
| 11 | Isabely67 | 2 | 1 | sim | |
| 23 | INGRID DO GRAU | 3 | 1 | sim | |
| 24 | Alyce | 3 | 1 | sim | |
| 34 | Gabrielplay | 4 | 1 | sim | |
| 45 | Gazinho | 5 | 1 | sim | |
| 67 | Kira | 7 | 1 | sim | "O que posso dizer além de six seven (67)? Objetivo: ser o maior farmador de aura da vila" |
| 83 | Poly | 9 | 1 | sim | |
| 88 | Broch | 9 | 1 | sim | |
| 150 | Joe Keffyler | 15 | 1 | sim | |
| 154 | Wesley | 16 | 1 | sim | |
| 168 | Mesi | 17 | 1 | sim | |
| 171 | Greninjapok09 | 18 | 1 | sim | |
| 181 | Victor | 19 | 1 | não | |
| 193 | Guilherme | 20 | 1 | sim | "Jesus Saves - Fundador da Vila" |
| 212 | Pietro | 22 | 1 | sim | |
| 223 | BSF_gamer01 | 23 | 1 | sim | |
| 229 | Pedro | 23 | 1 | sim | |
| 236 | Ronaldo gaucho | 24 | 1 | sim | |
| 272 | Zé | 28 | 2 | sim | |
| 281 | cristiano Ronaldo | 29 | 2 | sim | |
| 290 | ♥︎Dona Joana♥︎ | 29 | 2 | sim | "Amiga de quase todos e considera todo mundo como neto♥︎" |
| 302 | Arthur | 31 | 2 | sim | |
| 322 | Rafael | 33 | 3 | não | |
| 325 | Jean | 33 | 3 | sim | |
| 347 | João Guilherme | 35 | 3 | sim | |
| 348 | Neymar | 35 | 3 | sim | |
| 412 | Dudu | 42 | 4 | sim | |
| 441 | Theogoleiro | 45 | 4 | sim | |

O visual de cada um está em `dados_do_site/registrados.json`, **no mesmo formato do `npc_look()`** —
dá pra passar direto para `npc_sprite(look, dir, frame)`. Mostrar só o **nome** (nunca o @). Se a fonte do
vídeo não tiver o símbolo ♥︎, escrever **Dona Joana**.

**Amizades: 95 pedidos enviados, 14 amizades mútuas.**
- **♥︎Dona Joana♥︎ adicionou 58 vizinhos** — sozinha, mais que todo o resto da vila junto (37). É amiga mútua
  de Guilherme, Alyce, Wesley, INGRID DO GRAU e cristiano Ronaldo.
- **O "time de futebol":** Mesi, Neymar, cristiano Ronaldo e Ronaldo gaucho são todos amigos entre si
  (6 amizades mútuas). E ainda tem o Theogoleiro morando na casa 45.
- Isabely67 ★ Guilherme · Guilherme ★ Pedro · INGRID DO GRAU ★ Wesley.
- João Guilherme (o destaque do ep. 4) agora adicionou 11 vizinhos.

## 4. Morador em destaque (1 frase)

> **♥︎Dona Joana♥︎ (#290, casa 29):** "Mandou pedido de amizade pra 58 vizinhos — porque, pra ela, a vila
> inteira é neto."

Alternativa: *"Mesi, Neymar, Cristiano Ronaldo e Ronaldo Gaúcho já são todos amigos… a vila tem time, só falta
o campo (marco 700)."*

## 5. Regras pra não quebrar o site

1. Moradores #1 a #460 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #461 em diante usam
   `npc_look(id)` normal e `chegou_no_ep = 5`.
2. Casas e lotes antigos não mudam de lugar nem de ordem; lotes novos entram **no fim** da lista.
3. As ruas calçadas podem mudar o **desenho** do mapa à vontade, mas as coordenadas das ruas, portas e pontos
   (praça, mercadinho, vendinha, igreja, escola) precisam continuar as mesmas — os moradores do site andam por elas.
4. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`).
5. Atualizar `estado_vila.json` (seguidores, casas, construções, marcos feitos, lotes, episódio).
6. Devolver a pasta inteira do projeto num zip (com `codigo/`, `site/`, `estado_vila.json`, roteiro e referência).

## 6. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores. Lê o LEIA-ME, o estado_vila.json e o
> RELATORIO_PARA_EP5.md. Agora tenho **577 seguidores** (troca pelo número do dia) e a vila ainda não tem nome.
> Quero o **episódio 5**: primeiro o roteiro, depois o vídeo. Tem que ter a **prefeitura e as ruas calçadas**
> (marco 500, a vila vira cidadezinha), as **casas 47 a 57** na rua D, o morador em destaque do relatório
> (Dona Joana) e, se já tiver passado de 600, o **2º mercadinho e o posto de saúde**. Reserva lotes pro marco
> 600 e planeja a rua E, porque o mapa lota em 610. No fim roda o exportar_site.py e me devolve o projeto inteiro.
