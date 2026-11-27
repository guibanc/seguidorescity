# Relatório para o Episódio 10 — A Cidade dos Seguidores (Pindamonhangaba)

Levantado em **25/11/2026 às 16:00 (Brasília)**, direto do banco do site e do contador do YouTube.
Use o número de inscritos do dia em que for gravar: o contador sobe sozinho em https://cidadedosseguidores-six.vercel.app/

## 1. Números

| | Ep. 9 (último vídeo) | Agora |
|---|---|---|
| Inscritos / moradores | 780 | **814** |
| Casas prontas | 78 | **81** (casas 79, 80 e 81, na rua F) |
| Moradores novos | — | **#781 a #814** (34 moradores) |
| Próxima obra | casa 79 (785 → 790) | **casa 82** (começa com 815, fica pronta com 820; lote 162,600,a). Falta 1 inscrito pra obra começar. |

- **MARCO 800 BATIDO: PADARIA/LANCHONETE!** Ela entra no terreno que já estava reservado (lote 16,600,b, ponto `padaria`).
- **Próximo marco: 900 — TORRE DE INTERNET** (faltam 86). ⚠️ Ainda **não tem terreno reservado** pra ela.
- Depois: 1000 = ponte (vira cidade de verdade).
- ⚠️ **Espaço no mapa acabando:** só sobram lotes até a **casa 87**. A casa 88 fica pronta com 880 inscritos
  (faltam 66). **Neste episódio já precisa abrir lotes novos** (uma rua G, por exemplo), com o mapa crescendo
  **só pra baixo ou pra direita**. Aproveitar e reservar o terreno da torre de internet (900).

## 2. A ELEIÇÃO (o grande assunto do episódio)

A **votação está aberta** desde 24/11 e **termina na sexta, 27/11, às 11:25 (Brasília)**. Nessa hora o site
elege sozinho o mais votado. **Em caso de empate, ganha quem se candidatou primeiro.**

**Placar agora (9 votos):**

| Candidato | Votos | Promessa |
|---|---|---|
| Enzo Mildana (#614) | **3** | "Para uma comunidade mais Unida! Votem #614" |
| Cabo Jair (#96) ⭐ novo | **3** | "Saúde e segurança para todos, vote 22!" |
| Isabely67 (#11) | 2 | "Shows, shoppings, campos de futebol, praias… e muito mais" |
| Apenas um jogador (#335) | 1 | "Delegacia, hospital e bombeiros, de qualidade" |
| Os outros 12 | 0 | — |

- **Empate no topo:** Enzo Mildana 3 × 3 Cabo Jair. Do jeito que está agora, o Enzo ganharia, porque se candidatou antes.
- 16 candidatos ao todo (2 novos: **Cabo Jair** e **Saitu🌹**, que prometeu "Hospital galera").
- O Cabo Jair chegou agora e já está em 1º, empatado. No chat ele perguntou: *"Quero colocar panfleto, santinho
  ou fazer comício, alguém sabe como faz?"*.
- Cuidado: nome e número de candidato lembram política de verdade. **Mostrar só o nome**, sem piada de política real.
- sales e Mt continuam aparecendo **só com o nome** (os slogans têm piada adulta).

### 👉 Decisão sua: quando gravar?
- **Depois de sexta 11:25 (recomendado):** o episódio 10 já mostra **o primeiro prefeito de Pindamonhangaba**.
  Rode este relatório de novo antes de gravar (é só me pedir) que eu atualizo o resultado final.
- **Antes de sexta:** o vídeo mostra o empate e deixa o suspense: "quem vai ser o prefeito? descobre no ep. 11".

## 3. O que aconteceu no site desde o ep. 9

- **Votação ao vivo:** cada morador tem 1 voto, não dá pra trocar, aparece uma confirmação antes e a contagem vai subindo na hora.
- **Chat no celular:** o botão "Chat" abre um celular na tela, no estilo app de mensagem, com o histórico inteiro,
  o horário de cada mensagem e emojis. Rende uma cena de montagem (desenhada no estilo da cidade, sem print e sem @).
- **74 moradores têm nome** (eram 68). Os 6 novos: Gey, tomasthurbano, **Cabo Jair**, **Venefrides**,
  Manuel Larp João e Saitu🌹.
- **Chat:** 17 mensagens de 5 pessoas (181 no total). **Amizades:** 152 pedidos, 46 mútuas (nova: Cabo Jair & Manuel Larp João).

A lista completa, com o visual de cada um, está em `dados_do_site/registrados.json`
(mesmo formato do `npc_look()`). Mostrar só o **nome**, nunca o @.

### Falas e bios que rendem cena
- **GLEYDSON (#75)** mudou a bio pra *"Quero meus cachorro"* e cobrou no chat:
  *"quero meus cachorros, os 3… um preto pequeno, um amarelo peludo e um amarelo pelo curto… desde o episódio 1 ksksks"*.
  **A cidade tem petshop desde o ep. 9: dá pra ele finalmente buscar os 3 cachorros!**
- **Venefrides (#136)**, bio: *"Cês tão bão? Alguém arruma um pão de queijo aí pra mim?"*. **A padaria chegou bem na hora.**
- **Enzo Mildana:** *"vcs viram o episódio 9? 😏😜"* (ele foi o destaque do ep. 9).

## 4. Morador em destaque (1 frase)

> **GLEYDSON (#75):** "Desde o episódio 1 ele pedia os três cachorros: um preto pequeno, um amarelo peludo e
> um amarelo de pelo curto… hoje ele saiu do petshop com os três!"

Alternativas:
- *"O Venefrides pediu um pão de queijo na bio… e a cidade abriu uma padaria."*
- *"O Cabo Jair chegou agora, nem sabia como fazer comício, e já está empatado em 1º lugar."*

## 5. Regras pra não quebrar o site

1. Moradores #1 a #780 **não mudam** (número, casa, aparência, `chegou_no_ep`). Os novos #781 a #814 usam
   `npc_look(id)` normal e `chegou_no_ep = 10`.
2. Casas, lotes, ruas e pontos antigos não mudam de lugar (inclusive `campo`, `bombeiros`, `petshop`, `padaria`);
   lotes novos entram **no fim** da lista. Casas 79 a 81 usam os lotes já previstos em `lotes_livres`.
3. A padaria fica **só** no lote reservado (16,600,b). Ao terminar: `marcos_feitos` ganha "800": "padaria/lanchonete".
4. **Lotes novos pra casas 88+** e o **terreno da torre (marco 900)**: ponto novo no `vila.json` com `"marco": 900`
   e `"lotes"`. O mapa só cresce **pra baixo ou pra direita**, com `mapa.largura`/`mapa.altura` atualizados.
5. Continua **32 bits isométrico**: mesma fórmula; atualizar `iso.origem`, `iso.largura` e `iso.altura` se gerar a imagem de novo.
6. Não mostrar explorar, terrenos ou lojas (desligados no site).
7. No fim, rodar `python3 exportar_site.py ../site` (gera `site/img`, `site/dados` e o `novos_moradores.sql`).
8. Atualizar `estado_vila.json` (seguidores 814, casas 81, próxima casa 82, marco 800 feito, próximo episódio 11)
   e devolver a pasta inteira do projeto num zip.

## 6. Texto pronto pra colar na IA do vídeo

> Esse é o projeto da série A Cidade dos Seguidores (a cidade se chama Pindamonhangaba). Lê o LEIA-ME,
> o estado_vila.json e o RELATORIO_PARA_EP10.md. Agora tenho **814 seguidores** (troca pelo número do dia).
> Quero o **episódio 10**: primeiro o roteiro, depois o vídeo, em isométrico 32 bits. O centro é o
> **marco 800: a PADARIA/LANCHONETE** abrindo (o Venefrides finalmente ganha o pão de queijo) e a **eleição**:
> [ESCOLHA UM: "o resultado: o primeiro prefeito é ___" OU "o empate Enzo Mildana 3 × 3 Cabo Jair, resultado no ep. 11"].
> Tem que ter as **casas 79 a 81** na rua F, o **morador em destaque** (GLEYDSON buscando os 3 cachorros no
> petshop) e a montagem do **chat no celular**. Abre lotes novos pras casas 88+ e reserva o terreno da
> **torre de internet (900, faltam 86)**, que é o gancho do final. Não mostra explorar, terrenos ou lojas.
> No fim roda o exportar_site.py e me devolve o projeto inteiro.
