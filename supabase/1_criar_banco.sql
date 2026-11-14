-- =====================================================================
--  A Cidade dos Seguidores — banco do site (Supabase)
--  Cole TUDO no SQL Editor do Supabase e clique em "Run". Só precisa 1 vez.
--  Depois rode site/dados/novos_moradores.sql (e de novo a cada episódio).
-- =====================================================================
create extension if not exists pgcrypto with schema extensions;
set search_path = public, extensions;

-- moradores que existem na vila (vem do novos_moradores.sql de cada episódio)
create table if not exists moradores (
  id            int primary key,
  casa          int not null,
  chegou_no_ep  int not null
);

-- quem registrou qual morador
create table if not exists registros (
  morador_id     int primary key references moradores(id),
  usuario        text not null unique,            -- @user, sem o @, minúsculo
  nome           text not null,                   -- nome que aparece no boneco
  pin_hash       text not null,                   -- bcrypt do PIN
  aparencia      jsonb,                           -- personalização (null = visual original)
  criado_em      timestamptz not null default now(),
  tentativas     int not null default 0,
  bloqueado_ate  timestamptz,
  oculto         boolean not null default false,  -- moderação: some do site
  constraint usuario_ok check (usuario ~ '^[a-z0-9_.]{3,20}$'),
  constraint nome_ok    check (char_length(nome) between 2 and 20)
);

-- sessões curtas pra editar (token aleatório; guarda só o hash)
create table if not exists sessoes (
  token_hash  text primary key,
  morador_id  int not null references registros(morador_id) on delete cascade,
  expira_em   timestamptz not null
);

-- amizades: "de" adicionou "para". Se os dois se adicionaram = amizade de verdade
create table if not exists amizades (
  de         int not null references registros(morador_id) on delete cascade,
  para       int not null references moradores(id),
  criado_em  timestamptz not null default now(),
  primary key (de, para),
  constraint nao_eu check (de <> para)
);

-- palavras proibidas em nome/@ (palavrões, ofensas, termos pejorativos).
-- A lista vem do arquivo 2_palavras_bloqueadas.sql (rode ele depois deste).
-- Até 4 letras ou começando com "=": só palavra inteira ("cu" não barra "Marcus").
-- O resto: em qualquer lugar, ignorando acento, pontos, espaços, números e letras repetidas.
create table if not exists palavras_bloqueadas (p text primary key);

-- ninguém lê/escreve as tabelas direto: só pela view e pelas funções abaixo
alter table moradores enable row level security;
alter table registros enable row level security;
alter table sessoes   enable row level security;
alter table amizades  enable row level security;
alter table palavras_bloqueadas enable row level security;

-- leitura pública (sem PIN, sem nada sensível)
drop view if exists moradores_publicos cascade;
create view moradores_publicos with (security_invoker = false) as
  select m.id, m.casa, m.chegou_no_ep,
         case when r.oculto then null else r.nome end      as nome,
         case when r.oculto then null else r.usuario end   as usuario,
         case when r.oculto then null else r.aparencia end as aparencia,
         (r.morador_id is not null) as ocupado
  from moradores m left join registros r on r.morador_id = m.id;
grant select on moradores_publicos to anon;

-- ---------------------------------------------------------------------
-- regras
-- ---------------------------------------------------------------------
create or replace function nome_permitido(t text) returns boolean language sql stable
set search_path = public as $$
  -- igual ao supabase/filtro_nomes.js:
  -- tira acento, troca 4->a 3->e 1->i 0->o 5->s 7->t $->s @->a *->u, junta letras repetidas (puuuta -> puta)
  with n0 as (select regexp_replace(translate(lower(coalesce(t,'')), 'áàâãäéêëíïóôõöúüç@43105$7*', 'aaaaaeeeiioooouuc' || 'aaeiosstu'), '(.)\1+', '\1', 'g') as s),
       n  as (select s, regexp_replace(s, '[^a-z]', '', 'g') as junto,
                     array(select regexp_replace(x, '[^a-z]', '', 'g') from regexp_split_to_table(s, '\s+') x) as tokens from n0),
       b  as (select p like '=%' as igual, regexp_replace(ltrim(p, '='), '(.)\1+', '\1', 'g') as p from palavras_bloqueadas)
  select not exists (
    select 1 from b, n
    where case when b.igual or length(replace(b.p, ' ', '')) <= 4
               then n.s ~ ('(^|[^a-z])' || b.p || '([^a-z]|$)') or b.p = any(n.tokens) or n.junto = b.p
               else n.junto like '%' || replace(b.p, ' ', '') || '%' end)
$$;

create or replace function aparencia_ok(a jsonb) returns boolean language sql immutable as $$
  select a is null or (
    jsonb_typeof(a) = 'object'
    and not exists (select 1 from jsonb_object_keys(a) k where k not in
        ('pele','cabelo','cor_cabelo','camisa','estampa','camisa2','baixo','cor_baixo','sapato','oculos','chapeu','cor_chapeu','barba'))
    and coalesce(a->>'pele','')       ~ '^[0-5]$'
    and coalesce(a->>'cabelo','')     in ('curto','raspado','longo','rabo','coque','afro','careca','franja')
    and coalesce(a->>'cor_cabelo','') ~ '^[0-7]$'
    and coalesce(a->>'camisa','')     ~ '^([0-9]|1[01])$'
    and coalesce(a->>'estampa','')    in ('lisa','listrada','regata','duas_cores')
    and coalesce(a->>'camisa2','')    ~ '^([0-9]|1[01])$'
    and coalesce(a->>'baixo','')      in ('calca','bermuda','saia','vestido')
    and coalesce(a->>'cor_baixo','')  ~ '^[0-5]$'
    and coalesce(a->>'sapato','')     ~ '^[0-3]$'
    and jsonb_typeof(a->'oculos') = 'boolean'
    and jsonb_typeof(a->'barba')  = 'boolean'
    and (a->'chapeu' is null or a->'chapeu' = 'null'::jsonb or a->>'chapeu' in ('bone','palha','gorro'))
    and coalesce(a->>'cor_chapeu','') ~ '^([0-9]|1[01])$'
  )
$$;

-- token -> id do morador (ou null)
create or replace function sessao_morador(p_token text) returns int language sql stable security definer
set search_path = public, extensions as $$
  select morador_id from sessoes
  where token_hash = encode(digest(coalesce(p_token,''), 'sha256'), 'hex') and expira_em > now()
$$;

-- cria sessão de 30 dias e devolve o perfil
create or replace function nova_sessao(mid int) returns json language plpgsql security definer
set search_path = public, extensions as $$
declare tok text := encode(gen_random_bytes(24), 'hex'); r registros;
begin
  delete from sessoes where expira_em < now();
  insert into sessoes values (encode(digest(tok, 'sha256'), 'hex'), mid, now() + interval '30 days');
  select * into r from registros where morador_id = mid;
  return json_build_object('ok', true, 'token', tok, 'morador', mid, 'nome', r.nome, 'usuario', r.usuario, 'aparencia', r.aparencia);
end $$;

-- ---------------------------------------------------------------------
-- REGISTRAR: pega um morador livre (já entra logado)
-- ---------------------------------------------------------------------
drop function if exists registrar(int, text, text, text);
create or replace function registrar(p_morador int, p_usuario text, p_nome text, p_pin text, p_aparencia jsonb default null)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare u text := lower(trim(both '@' from trim(coalesce(p_usuario,''))));
        n text := trim(regexp_replace(coalesce(p_nome,''), '\s+', ' ', 'g'));
begin
  if coalesce(p_pin,'') !~ '^[0-9]{6}$' then return json_build_object('ok',false,'erro','PIN precisa ter 6 números'); end if;
  if p_pin in ('000000','111111','222222','333333','444444','555555','666666','777777','888888','999999','123456','654321','121212')
    then return json_build_object('ok',false,'erro','PIN muito fácil'); end if;
  if not nome_permitido(n) or not nome_permitido(u) then return json_build_object('ok',false,'erro','Nome não permitido'); end if;
  if not aparencia_ok(p_aparencia) then return json_build_object('ok',false,'erro','Aparência inválida'); end if;
  if not exists (select 1 from moradores where id = p_morador) then return json_build_object('ok',false,'erro','Morador não existe'); end if;
  insert into registros (morador_id, usuario, nome, pin_hash, aparencia)
  values (p_morador, u, n, crypt(p_pin, gen_salt('bf', 8)), p_aparencia);
  return nova_sessao(p_morador);
exception
  when unique_violation then
    if exists (select 1 from registros where usuario = u) then return json_build_object('ok',false,'erro','Esse @ já está em uso'); end if;
    return json_build_object('ok',false,'erro','Esse morador já tem dono, escolhe outro');
  when check_violation then return json_build_object('ok',false,'erro','@ (3-20 letras/números) ou nome (2-20) inválido');
end $$;

-- ENTRAR: @user + PIN -> token. 5 erros = bloqueia 15 min
create or replace function entrar(p_usuario text, p_pin text)
returns json language plpgsql security definer set search_path = public, extensions as $$
declare r registros;
begin
  select * into r from registros where usuario = lower(trim(both '@' from trim(coalesce(p_usuario,''))));
  if not found then return json_build_object('ok',false,'erro','@ ou PIN errado'); end if;
  if r.bloqueado_ate is not null and r.bloqueado_ate > now() then
    return json_build_object('ok',false,'erro','Muitas tentativas. Tenta de novo em alguns minutos'); end if;
  if r.pin_hash <> crypt(coalesce(p_pin,''), r.pin_hash) then
    update registros set
           bloqueado_ate = case when tentativas + 1 >= 5 then now() + interval '15 minutes' end,
           tentativas    = case when tentativas + 1 >= 5 then 0 else tentativas + 1 end
     where morador_id = r.morador_id;
    return json_build_object('ok',false,'erro','@ ou PIN errado');
  end if;
  update registros set tentativas = 0, bloqueado_ate = null where morador_id = r.morador_id;
  return nova_sessao(r.morador_id);
end $$;

-- confere se o token ainda vale (ao abrir o site)
create or replace function meu_perfil(p_token text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); r registros;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select * into r from registros where morador_id = mid;
  return json_build_object('ok',true,'morador',mid,'nome',r.nome,'usuario',r.usuario,'aparencia',r.aparencia);
end $$;

-- SALVAR (botão "Salvar" do editor): nome + aparência juntos
create or replace function salvar_perfil(p_token text, p_nome text, p_aparencia jsonb)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); n text := trim(regexp_replace(coalesce(p_nome,''), '\s+', ' ', 'g'));
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if not nome_permitido(n) then return json_build_object('ok',false,'erro','Nome não permitido'); end if;
  if not aparencia_ok(p_aparencia) then return json_build_object('ok',false,'erro','Aparência inválida'); end if;
  update registros set nome = n, aparencia = p_aparencia where morador_id = mid;
  return json_build_object('ok',true);
exception when check_violation then return json_build_object('ok',false,'erro','Nome com 2 a 20 letras');
end $$;

create or replace function sair(p_token text)
returns json language sql security definer set search_path = public, extensions as $$
  delete from sessoes where token_hash = encode(digest(coalesce(p_token,''), 'sha256'), 'hex');
  select json_build_object('ok', true);
$$;

-- ---------------------------------------------------------------------
-- AMIZADES
-- ---------------------------------------------------------------------
create or replace function adicionar_amigo(p_token text, p_amigo int)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if mid = p_amigo then return json_build_object('ok',false,'erro','Esse é você :)'); end if;
  if not exists (select 1 from moradores where id = p_amigo) then return json_build_object('ok',false,'erro','Morador não existe'); end if;
  if (select count(*) from amizades where de = mid) >= 100 then return json_build_object('ok',false,'erro','Limite de 100 amigos'); end if;
  insert into amizades (de, para) values (mid, p_amigo) on conflict do nothing;
  return json_build_object('ok',true,'mutuo', exists (select 1 from amizades where de = p_amigo and para = mid));
end $$;

create or replace function remover_amigo(p_token text, p_amigo int)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  delete from amizades where de = mid and para = p_amigo;
  return json_build_object('ok',true);
end $$;

-- lista pública: quem o morador adicionou e quem adicionou ele (some quem está oculto)
create or replace function amigos_de(p_morador int)
returns json language sql stable security definer set search_path = public as $$
  select json_build_object(
    'segue',      coalesce((select json_agg(a.para) from amizades a left join registros r on r.morador_id = a.para
                            where a.de = p_morador and not coalesce(r.oculto,false)), '[]'::json),
    'seguidores', coalesce((select json_agg(a.de) from amizades a join registros r on r.morador_id = a.de
                            where a.para = p_morador and not r.oculto), '[]'::json))
$$;

-- BUSCA (nome ou @), máximo 20 resultados
drop function if exists buscar(text);
create or replace function buscar(p_texto text)
returns setof moradores_publicos language sql stable security definer set search_path = public as $$
  select * from moradores_publicos
  where ocupado and (nome ilike '%'||replace(replace(p_texto,'%',''),'_','')||'%'
                  or usuario ilike '%'||lower(trim(both '@' from replace(replace(p_texto,'%',''),'_','')))||'%')
  order by nome limit 20
$$;

-- permissões: o site (anon) só pode chamar estas funções
revoke all on function registrar(int,text,text,text,jsonb), entrar(text,text), meu_perfil(text), salvar_perfil(text,text,jsonb),
  sair(text), adicionar_amigo(text,int), remover_amigo(text,int), amigos_de(int), buscar(text),
  nome_permitido(text), aparencia_ok(jsonb), sessao_morador(text), nova_sessao(int) from public, anon, authenticated;
grant execute on function registrar(int,text,text,text,jsonb), entrar(text,text), meu_perfil(text), salvar_perfil(text,text,jsonb),
  sair(text), adicionar_amigo(text,int), remover_amigo(text,int), amigos_de(int), buscar(text) to anon, authenticated;
