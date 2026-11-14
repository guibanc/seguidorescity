# Site da Vila — especificação pra programar

Objetivo: o pessoal **acompanha a vila** (mapa vivo em 16 bits, mesmo visual dos vídeos) e cada inscrito **registra o nome dele em um morador que já existe**, depois **busca** esse morador e vê **a rotina dele** ao longo do dia.

---

## 1. Arquitetura

| Parte | Onde | Por quê |
|---|---|---|
| Site (HTML + JS + imagens) | **Vercel**, **Netlify** ou **Cloudflare Pages** (grátis) | É tudo estático, sobe só a pasta |
| Banco + regras de login | **Supabase** (plano grátis) | Postgres, funções SQL, `pgcrypto` pro hash do PIN |
| Arte e dados da vila | arquivos em `site/img` e `site/dados` | Gerados pelo `codigo/exportar_site.py` a cada episódio |

O site **não** precisa de servidor próprio: o navegador lê os JSON/PNG estáticos e chama **funções RPC** do Supabase com a chave `anon`.

```
site/
  index.html            (você cria)
  app.js                (você cria)
  img/vila_dia.png      mapa sem moradores, dia   (540x960)
  img/vila_noite.png    mapa sem moradores, noite (540x960)
  img/moradores.png     atlas com todos os moradores
  dados/vila.json       casas, ruas, pontos (mercadinho, praça...), info do atlas
  dados/moradores.json  aparência, casa e agenda de cada morador
  dados/novos_moradores.sql   INSERT dos moradores pro Supabase
```

---

## 2. Telas

1. **Vila (home)**
   - Canvas com o mapa. Arrastar = mover, pinça/roda = zoom (1x a 4x). Use `imageSmoothingEnabled = false` pra manter o pixel art nítido.
   - Topo: contador (seguidores / casas) e o próximo marco ("faltam 30 pra escola").
   - Relógio da vila = **hora de Brasília** (`America/Sao_Paulo`). Das 18h40 às 6h usa `vila_noite.png`.
   - Toca num morador → abre a **ficha**.
2. **Ficha do morador**: retrato grande (sprite ampliado), nome (ou "Morador #205 — livre"), @user, casa, "chegou no episódio X", **o que está fazendo agora** e a agenda do dia. Botão "Seguir na vila" (a câmera acompanha) e, se estiver livre, "Esse é meu!".
3. **Registrar**: escolhe o morador (clicando no mapa ou "me dá um aleatório"), digita **nome**, **@user** e **PIN de 6 dígitos** (2 vezes).
4. **Buscar**: campo "procure seu nome ou @". Resultado → câmera voa até o morador e começa a seguir.
5. **Entrar**: @user + PIN → pode **trocar o nome** que aparece no boneco.
6. Link direto: `site.com/?m=205` abre a vila já seguindo o morador 205 (é o link que a pessoa compartilha).

---

## 3. Banco (Supabase) — copiar e colar no SQL Editor

```sql
create extension if not exists pgcrypto;

-- moradores que existem na vila (vem do novos_moradores.sql de cada episódio)
create table moradores (
  id            int primary key,
  casa          int not null,
  chegou_no_ep  int not null
);

-- quem registrou qual morador
create table registros (
  morador_id     int primary key references moradores(id),
  usuario        text not null unique,            -- @user, sem o @, minúsculo
  nome           text not null,                   -- nome que aparece no boneco
  pin_hash       text not null,                   -- bcrypt do PIN
  criado_em      timestamptz not null default now(),
  tentativas     int not null default 0,
  bloqueado_ate  timestamptz,
  oculto         boolean not null default false,   -- moderação: some do site
  constraint usuario_ok check (usuario ~ '^[a-z0-9_.]{3,20}$'),
  constraint nome_ok    check (char_length(nome) between 2 and 20)
);

-- sessões curtas pra editar (token aleatório; guarda só o hash)
create table sessoes (
  token_hash  text primary key,
  morador_id  int not null references registros(morador_id) on delete cascade,
  expira_em   timestamptz not null
);

-- ninguém lê/escreve as tabelas direto: só pelas funções abaixo
alter table moradores enable row level security;
alter table registros enable row level security;
alter table sessoes   enable row level security;

-- leitura pública (sem PIN, sem nada sensível)
create view moradores_publicos with (security_invoker = false) as
  select m.id, m.casa, m.chegou_no_ep,
         case when r.oculto then null else r.nome end    as nome,
         case when r.oculto then null else r.usuario end as usuario,
         (r.morador_id is not null) as ocupado
  from moradores m left join registros r on r.morador_id = m.id;
grant select on moradores_publicos to anon;

-- palavras bloqueadas (completa a lista)
create table palavras_bloqueadas (p text primary key);
alter table palavras_bloqueadas enable row level security;
insert into palavras_bloqueadas values ('porra'),('caralho'),('merda'),('puta'),('fdp'),('buceta'),('cu') on conflict do nothing;

create or replace function nome_permitido(t text) returns boolean language sql stable as $$
  select not exists (
    select 1 from palavras_bloqueadas
    where lower(translate(t,'áàâãéêíóôõúç@4310$','aaaaeeiooouca aeios')) like '%'||p||'%')
$$;

-- REGISTRAR: pega um morador livre
create or replace function registrar(p_morador int, p_usuario text, p_nome text, p_pin text)
returns json language plpgsql security definer set search_path = public as $$
declare u text := lower(trim(both '@' from trim(p_usuario)));
        n text := trim(regexp_replace(p_nome, '\s+', ' ', 'g'));
begin
  if p_pin !~ '^[0-9]{6}$' then return json_build_object('ok',false,'erro','PIN precisa ter 6 números'); end if;
  if p_pin in ('000000','111111','123456','654321','121212') then return json_build_object('ok',false,'erro','PIN muito fácil'); end if;
  if not nome_permitido(n) or not nome_permitido(u) then return json_build_object('ok',false,'erro','Nome não permitido'); end if;
  if not exists (select 1 from moradores where id = p_morador) then return json_build_object('ok',false,'erro','Morador não existe'); end if;
  insert into registros (morador_id, usuario, nome, pin_hash)
  values (p_morador, u, n, crypt(p_pin, gen_salt('bf', 8)));
  return json_build_object('ok',true,'morador',p_morador);
exception
  when unique_violation then
    if exists (select 1 from registros where usuario = u) then return json_build_object('ok',false,'erro','Esse @ já está em uso'); end if;
    return json_build_object('ok',false,'erro','Esse morador já tem dono, escolhe outro');
  when check_violation then return json_build_object('ok',false,'erro','@ (3-20 letras/números) ou nome (2-20) inválido');
end $$;

-- ENTRAR: @user + PIN → token por 7 dias. 5 erros = bloqueia 15 min
create or replace function entrar(p_usuario text, p_pin text)
returns json language plpgsql security definer set search_path = public as $$
declare r registros; tok text;
begin
  select * into r from registros where usuario = lower(trim(both '@' from trim(p_usuario)));
  if not found then return json_build_object('ok',false,'erro','@ ou PIN errado'); end if;
  if r.bloqueado_ate is not null and r.bloqueado_ate > now() then
    return json_build_object('ok',false,'erro','Muitas tentativas. Tenta de novo em alguns minutos'); end if;
  if r.pin_hash <> crypt(p_pin, r.pin_hash) then
    update registros set tentativas = tentativas + 1,
           bloqueado_ate = case when tentativas + 1 >= 5 then now() + interval '15 minutes' end,
           tentativas    = case when tentativas + 1 >= 5 then 0 else tentativas + 1 end
     where morador_id = r.morador_id;
    return json_build_object('ok',false,'erro','@ ou PIN errado');
  end if;
  update registros set tentativas = 0, bloqueado_ate = null where morador_id = r.morador_id;
  tok := encode(gen_random_bytes(24),'hex');
  insert into sessoes values (encode(digest(tok,'sha256'),'hex'), r.morador_id, now() + interval '7 days');
  return json_build_object('ok',true,'token',tok,'morador',r.morador_id,'nome',r.nome);
end $$;

-- TROCAR NOME (precisa do token do entrar)
create or replace function trocar_nome(p_token text, p_nome text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int; n text := trim(regexp_replace(p_nome, '\s+', ' ', 'g'));
begin
  select morador_id into mid from sessoes
   where token_hash = encode(digest(p_token,'sha256'),'hex') and expira_em > now();
  if not found then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if not nome_permitido(n) then return json_build_object('ok',false,'erro','Nome não permitido'); end if;
  update registros set nome = n where morador_id = mid;
  return json_build_object('ok',true);
exception when check_violation then return json_build_object('ok',false,'erro','Nome com 2 a 20 letras');
end $$;

-- BUSCA (nome ou @), máximo 20 resultados
create or replace function buscar(p_texto text)
returns setof moradores_publicos language sql stable security definer set search_path = public as $$
  select * from moradores_publicos
  where ocupado and (nome ilike '%'||p_texto||'%' or usuario ilike '%'||lower(trim(both '@' from p_texto))||'%')
  order by nome limit 20
$$;

revoke all on function registrar, entrar, trocar_nome, buscar, nome_permitido from public;
grant execute on function registrar, entrar, trocar_nome, buscar to anon;
```

Depois rode `dados/novos_moradores.sql` (insere os moradores 1 a 370). A cada episódio novo, rode o `novos_moradores.sql` novo (ele ignora quem já existe).

**Moderação:** no painel do Supabase, `update registros set oculto = true where usuario = 'fulano';` esconde o nome. Pra liberar o morador de novo: `delete from registros where usuario = 'fulano';`.

**Chamadas no JS (supabase-js):**
```js
const { data } = await sb.rpc('registrar', { p_morador: 205, p_usuario: '@gui', p_nome: 'Guilherme', p_pin: '583920' })
const { data } = await sb.rpc('entrar',    { p_usuario: '@gui', p_pin: '583920' })   // guarda data.token no localStorage
const { data } = await sb.rpc('trocar_nome', { p_token, p_nome: 'Gui' })
const { data } = await sb.rpc('buscar', { p_texto: 'gui' })
const { data } = await sb.from('moradores_publicos').select('id,nome,usuario,ocupado')   // carrega os nomes 1x ao abrir
```

---

## 4. Arquivos de dados

### `dados/vila.json`
- `mapa`: 540x960 px (as coordenadas dos JSON já estão nessa escala).
- `lista_casas[]`: `casa`, `lote` (canto do sprite), `porta`, `ponto_na_rua`, `rua` (A/B/C), `moradores` (ids que moram nela; 10 por casa).
- `pontos`: `mercadinho.porta/rua`, `vendinha.porta/rua`, `praca.area` (retângulo) e `praca.bancos`, `igreja.porta`, `entrada`.
- `ruas`: segmentos `principal` (vertical, x=263) e `A`, `B`, `C` (horizontais).
- `atlas`: como achar cada morador no `moradores.png` (ver abaixo).

### `img/moradores.png` (atlas)
- 10 moradores por linha. Cada morador é uma célula de **48x72**: 4 linhas de direção (`down`, `left`, `right`, `up`) × 4 quadros de 12x18.
- Morador `id` → `col = (id-1) % 10`, `lin = floor((id-1)/10)` (também vem pronto em `moradores.json → atlas`).
- Quadro: `sx = col*48 + quadro*12`, `sy = lin*72 + dir*18`. Desenha com o **pé** em (`x-6`, `y-14`) — `ancora_pes: [6,14]`.
- Parado = quadro 0 da direção `down`. Andando = quadros 0,1,2,3 a ~8 por segundo.

### `dados/moradores.json` (um por morador)
```json
{ "id": 205, "casa": 21, "chegou_no_ep": 1,
  "aparencia": { "pele": 3, "cabelo": "rabo", ... },     // só informativo; o desenho já está no atlas
  "atlas": { "col": 4, "lin": 20 },
  "velocidade": 0.98,
  "agenda": [ { "de":"00:00","ate":"07:45","onde":"casa","faz":"dormindo" },
              { "de":"08:25","ate":"09:05","onde":"mercadinho","faz":"fazendo compras" }, ... ],
  "domingo": { "de":"09:00","duracao_min":60,"onde":"igreja" }   // ou null
}
```
`onde` ∈ `casa`, `mercadinho`, `vendinha`, `praca`, `passeio_rua`, `igreja`. Os buracos entre um bloco e outro são **o tempo andando** de um lugar pro outro.

---

## 5. Simulação (o coração do site)

Regra de ouro: **a posição de cada morador é uma função da hora** — `pos = f(id, horaAtual)`. Nada é salvo nem sincronizado; todo mundo que abre o site vê o mesmo morador no mesmo lugar, na mesma hora.

```js
function estado(m, agoraMin) {           // agoraMin = minutos desde 00:00 (Brasília)
  const blocos = agendaDoDia(m, diaDaSemana)          // agenda + igreja no domingo
  const atual = blocos.find(b => agoraMin >= b.de && agoraMin < b.ate)
  if (atual) return { onde: atual.onde, faz: atual.faz, pos: posNoLugar(m, atual, agoraMin) }
  // entre dois blocos: andando do lugar anterior pro próximo
  const ant = ultimoAntes(blocos, agoraMin), prox = primeiroDepois(blocos, agoraMin)
  const f = (agoraMin - ant.ate) / (prox.de - ant.ate)
  return { onde: 'andando', faz: 'indo pra ' + nomeBonito(prox.onde), pos: noCaminho(caminho(m, ant.onde, prox.onde), f) }
}
```

- **Caminho** = sempre pelas ruas: `porta da casa → ponto_na_rua → rua principal (x=263) → rua do destino → porta do destino`. São no máximo 5 pontos; anda em linha reta entre eles. A direção do sprite sai do sentido do movimento.
- **Dentro dos lugares:**
  - `casa`, `mercadinho`, `vendinha`, `igreja` → **não desenha** o morador (ele está lá dentro). A ficha mostra "dentro do mercadinho".
  - `praca` → ponto aleatório fixo dentro de `praca.area` (use `seed = id`), com um vaivém lento de ±4 px. Alguns sentam nos `bancos`.
  - `passeio_rua` → vai e volta devagar num trecho da rua da casa dele (amplitude 20 a 80 px, `seed = id`).
- **Variação:** some `(id*37) % 11 - 5` minutos em todos os horários de cada dia (`seed = id + dia`), pra rotina não ser idêntica todo dia.
- **Noite:** das 18h40 às 6h troca pra `vila_noite.png`. Quase todo mundo está em casa (é o que a agenda manda), então a rua esvazia sozinha.

### Limite de bonecos na tela (leveza)
- Calcule o estado de todos (é só conta, é leve), mas **desenhe no máximo 50**:
  1. o morador que a pessoa está seguindo (sempre);
  2. moradores **registrados** que estão na área visível;
  3. o resto da área visível, ordenado por um "sorteio fixo" (`hash(id)`), até completar 50.
- O sorteio fixo faz os mesmos bonecos continuarem na tela de um frame pro outro, sem piscar.
- Redesenhe a 30 fps só enquanto a página está visível (`requestAnimationFrame`); com a aba escondida, pare.

### Nome em cima do boneco
- Mostra o nome só de quem está **registrado** e só com zoom ≥ 2x (senão vira poluição). O morador seguido sempre tem o nome, numa plaquinha vermelha com seta (igual ao vídeo) e um anel amarelo no pé.

---

## 6. A cada episódio novo

1. Eu atualizo o projeto e rodo `python3 codigo/exportar_site.py site`.
2. Você sobe a pasta `site/img` e `site/dados` novas na hospedagem.
3. Roda o `dados/novos_moradores.sql` novo no Supabase.

Os registros antigos continuam: o morador 205 é sempre o 205, na mesma casa, com a mesma aparência.

---

## 7. Checklist da v1

- [ ] Mapa com zoom/arrastar, dia/noite pela hora de Brasília
- [ ] Moradores andando pela agenda, máx. 50 desenhados
- [ ] Ficha do morador (o que está fazendo agora + agenda)
- [ ] Registrar (escolher no mapa ou aleatório) com @user + PIN
- [ ] Buscar por nome/@ → câmera vai até ele e segue
- [ ] Link `?m=ID`
- [ ] Entrar e trocar nome
- [ ] Filtro de palavrão + `oculto` pra moderação

Depois: profissão do morador (muda a roupa e o lugar de trabalho na agenda), puxar comentários do YouTube e responder com boas-vindas.
