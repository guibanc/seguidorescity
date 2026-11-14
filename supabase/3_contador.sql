-- =====================================================================
--  Contador de seguidores ao vivo (o site lê a cada 1 minuto)
--  Rode 1 vez no SQL Editor do Supabase.
--
--  Enquanto a busca automática na plataforma não estiver ligada,
--  dá pra atualizar à mão (SQL Editor):
--    update contador set seguidores = 381, atualizado_em = now() where id = 1;
-- =====================================================================
create table if not exists contador (
  id             int primary key default 1 check (id = 1),   -- uma linha só
  seguidores     int not null check (seguidores >= 0),
  plataforma     text,
  atualizado_em  timestamptz not null default now()
);
alter table contador enable row level security;   -- ninguém de fora altera

-- leitura pública (só o número)
create or replace view contador_publico with (security_invoker = false) as
  select seguidores, plataforma, atualizado_em from contador where id = 1;
grant select on contador_publico to anon, authenticated;

insert into contador (id, seguidores, plataforma) values (1, 370, 'manual')
on conflict (id) do nothing;
