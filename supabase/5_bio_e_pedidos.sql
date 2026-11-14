-- =====================================================================
--  Bio (1 frase por morador) + recusar pedido de amizade
--  Rode 1 vez no SQL Editor do Supabase (depois dos arquivos 1 a 4).
-- =====================================================================
alter table registros add column if not exists bio text;
alter table registros drop constraint if exists bio_ok;
alter table registros add constraint bio_ok check (bio is null or char_length(bio) between 1 and 90);

-- view pública agora com a bio (recria a busca, que depende dela)
drop view if exists moradores_publicos cascade;
create view moradores_publicos with (security_invoker = false) as
  select m.id, m.casa, m.chegou_no_ep,
         case when r.oculto then null else r.nome end      as nome,
         case when r.oculto then null else r.usuario end   as usuario,
         case when r.oculto then null else r.aparencia end as aparencia,
         case when r.oculto then null else r.bio end       as bio,
         (r.morador_id is not null) as ocupado
  from moradores m left join registros r on r.morador_id = m.id;
grant select on moradores_publicos to anon, authenticated;

create or replace function buscar(p_texto text)
returns setof moradores_publicos language sql stable security definer set search_path = public as $$
  select * from moradores_publicos
  where ocupado and (nome ilike '%'||replace(replace(p_texto,'%',''),'_','')||'%'
                  or usuario ilike '%'||lower(trim(both '@' from replace(replace(p_texto,'%',''),'_','')))||'%')
  order by nome limit 20
$$;

-- sessão e perfil devolvem a bio também
create or replace function nova_sessao(mid int) returns json language plpgsql security definer
set search_path = public, extensions as $$
declare tok text := encode(gen_random_bytes(24), 'hex'); r registros;
begin
  delete from sessoes where expira_em < now();
  insert into sessoes values (encode(digest(tok, 'sha256'), 'hex'), mid, now() + interval '30 days');
  select * into r from registros where morador_id = mid;
  return json_build_object('ok', true, 'token', tok, 'morador', mid, 'nome', r.nome, 'usuario', r.usuario, 'aparencia', r.aparencia, 'bio', r.bio);
end $$;

create or replace function meu_perfil(p_token text)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); r registros;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select * into r from registros where morador_id = mid;
  return json_build_object('ok',true,'morador',mid,'nome',r.nome,'usuario',r.usuario,'aparencia',r.aparencia,'bio',r.bio);
end $$;

-- SALVAR agora com a frase da bio (p_bio null = não mexe; '' = apaga)
drop function if exists salvar_perfil(text, text, jsonb);
create or replace function salvar_perfil(p_token text, p_nome text, p_aparencia jsonb, p_bio text default null)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
        n text := trim(regexp_replace(coalesce(p_nome,''), '\s+', ' ', 'g'));
        b text := nullif(trim(regexp_replace(coalesce(p_bio,''), '\s+', ' ', 'g')), '');
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if not nome_permitido(n) then return json_build_object('ok',false,'erro','Nome não permitido'); end if;
  if b is not null and not nome_permitido(b) then return json_build_object('ok',false,'erro','Essa frase não é permitida'); end if;
  if char_length(coalesce(b,'')) > 90 then return json_build_object('ok',false,'erro','A frase pode ter até 90 letras'); end if;
  if not aparencia_ok(p_aparencia) then return json_build_object('ok',false,'erro','Aparência inválida'); end if;
  update registros set nome = n, aparencia = p_aparencia,
         bio = case when p_bio is null then bio else b end
   where morador_id = mid;
  return json_build_object('ok',true);
exception when check_violation then return json_build_object('ok',false,'erro','Nome com 2 a 20 letras');
end $$;

-- RECUSAR um pedido de amizade (apaga o "fulano me adicionou")
create or replace function recusar_amizade(p_token text, p_de int)
returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  delete from amizades where de = p_de and para = mid;
  return json_build_object('ok',true);
end $$;

revoke all on function salvar_perfil(text,text,jsonb,text), recusar_amizade(text,int), buscar(text) from public, anon, authenticated;
grant execute on function salvar_perfil(text,text,jsonb,text), recusar_amizade(text,int), buscar(text) to anon, authenticated;
