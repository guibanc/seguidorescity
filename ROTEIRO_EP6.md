# A Cidade dos Seguidores — Episódio 6 (roteiro)
~90 s · 577 → 617 seguidores · o mapa lota, **cresce pra baixo** (ruas E e F) · **NOVA EVOLUÇÃO: visão isométrica** · marco 600: 2º mercadinho + posto de saúde · aviso dos minigames

| # | Tempo | Narração (IA de voz) | Na tela |
|---|---|---|---|
| 1 | 0–4 | A Cidade dos Seguidores... episódio 6! | Título sobre a cidade em 16 bits, como terminou no ep. 5 |
| 2 | 4–9 | Da última vez, eram 577 moradores, 57 casas... e só sobravam três lotes. | "ATÉ AGORA: 577 / 57 CASAS" · 3 lotes livres piscando na rua D |
| 3 | 9–15 | E eles acabaram rapidinho: casa 58, 59, 60, 61... | Contador 577 → 610, casas 58–61 subindo na rua D |
| 4 | 15–20 | Só que o contador passou de 600, e com ele vieram o segundo mercadinho e o posto de saúde. | "600!" + "NOVO MARCO DESBLOQUEADO" · ícones dos 2 prédios |
| 5 | 20–24 | Mas construir onde? Não tinha mais nenhum lote. | Lotes piscando em vermelho · "MAPA LOTADO!" · prédios "flutuando" sem lugar |
| 6 | 24–31 | Então a cidade fez o que tinha que fazer: cresceu! O mapa aumentou pra baixo... e ganhou duas ruas novas. | A borda de baixo "desenrola": terra nova, árvores saindo, rua principal descendo, ruas E e F sendo abertas · "O MAPA CRESCEU!" |
| 7 | 31–40 | E junto com o mapa novo veio uma evolução: a cidade agora é isométrica! Telhado de verdade, janela, chaminé... dá até pra ver a lateral das casas. | **Virada de estilo:** a câmera inclina e o mapa 16 bits "gira" pro isométrico, com flash · "NOVA EVOLUÇÃO: ISOMÉTRICO!" · passeio pelas casas e pela prefeitura no estilo novo |
| 8 | 40–48 | Na rua nova já subiram o segundo mercadinho e o posto de saúde. | Obra dos 2 prédios na rua E (fundação → paredes → telhado) · posto com cruz verde, mercadinho com toldo |
| 9 | 48–53 | E a casa 62 já tá em obra, a primeira da rua E. | Casa 62 com pedreiros · "615 → 620" |
| 10 | 53–60 | O próximo marco é 700: campo de futebol. E tem jogador na cidade que já tá esperando faz tempo... | Terreno cercado na rua F com "700" · moradores com bola parados na cerca, olhando pro terreno |
| 11 | 60–66 | O prefeito e o nome da cidade? Continuam chegando... fica de olho. | Prefeitura com "?" · placa da entrada "???" |
| 12 | 66–74 | E tem mais novidade: logo logo vai ter minigame no site! Dá pra jogar dentro da cidade. | Tela de "jogo" em pixel art sobre a praça (controle, "PRESS START") · "MINIGAMES EM BREVE!" |
| 13 | 74–80 | Resultado: 617 moradores, 61 casas, mapa maior e um visual novo. | Resumo em 4 banners, cidade inteira em isométrico |
| 14 | 80–88 | Entra no link da bio, escolhe o teu morador... e prepara o controle! | "LINK NA BIO!" · "VIRA MORADOR" · controle piscando |

**Opcional (morador em destaque do relatório)** — no lugar da fala 10, se quiser citar alguém:
> O próximo marco é 700: campo de futebol. E o Cristiano Ronaldo daqui já avisou na bio: é o melhor jogador da cidade... pena que ainda não tem campo.

**Se no dia de gravar tiver outro número**, troca 617 / 61 casas na fala 13 (e o contador acompanha).

## Texto corrido (pra colar na IA de voz)
A Cidade dos Seguidores... episódio 6!
Da última vez, eram 577 moradores, 57 casas... e só sobravam três lotes.
E eles acabaram rapidinho: casa 58, 59, 60, 61...
Só que o contador passou de 600, e com ele vieram o segundo mercadinho e o posto de saúde.
Mas construir onde? Não tinha mais nenhum lote.
Então a cidade fez o que tinha que fazer: cresceu! O mapa aumentou pra baixo... e ganhou duas ruas novas.
E junto com o mapa novo veio uma evolução: a cidade agora é isométrica! Telhado de verdade, janela, chaminé... dá até pra ver a lateral das casas.
Na rua nova já subiram o segundo mercadinho e o posto de saúde.
E a casa 62 já tá em obra, a primeira da rua E.
O próximo marco é 700: campo de futebol. E tem jogador na cidade que já tá esperando faz tempo...
O prefeito e o nome da cidade? Continuam chegando... fica de olho.
E tem mais novidade: logo logo vai ter minigame no site! Dá pra jogar dentro da cidade.
Resultado: 617 moradores, 61 casas, mapa maior e um visual novo.
Entra no link da bio, escolhe o teu morador... e prepara o controle!

## Notas de produção (plano do mapa novo)
- **Mapa cresce só pra baixo:** altura 480 → **680** (largura continua 270). Nenhuma coordenada antiga muda; `mapa.altura` no `vila.json` vai pra 680.
- **Rua principal** desce até o fim do mapa. **Rua E** em y = 510 e **rua F** em y = 600, com os mesmos lotes das outras ruas. Os lotes novos entram **no fim** da lista.
- As árvores da antiga borda de baixo saem (viram lote). O rio continua descendo pela direita, então **nada do outro lado do rio** (a ponte segue sendo o marco 1000).
- **Marco 600:** 2º mercadinho em `(104, 510, 'a')` e posto de saúde em `(140, 510, 'a')` + `(162, 510, 'a')`, perto da rua principal.
- **Marco 700 (reservado):** campo de futebol nos lotes de baixo da rua F, lado direito: `(140|162|184|206, 600, 'b')`, um terreno só de ~88 x 48.
- **Casas novas:** casa 62 = primeiro lote livre da rua E. Com E + F ficam ~28 lotes de casa → dá até uns 900 inscritos.
- **Placa antiga da entrada** fica onde está (as coordenadas do site dependem dela); a entrada nova da cidade passa a ser a ponta de baixo da rua principal.
- **Isométrico:** mesmo mapa lógico (x, y) do site, só muda o desenho. Casas, igreja, escola, prefeitura, mercadinhos e posto redesenhados com volume; moradores do site com o visual que escolheram e o nome em cima, se aparecerem (a narração não cita ninguém).
- **Moradores novos #578–#617:** `npc_look(id)` normal, `chegou_no_ep = 6`.
- **Site:** vai precisar do mapa isométrico novo (imagem maior) e da conversão de coordenadas (x, y) → tela no `app.js`. Eu deixo pronta a imagem e a fórmula; a parte dos minigames fica contigo.
