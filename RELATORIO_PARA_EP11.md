# Relatório para o Episódio 11 — A Cidade dos Seguidores (Pindamonhangaba)

Levantado em **27/11/2026 às 17:47 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 10 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 814 | **838** |
| Casas prontas | 81 | **83** (casas 82 e 83, na rua F) |
| Moradores novos | — | **#815 a #838** (24 moradores) |
| Próxima obra | casa 82 (815 → 820) | **casa 84 já em obra** (começou com 835, fica pronta com 840; lote 60,600,b) |

- **Próximo marco: 900 — TORRE DE INTERNET** (faltam 62). O terreno já está reservado na rua G (lote 206,690,b, ponto `torre`).
- Depois: 1000 = **ponte sobre o rio** (vira cidade de verdade).
- **Espaço no mapa: tranquilo de novo.** Com a rua G, tem lote até a **casa 104** (1040 inscritos).
- **Vacas do curral:** o desafio do ep. 10 era "1 comentário = 1 vaca". Isso eu não consigo contar daqui:
  **conte os comentários do ep. 10 no YouTube** e passe o número pra IA do vídeo.

## 2. 👑 TEMOS PREFEITO: ENZO MILDANA!

A votação fechou **hoje, 27/11, às 11:25**, e o site elegeu sozinho o mais votado.

| | Votos |
|---|---|
| 👑 **Enzo Mildana (#614)** "Para uma comunidade mais unida!" | **8** |
| Capitão Jair (#96) (era "Cabo Jair") "Saúde e segurança para todos" | **7** |
| Isabely67 (#11) | 2 |
| Kira, Bachirapro, Apenas um jogador e Teuszx | 1 cada |
| Os outros 12 candidatos | 0 |

**21 votos, 19 candidatos, e ganhou por 1 voto.** Na última apuração (ep. 10) estava 3 × 3.

**Como foi a reta final (chat):**
- O **Jair** fez campanha pesada: foram 27 mensagens, mais que qualquer um. Prometeu delegacia, hospital, escola melhor,
  quadra de futsal, lan house, supermercado, *"prometo o asfalto"*. No fim, perdeu com elegância:
  *"Obrigado a quem votou em mim, lutamos muito mas não deu"*.
- O **Enzo** apostou na palavra: *"Eu não vou fazer promessas vagas… votem em mim para uma comunidade mais unida,
  pois a união faz a força!"*.
- **IVALDO** comemorou: *"ENZOOOOOO… isso enzooooo 🥳🥳🥳"*.
- **GABRIEL** chegou no meio da eleição: *"Minha irmã de 11 anos votou por mim no Enzo… brincadeira, fui eu mesmo"*.
- O debate continuou depois do resultado: *"Votou em quem não deu proposta"* × *"não é só ele que vai fazer
  as coisas, vai ser a democracia das pessoas"* × *"a democracia é pra gente votar, a união é que está nas pessoas"*.

⚠️ **Cuidado:** o Jair usou números, apelidos e frases que lembram política de verdade, e o Teuszx usou um slogan
com nome de político real. **No vídeo, mostrar só os nomes e as promessas da cidade** (hospital, asfalto, quadra…),
sem nenhuma referência a política real. sales e Mt continuam aparecendo **só com o nome**.

**Ideias pro episódio:** posse na prefeitura (faixa de prefeito, discurso "a união faz a força", fogos), a coroa 👑
em cima do Enzo no mapa, e o Jair cumprimentando o Enzo (fair play). Gancho: **"qual vai ser a primeira obra do prefeito?"**

## 3. O que aconteceu no site desde o ep. 10

- O site agora mostra o **prefeito com coroa 👑** na prefeitura e na ficha dele.
- **Chat bombou:** 82 mensagens de 12 pessoas em 2 dias (263 no total), quase tudo sobre a eleição.
- **82 moradores têm nome** (eram 74). Os 8 novos: Teuszx, Davimito334, Brunao, Ribeiro, Val, **GABRIEL**,
  **IVALDO** e **Diego brando** (*"Oi, tudo bem? Sou novo aqui na cidade"*).
- **cristiano Ronaldo mudou de casa** (#12 → **#761**, casa 77) e atualizou a bio: *"JÁ FIZ 989 GOLS, SIUUU!!"*.
  No chat: *"eu tô jogando no campo, eu sou jogador"*.
- **Amizades:** 155 pedidos, 47 mútuas. Novas: GABRIEL & Enzo Mildana; e o cristiano Ronaldo refez as amizades
  com o time (Mesi, Neymar, Ronaldo gaucho) e com a Dona Joana.
- Teve gente confusa no chat: *"já lançou o episódio 10 mas o site está no 9"*. **O site já foi atualizado pro ep. 10.**

A lista completa, com o visual de cada um, está em `dados_do_site/registrados.json`
(mesmo formato do `npc_look()`). Mostrar só o **nome**, nunca o @.

## 4. Morador em destaque (1 frase)

> **Enzo Mildana (#614), o 1º prefeito de Pindamonhangaba:** "Foi destaque no ep. 9 como 'o único sempre on-line',
> fez campanha sem prometer nada além da palavra… e ganhou por um voto: 8 a 7!"

Alternativas:
- *"O Capitão Jair fez 27 mensagens de campanha, prometeu até asfalto, perdeu por 1 voto… e agradeceu todo mundo."*
- *"O cristiano Ronaldo daqui já diz que fez 989 gols. O campo da cidade não para."*

## 5. Regras pra não quebrar o site

1. Moradores #1 a #814 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #815 a #838 usam
   `npc_look(id)` normal e `chegou_no_ep = 11`.
2. Casas, lotes, ruas e pontos antigos não mudam de lugar (inclusive `campo`, `bombeiros`, `petshop`, `padaria`,
   `torre`); lotes novos entram **no fim** da lista. Casas 82 a 83 usam os lotes já previstos em `lotes_livres`.
3. O mapa só cresce **pra baixo ou pra direita**, com `mapa.largura`/`mapa.altura` atualizados.
4. Continua **32 bits isométrico**: mesma fórmula; atualizar `iso.origem`, `iso.largura` e `iso.altura` se gerar a imagem de novo.
5. Em `estado_vila.json`: `prefeitura.prefeito` = 614 (Enzo Mildana), seguidores 838, casas 83, próxima casa 84,
   próximo episódio 12.
6. Não mostrar explorar, terrenos ou lojas (desligados no site).
7. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`)
   e devolver a pasta inteira do projeto num zip.

## 6. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores (a cidade se chama Pindamonhangaba). Lê o LEIA-ME,
> o estado_vila.json e o RELATORIO_PARA_EP11.md. Agora tenho **838 seguidores** (troca pelo número do dia).
> Quero o **episódio 11**: primeiro o roteiro, depois o vídeo, em isométrico 32 bits. O centro é o
> **RESULTADO DA ELEIÇÃO: Enzo Mildana é o 1º prefeito de Pindamonhangaba, 8 × 7 no Capitão Jair**. Mostra
> a apuração voto a voto, a posse na prefeitura (faixa, discurso "a união faz a força", fogos) e o Jair
> cumprimentando o Enzo. Tem que ter as **casas 82 e 83** (e a 84 em obra), as **vacas no curral** (o número
> de comentários do ep. 10: ___) e o gancho da **torre de internet no 900 (faltam 62)**, terminando com
> "qual vai ser a primeira obra do prefeito?". Sem referência a política de verdade. Não mostra explorar,
> terrenos ou lojas. No fim roda o exportar_site.py e me devolve o projeto inteiro.
