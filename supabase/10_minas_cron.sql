-- =====================================================================
--  Regenera a MINA sozinho a cada 15 minutos (pg_cron do Supabase).
--  Rode 1 vez no SQL Editor, depois do 8_jogo.sql.
--  Pra mudar o tempo: troque '*/15' (ex.: '*/10' = a cada 10 min) e
--  também o intervalo mostrado no site:
--    update mina_estado set intervalo_min = 10 where id = 1;
-- =====================================================================
create extension if not exists pg_cron;
select cron.unschedule('gerar-mina') where exists (select 1 from cron.job where jobname = 'gerar-mina');
select cron.schedule('gerar-mina', '*/15 * * * *', 'select public.gerar_mina()');
select gerar_mina();
