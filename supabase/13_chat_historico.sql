-- =====================================================================
--  CHAT COM HISTÓRICO (o celular do site)
--  Antes, o envio apagava de vez em quando as mensagens com mais de 3 dias.
--  Agora o chat guarda tudo, pra dar pra ver o histórico inteiro.
--  Rode 1 vez no SQL Editor do Supabase.
--
--  Moderação (apagar mensagens de alguém), se precisar:
--    delete from chat where morador_id = (select morador_id from registros where usuario = 'fulano');
-- =====================================================================

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
  return json_build_object('ok',true,'id',novo);
end $$;

grant execute on function enviar_chat(text,text) to anon, authenticated;
