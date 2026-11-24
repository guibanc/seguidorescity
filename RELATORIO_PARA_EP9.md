# Relatório para o Episódio 9 — A Cidade dos Seguidores (Pindamonhangaba)

Levantado em **23/11/2026 às 22:38 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 8 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 721 | **780** |
| Casas prontas | 72 | **78** (casas 73 a 76 fecham a rua E; **77 e 78 abrem a rua F**) |
| Moradores novos | — | **#722 a #780** (59 moradores) |
| Próxima obra | casa 73 (725 → 730) | **casa 79** (começa com 785, fica pronta com 790; lote 140,600,a) |

- **Próximo marco: 800 — PADARIA/LANCHONETE. Faltam só 20!** Pode chegar antes do episódio 10.
  ⚠️ **Ainda não tem terreno reservado pra ela.** Reservar no mapa (ponto novo no `vila.json` com
  `"marco": 800` e `"lotes"`), igual foi feito com o campo. Assim o site mostra a placa "faltam X" em cima do terreno.
- Depois: 900 = torre de internet · 1000 = ponte (vira cidade).
- **Espaço no mapa: tranquilo.** A rua F tem lotes até a casa 90 (900 inscritos). Pro 1000, o mapa vai
  precisar crescer de novo (sempre pra baixo ou pra direita).

## 2. O que aconteceu no site desde o ep. 8

- **Eleição: agora são 14 candidatos** (eram 11). A votação ainda não abriu.
- **68 moradores têm nome** (eram 64). Os 4 novos: **jessica**, **Zé pelintra**, **beca** e um segundo
  **Neymar** (#566, casa 57; o Neymar do time continua lá).
- Heitor Emmanull **mudou de casa** (#611 → #471). Poly agora se chama **Poly_jogadora**.
- **Chat:** 13 mensagens de 5 pessoas desde o ep. 8 (164 no total). Foi uma semana mais calma, quase toda de campanha.
- **Amizades: 149 pedidos, 45 amizades mútuas** (eram 143 e 42). Novas: Poly_jogadora com Albert aisten e beca;
  jessica com Enzo Mildana.

A lista completa, com o visual de cada um, está em `dados_do_site/registrados.json`
(mesmo formato do `npc_look()`). Mostrar só o **nome**, nunca o @.

### Os 3 candidatos novos

| Candidato | Promessa |
|---|---|
| Apenas um jogador (#335) | "Voto: 777. Delegacia, hospital e bombeiros, de qualidade, tudo 25% de imposto" |
| jessica (#191) | "vote seguro vote 32: trarei mais segurança para os moradores e água grátis" |
| Albert aisten (#257) | "Prometo um parquinho e uma academia ao ar livre, vote 35. O melhor presidente" |

Os outros 11 continuam com as promessas do relatório do ep. 8 (sales e Mt: **mostrar só o nome**).

### Chat: o que rolou (rende cena)
- **jessica faz campanha pros dois lados:** *"votem joao guilherme… estou distribuindo panfleto"*,
  mas ela mesma também é candidata ("vote 32").
- **Enzo Mildana fez discurso:** *"Vcs oferecem propostas de curto prazo, eu estou oferecendo a minha palavra,
  a comida e bebida acaba em menos de dias… no entanto a palavra de um homem mantém-se fixa até seu último suspiro!"*
- **Briga de número:** Apenas um jogador pediu *"votem 777"*, e o Bachirapro reclamou
  *"Esse apenas um jogador ta me copiando mano"*. O Enzo apaziguou: *"deixa quieto bro…"*.
- Bachirapro seguiu firme: *"Votem em mim: pastel e caldo de cana de graça"*.
- Enzo Mildana: *"Parece que eu sou o único sempre on-line"* (e depois escreveu em japonês que precisa
  "ter uma vida mais social" 😄).

## 3. Morador em destaque (1 frase)

> **Enzo Mildana (#614):** "O candidato que nunca sai do site: disse que é o único sempre on-line, fez discurso
> no chat e ainda acalmou a briga dos outros candidatos."

Alternativas:
- *"A jessica é candidata… mas passou a semana distribuindo panfleto do João Guilherme."*
- *"14 candidatos e ninguém votou ainda: a votação nem abriu!"*

## 4. Decisão sua antes de gravar

- **A votação vai abrir?** Se o vídeo anunciar "a votação começou", eu preciso abrir a votação no site antes
  do vídeo sair (hoje a fase é só de candidaturas). Se não, o vídeo fala só "14 candidatos, votação em breve".

## 5. Regras pra não quebrar o site

1. Moradores #1 a #721 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #722 a #780 usam
   `npc_look(id)` normal e `chegou_no_ep = 9`.
2. Casas, lotes, ruas e pontos antigos não mudam de lugar (o ponto `campo` também fica igual); lotes novos
   entram **no fim** da lista. Casas 73 a 78 usam os lotes já previstos em `lotes_livres`.
3. O terreno da padaria/lanchonete (marco 800) é um **ponto novo** no `vila.json`, com `"marco": 800` e `"lotes"`.
4. O mapa só cresce **pra baixo ou pra direita**, com `mapa.largura`/`mapa.altura` atualizados.
5. Continua **32 bits isométrico**: mesma fórmula; atualizar `iso.origem`, `iso.largura` e `iso.altura`
   no `vila.json` se gerar a imagem de novo.
6. O site não tem mais Explorar, Terrenos e Lotes, mochila nem lojas: **não mostrar** nada disso.
7. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`).
8. Atualizar `estado_vila.json` (seguidores 780, casas 78, próxima casa 79, próximo episódio 10) e devolver
   a pasta inteira do projeto num zip.

## 6. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores (a cidade se chama Pindamonhangaba). Lê o LEIA-ME,
> o estado_vila.json e o RELATORIO_PARA_EP9.md. Agora tenho **780 seguidores** (troca pelo número do dia).
> Quero o **episódio 9**: primeiro o roteiro, depois o vídeo, em isométrico 32 bits. Tem que ter as **casas 73 a 78**
> (a rua E fecha e a **rua F começa** a encher), a **campanha esquentando** (14 candidatos, a jessica panfletando
> pro João Guilherme, o discurso do Enzo, a briga do 777), o **morador em destaque** (Enzo Mildana) e o gancho
> forte da **padaria/lanchonete no 800: faltam só 20**. Reserva o terreno dela no mapa com uma placa.
> Não mostra nada de explorar, terrenos ou lojas. No fim roda o exportar_site.py e me devolve o projeto inteiro.
