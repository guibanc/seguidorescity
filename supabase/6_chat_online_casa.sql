-- =====================================================================
--  Chat público ao vivo + mudar de casa
--  Rode 1 vez no SQL Editor do Supabase (depois dos arquivos 1 a 5).
--  "Quem está online" e as posições dos bonecos usam o Realtime
--  (presença/broadcast) e não precisam de tabela.
-- =====================================================================

-- ---------------------------------------------------------------------
-- CHAT (estilo live: só logado escreve, todo mundo lê)
-- ---------------------------------------------------------------------
create table if not exists chat (
  id          bigserial primary key,
  morador_id  int not null,                       -- quem mandou (sem FK: o nome fica gravado)
  nome        text not null,
  texto       text not null check (char_length(texto) between 1 and 120),
  criado_em   timestamptz not null default now()
);
create index if not exists chat_criado_em on chat (criado_em desc);
alter table chat enable row level security;
drop policy if exists "chat publico" on chat;
create policy "chat publico" on chat for select to anon, authenticated using (true);
grant select on chat to anon, authenticated;

-- entrega em tempo real (Realtime "postgres_changes")
do $$ begin
  if not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'chat') then
    alter publication supabase_realtime add table chat;
  end if;
end $$;

create or replace function enviar_chat(p_token text, p_texto text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); r registros; t text := trim(regexp_replace(coalesce(p_texto,''), '\s+', ' ', 'g')); novo bigint;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if char_length(t) < 1 then return json_build_object('ok',false,'erro','Escreve alguma coisa'); end if;
  if char_length(t) > 120 then return json_build_object('ok',false,'erro','Até 120 letras por mensagem'); end if;
  if not nome_permitido(t) then return json_build_object('ok',false,'erro','Essa mensagem não é permitida'); end if;
  select * into r from registros where morador_id = mid;
  if r.oculto then return json_build_object('ok',false,'erro','Sua conta está em moderação'); end if;
  if exists (select 1 from chat where morador_id = mid and criado_em > now() - interval '2 seconds') then
    return json_build_object('ok',false,'erro','Calma aí, uma mensagem a cada 2 segundos'); end if;
  insert into chat (morador_id, nome, texto) values (mid, r.nome, t) returning id into novo;
  if random() < 0.02 then delete from chat where criado_em < now() - interval '3 days'; end if;   -- limpeza
  return json_build_object('ok',true,'id',novo);
end $$;

-- moderação: apagar mensagens de alguém
--   delete from chat where morador_id = (select morador_id from registros where usuario = 'fulano');

-- ---------------------------------------------------------------------
-- MUDAR DE CASA: troca de lugar com um NPC (morador sem nome) da casa escolhida.
-- Se os 10 da casa já têm nome, não dá. 1 mudança a cada 24 h.
-- As amizades e a sessão acompanham; o visual é guardado pra não mudar de rosto.
-- ---------------------------------------------------------------------
alter table registros add column if not exists casa_trocada_em timestamptz;

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
  -- um morador SEM nome da casa escolhida (trava a linha pra duas pessoas não pegarem o mesmo)
  select m.id into novo from moradores m
   where m.casa = p_casa and not exists (select 1 from registros x where x.morador_id = m.id)
   order by m.id limit 1 for update of m skip locked;
  if novo is null then return json_build_object('ok',false,'erro','Essa casa já está cheia de moradores com nome'); end if;

  update registros set usuario = usuario || '~mudando' where morador_id = mid;      -- libera o @ (é único)
  insert into registros (morador_id, usuario, nome, pin_hash, aparencia, bio, criado_em, tentativas, bloqueado_ate, oculto, casa_trocada_em)
  values (novo, r.usuario, r.nome, r.pin_hash, p_aparencia, r.bio, r.criado_em, 0, null, r.oculto, now());
  -- amizades: quem eu adicionei
  update amizades set de = novo where de = mid;
  -- amizades: quem adicionou a mim / ao NPC trocam de lugar (troca pura, sem conflito)
  update amizades set para = -1   where para = novo;
  update amizades set para = novo where para = mid;
  update amizades set para = mid  where para = -1;
  update sessoes set morador_id = novo where morador_id = mid;
  update chat set morador_id = novo where morador_id = mid;
  delete from registros where morador_id = mid;
  return json_build_object('ok',true,'morador',novo,'casa',p_casa,'antigo',mid);
end $$;

revoke all on function enviar_chat(text,text), trocar_casa(text,int,jsonb) from public, anon, authenticated;
grant execute on function enviar_chat(text,text), trocar_casa(text,int,jsonb) to anon, authenticated;
