-- =====================================================================
--  VOTAÇÃO PRA PREFEITO (ep. 9)
--  - fica aberta por 72 HORAS; nesse tempo ainda dá pra se candidatar
--  - só vota quem está logado (com morador)
--  - 1 voto por morador e NÃO dá pra trocar
--  - os votos aparecem contando ao vivo pra todo mundo
--  - durante a votação ninguém retira a candidatura (perderia os votos)
--  - quando acaba o prazo, o mais votado vira prefeito sozinho
--    (empate: ganha quem se candidatou primeiro)
--  Rode 1 vez no SQL Editor do Supabase. A última linha ABRE a votação.
-- =====================================================================

alter table eleicao add column if not exists termina_em timestamptz;

-- se o prazo passou, encerra e elege o mais votado (chamado por todas as funções da eleição)
create or replace function fechar_eleicao_se_acabou()
returns void language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from eleicao where id = 1 and fase = 'votacao' and termina_em is not null and now() >= termina_em) then
    perform encerrar_eleicao();
  end if;
end $$;

-- o que o site lê (agora com o prazo)
create or replace function eleicao_info()
returns json language plpgsql volatile security definer set search_path = public as $$
declare r json;
begin
  perform fechar_eleicao_se_acabou();
  select json_build_object(
    'fase', e.fase,
    'termina_em', e.termina_em,
    'prefeito', case when r2.oculto then null else e.prefeito end,
    'prefeito_nome', case when r2.oculto then null else r2.nome end,
    'candidatos', coalesce((
      select json_agg(json_build_object('m', c.morador_id, 'nome', x.nome, 'slogan', c.slogan,
                                        'votos', case when e.fase = 'candidaturas' then null else (select count(*) from votos v where v.candidato = c.morador_id) end)
                      order by (select count(*) from votos v where v.candidato = c.morador_id) desc, c.criado_em)
      from candidaturas c join registros x on x.morador_id = c.morador_id where not x.oculto), '[]'::json))
  into r
  from eleicao e left join registros r2 on r2.morador_id = e.prefeito where e.id = 1;
  return r;
end $$;

-- se candidatar: aberto nas candidaturas E durante a votação
create or replace function candidatar(p_token text, p_slogan text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); s text := trim(regexp_replace(coalesce(p_slogan,''), '\s+', ' ', 'g')); f text;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  perform fechar_eleicao_se_acabou();
  select fase into f from eleicao where id = 1;
  if f not in ('candidaturas','votacao') then return json_build_object('ok',false,'erro','A eleição já acabou'); end if;
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
  if f <> 'candidaturas' then return json_build_object('ok',false,'erro','Durante a votação não dá pra retirar a candidatura'); end if;
  delete from candidaturas where morador_id = mid;
  return json_build_object('ok',true);
end $$;

create or replace function votar(p_token text, p_candidato int)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); f text; ja int;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre com seu morador pra votar'); end if;
  perform fechar_eleicao_se_acabou();
  select fase into f from eleicao where id = 1;
  if f <> 'votacao' then return json_build_object('ok',false,'erro', case when f = 'candidaturas' then 'A votação ainda não começou' else 'A votação já acabou' end); end if;
  if (select oculto from registros where morador_id = mid) then return json_build_object('ok',false,'erro','Sua conta está em moderação'); end if;
  if not exists (select 1 from candidaturas where morador_id = p_candidato) then return json_build_object('ok',false,'erro','Esse morador não é candidato'); end if;
  select candidato into ja from votos where eleitor = mid;
  if ja is not null then return json_build_object('ok',false,'erro','Você já votou. O voto não pode ser trocado.'); end if;
  insert into votos (eleitor, candidato) values (mid, p_candidato) on conflict (eleitor) do nothing;
  if not found then return json_build_object('ok',false,'erro','Você já votou. O voto não pode ser trocado.'); end if;
  return json_build_object('ok',true);
end $$;

grant execute on function eleicao_info(), candidatar(text,text), retirar_candidatura(text), votar(text,int) to anon, authenticated;
revoke execute on function fechar_eleicao_se_acabou(), encerrar_eleicao() from public, anon, authenticated;

-- ABRE A VOTAÇÃO: 72 horas a partir de agora
update eleicao set fase = 'votacao', termina_em = now() + interval '72 hours', atualizado_em = now() where id = 1;
