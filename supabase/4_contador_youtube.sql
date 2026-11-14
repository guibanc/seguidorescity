-- =====================================================================
--  Contador AUTOMÁTICO pelo YouTube (a cada 10 minutos)
--  Antes: rode 3_contador.sql e guarde a chave do Google no Vault
--  (veja COMO_PUBLICAR.md). Depois cole este arquivo inteiro e clique Run.
--
--  Como funciona: a cada 10 min o banco lê a resposta do pedido anterior,
--  grava o número em "contador" e já faz o próximo pedido ao YouTube.
--  A chave fica no Vault (cofre do Supabase), nunca no site.
-- =====================================================================
create extension if not exists pg_net;
create extension if not exists pg_cron;

create table if not exists contador_config (
  id             int primary key default 1 check (id = 1),
  canal_id       text not null,
  ultimo_pedido  bigint,
  ultimo_erro    text,
  conferido_em   timestamptz
);
alter table contador_config enable row level security;   -- ninguém de fora lê
insert into contador_config (id, canal_id) values (1, 'UC_EHVoaQsT02LtcTEb1pqdw')
on conflict (id) do update set canal_id = excluded.canal_id;

create or replace function contador_youtube() returns void
language plpgsql security definer set search_path = public, extensions as $$
declare
  cfg contador_config; resp record; chave text; dados jsonb; n bigint;
begin
  select * into cfg from contador_config where id = 1;

  -- 1) resposta do pedido anterior
  if cfg.ultimo_pedido is not null then
    select status_code, content, error_msg into resp from net._http_response where id = cfg.ultimo_pedido;
    if found then
      if resp.status_code = 200 then
        dados := resp.content::jsonb;
        if coalesce((dados #>> '{items,0,statistics,hiddenSubscriberCount}')::boolean, false) then
          update contador_config set ultimo_erro = 'O canal está escondendo o número de inscritos', conferido_em = now() where id = 1;
        else
          n := (dados #>> '{items,0,statistics,subscriberCount}')::bigint;
          if n is null then
            update contador_config set ultimo_erro = 'Canal não encontrado (confira o canal_id)', conferido_em = now() where id = 1;
          else
            update contador set seguidores = n, plataforma = 'youtube', atualizado_em = now() where id = 1;
            update contador_config set ultimo_erro = null, conferido_em = now() where id = 1;
          end if;
        end if;
      else
        update contador_config
           set ultimo_erro = coalesce('YouTube respondeu ' || resp.status_code || ': ' || left(resp.content, 300), resp.error_msg, 'sem resposta'),
               conferido_em = now()
         where id = 1;
      end if;
    end if;
  end if;

  -- 2) próximo pedido
  select decrypted_secret into chave from vault.decrypted_secrets where name = 'youtube_api_key';
  if chave is null then
    update contador_config set ultimo_erro = 'Falta guardar a chave youtube_api_key no Vault', conferido_em = now() where id = 1;
    return;
  end if;
  update contador_config
     set ultimo_pedido = net.http_get(
           url    := 'https://www.googleapis.com/youtube/v3/channels',
           params := jsonb_build_object('part', 'statistics', 'id', cfg.canal_id, 'key', chave))
   where id = 1;
end $$;
revoke all on function contador_youtube() from public, anon, authenticated;

-- agenda: a cada 10 minutos (144 pedidos/dia; o YouTube libera 10.000 por dia de graça)
select cron.unschedule('contador-youtube') where exists (select 1 from cron.job where jobname = 'contador-youtube');
select cron.schedule('contador-youtube', '*/10 * * * *', 'select public.contador_youtube()');

-- primeiro pedido já agora (o número aparece na próxima rodada, ou rode "select contador_youtube();" de novo daqui a uns segundos)
select contador_youtube();
