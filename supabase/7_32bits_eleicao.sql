-- =====================================================================
--  Ep. 7: personalização maior (32 bits) + ELEIÇÃO PRA PREFEITO
--  Rode 1 vez no SQL Editor do Supabase (depois dos arquivos 1 a 6).
--
--  Fases da eleição (você controla pelo SQL Editor):
--    'candidaturas'  -> quem tem morador se candidata (com um slogan). Ainda não vota.
--    'votacao'       -> todo mundo com morador vota (1 voto, dá pra trocar). Candidaturas fecham.
--    'encerrada'     -> o mais votado vira prefeito(a) e aparece no site.
--  Comandos:
--    update eleicao set fase = 'votacao', atualizado_em = now() where id = 1;   -- abre a votação
--    select encerrar_eleicao();                                                 -- fecha e elege
--    -- nova eleição: delete from votos; delete from candidaturas;
--    --               update eleicao set fase = 'candidaturas', prefeito = null, atualizado_em = now() where id = 1;
-- =====================================================================

-- ---------------------------------------------------------------------
-- visual: opções novas (cabelo, chapéu, estampa, acessório + cor)
-- ---------------------------------------------------------------------
create or replace function aparencia_ok(a jsonb) returns boolean language sql immutable as $$
  select a is null or (
    jsonb_typeof(a) = 'object'
    and not exists (select 1 from jsonb_object_keys(a) k where k not in
        ('pele','cabelo','cor_cabelo','camisa','estampa','camisa2','baixo','cor_baixo','sapato','oculos','chapeu','cor_chapeu','barba','acessorio','cor_acessorio'))
    and coalesce(a->>'pele','')       ~ '^[0-5]$'
    and coalesce(a->>'cabelo','')     in ('curto','raspado','longo','rabo','coque','afro','careca','franja','moicano','trancas','cacheado','topete')
    and coalesce(a->>'cor_cabelo','') ~ '^[0-7]$'
    and coalesce(a->>'camisa','')     ~ '^([0-9]|1[01])$'
    and coalesce(a->>'estampa','')    in ('lisa','listrada','regata','duas_cores','xadrez','time')
    and coalesce(a->>'camisa2','')    ~ '^([0-9]|1[01])$'
    and coalesce(a->>'baixo','')      in ('calca','bermuda','saia','vestido')
    and coalesce(a->>'cor_baixo','')  ~ '^[0-5]$'
    and coalesce(a->>'sapato','')     ~ '^[0-3]$'
    and jsonb_typeof(a->'oculos') = 'boolean'
    and jsonb_typeof(a->'barba')  = 'boolean'
    and (a->'chapeu' is null or a->'chapeu' = 'null'::jsonb or a->>'chapeu' in ('bone','palha','gorro','boina','coroa','bandana'))
    and coalesce(a->>'cor_chapeu','') ~ '^([0-9]|1[01])$'
    and (a->'acessorio' is null or a->>'acessorio' in ('mochila','cachecol','colar','fone','oculos_sol'))
    and (a->'cor_acessorio' is null or a->>'cor_acessorio' ~ '^([0-9]|1[01])$')
  )
$$;

-- ---------------------------------------------------------------------
-- ELEIÇÃO
-- ---------------------------------------------------------------------
create table if not exists eleicao (
  id             int primary key default 1 check (id = 1),
  fase           text not null default 'candidaturas' check (fase in ('candidaturas','votacao','encerrada')),
  prefeito       int,                 -- morador eleito (fica mesmo se ele mudar de casa: atualizado pelo trocar_casa)
  atualizado_em  timestamptz not null default now()
);
insert into eleicao (id) values (1) on conflict (id) do nothing;

create table if not exists candidaturas (
  morador_id  int primary key references registros(morador_id) on delete cascade on update cascade,
  slogan      text not null check (char_length(slogan) between 3 and 80),
  criado_em   timestamptz not null default now()
);
create table if not exists votos (
  eleitor    int primary key references registros(morador_id) on delete cascade on update cascade,
  candidato  int not null references candidaturas(morador_id) on delete cascade on update cascade,
  criado_em  timestamptz not null default now()
);
alter table eleicao      enable row level security;
alter table candidaturas enable row level security;
alter table votos        enable row level security;

-- tudo que o site precisa numa chamada só (quem votou em quem NÃO aparece)
create or replace function eleicao_info()
returns json language sql stable security definer set search_path = public as $$
  select json_build_object(
    'fase', e.fase,
    'prefeito', case when r.oculto then null else e.prefeito end,
    'prefeito_nome', case when r.oculto then null else r.nome end,
    'candidatos', coalesce((
      select json_agg(json_build_object('m', c.morador_id, 'nome', x.nome, 'slogan', c.slogan,
                                        'votos', case when e.fase = 'candidaturas' then null else (select count(*) from votos v where v.candidato = c.morador_id) end)
                      order by (select count(*) from votos v where v.candidato = c.morador_id) desc, c.criado_em)
      from candidaturas c join registros x on x.morador_id = c.morador_id where not x.oculto), '[]'::json))
  from eleicao e left join registros r on r.morador_id = e.prefeito where e.id = 1
$$;

create or replace function candidatar(p_token text, p_slogan text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); s text := trim(regexp_replace(coalesce(p_slogan,''), '\s+', ' ', 'g')); f text;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select fase into f from eleicao where id = 1;
  if f <> 'candidaturas' then return json_build_object('ok',false,'erro','As candidaturas estão fechadas'); end if;
  if (select oculto from registros where morador_id = mid) then return json_build_object('ok',false,'erro','Sua conta está em moderação'); end if;
  if char_length(s) < 3 or char_length(s) > 80 then return json_build_object('ok',false,'erro','O slogan precisa ter de 3 a 80 letras'); end if;
  if not nome_permitido(s) then return json_build_object('ok',false,'erro','Esse slogan não é permitido'); end if;
  insert into candidaturas (morador_id, slogan) values (mid, s)
  on conflict (morador_id) do update set slogan = excluded.slogan;
  return json_build_object('ok',true);
end $$;

create or replace function retirar_candidatura(p_token text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); f text;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select fase into f from eleicao where id = 1;
  if f = 'encerrada' then return json_build_object('ok',false,'erro','A eleição já acabou'); end if;
  delete from candidaturas where morador_id = mid;
  return json_build_object('ok',true);
end $$;

create or replace function votar(p_token text, p_candidato int)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); f text;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select fase into f from eleicao where id = 1;
  if f <> 'votacao' then return json_build_object('ok',false,'erro', case when f = 'candidaturas' then 'A votação ainda não começou' else 'A eleição já acabou' end); end if;
  if not exists (select 1 from candidaturas where morador_id = p_candidato) then return json_build_object('ok',false,'erro','Esse morador não é candidato'); end if;
  insert into votos (eleitor, candidato) values (mid, p_candidato)
  on conflict (eleitor) do update set candidato = excluded.candidato, criado_em = now();
  return json_build_object('ok',true);
end $$;

create or replace function meu_voto(p_token text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  return json_build_object('ok',true,'candidato',(select candidato from votos where eleitor = mid),
                           'candidato_eu', exists (select 1 from candidaturas where morador_id = mid));
end $$;

-- só pelo SQL Editor (o site não chama): fecha a eleição e elege o mais votado
create or replace function encerrar_eleicao()
returns json language plpgsql security definer set search_path = public as $$
declare vencedor int;
begin
  select c.morador_id into vencedor from candidaturas c
   order by (select count(*) from votos v where v.candidato = c.morador_id) desc, c.criado_em limit 1;
  update eleicao set fase = 'encerrada', prefeito = vencedor, atualizado_em = now() where id = 1;
  return json_build_object('ok',true,'prefeito',vencedor);
end $$;

-- ---------------------------------------------------------------------
-- mudar de casa agora leva junto a candidatura, o voto e o cargo de prefeito
-- ---------------------------------------------------------------------
create or replace function trocar_casa(p_token text, p_casa int, p_aparencia jsonb)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); r registros; antiga int; novo int;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select * into r from registros where morador_id = mid;
  if r.casa_trocada_em is not null and r.casa_trocada_em > now() - interval '24 hours' then
    return json_build_object('ok',false,'erro','Você já se mudou hoje. Dá pra mudar de novo amanhã'); end if;
  select casa into antiga from moradores where id = mid;
  if p_casa = antiga then return json_build_object('ok',false,'erro','Você já mora nessa casa'); end if;
  if not exists (select 1 from moradores where casa = p_casa) then return json_build_object('ok',false,'erro','Essa casa não existe'); end if;
  if p_aparencia is null or not aparencia_ok(p_aparencia) then return json_build_object('ok',false,'erro','Aparência inválida'); end if;
  select m.id into novo from moradores m
   where m.casa = p_casa and not exists (select 1 from registros x where x.morador_id = m.id)
   order by m.id limit 1 for update of m skip locked;
  if novo is null then return json_build_object('ok',false,'erro','Essa casa já está cheia de moradores com nome'); end if;

  -- libera o @ (que é único) com um nome provisório válido (antes era '~mudando', que o banco recusava)
  update registros set usuario = '__mud.' || mid where morador_id = mid;
  insert into registros (morador_id, usuario, nome, pin_hash, aparencia, bio, criado_em, tentativas, bloqueado_ate, oculto, casa_trocada_em)
  values (novo, r.usuario, r.nome, r.pin_hash, p_aparencia, r.bio, r.criado_em, 0, null, r.oculto, now());
  update amizades set de = novo where de = mid;
  update amizades set para = -1   where para = novo;
  update amizades set para = novo where para = mid;
  update amizades set para = mid  where para = -1;
  update sessoes set morador_id = novo where morador_id = mid;
  update chat set morador_id = novo where morador_id = mid;
  update candidaturas set morador_id = novo where morador_id = mid;     -- (os votos nele acompanham: on update cascade)
  update votos set eleitor = novo where eleitor = mid;
  update eleicao set prefeito = novo where prefeito = mid;
  delete from registros where morador_id = mid;
  return json_build_object('ok',true,'morador',novo,'casa',p_casa,'antigo',mid);
end $$;

revoke all on function eleicao_info(), candidatar(text,text), retirar_candidatura(text), votar(text,int), meu_voto(text), encerrar_eleicao(), trocar_casa(text,int,jsonb) from public, anon, authenticated;
grant execute on function eleicao_info(), candidatar(text,text), retirar_candidatura(text), votar(text,int), meu_voto(text), trocar_casa(text,int,jsonb) to anon, authenticated;
