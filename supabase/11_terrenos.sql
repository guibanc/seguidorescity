-- =====================================================================
--  TERRENOS E LOTES: cada morador pega 1 lote grátis (16x16), constrói
--  a casa bloco por bloco e pode abrir uma loja (balcão) pros outros.
--  Ordem: rode DE NOVO o 8_jogo.sql (agora tem 40 ranks) e depois este.
-- =====================================================================

-- ---------------------------------------------------------------------
-- itens de construção (tipo 'bloco'):
--   forma 'piso'   = no chão (z = -1), dá pra andar em cima
--   forma 'cubo'   = bloco inteiro, empilha até 4 de altura (z 0..3)
--   forma 'objeto' = móvel/decoração (não aguenta nada em cima)
-- decoração não vende no mercadinho (venda 0): se vende entre jogadores
-- ---------------------------------------------------------------------
alter table itens drop constraint if exists itens_tipo_check;
alter table itens add constraint itens_tipo_check check (tipo in ('material','ferramenta','arma','armadura','comida','bloco'));
alter table itens add column if not exists forma  text check (forma in ('piso','cubo','objeto'));
alter table itens add column if not exists solido boolean not null default true;

insert into itens (id, nome, tipo, empilha, venda, compra, ordem, forma, solido) values
('piso_madeira','Piso de madeira','bloco',64,0,null,300,'piso',false),
('piso_pedra','Piso de pedra','bloco',64,0,null,301,'piso',false),
('tapete','Tapete','bloco',64,0,null,302,'piso',false),
('canteiro','Canteiro de flores','bloco',64,0,null,303,'piso',false),
('tronco','Tronco','bloco',64,0,null,310,'cubo',true),
('parede_madeira','Parede de tábua','bloco',64,0,null,311,'cubo',true),
('parede_pedra','Pedra lisa','bloco',64,0,null,312,'cubo',true),
('parede_reboco','Parede rebocada','bloco',64,0,null,313,'cubo',true),
('tijolo','Tijolos','bloco',64,0,4,314,'cubo',true),
('vidro','Vidro','bloco',64,0,5,315,'cubo',true),
('telha','Telhado','bloco',64,0,null,316,'cubo',true),
('porta','Porta','bloco',16,0,null,320,'objeto',false),
('cerca','Cerca','bloco',64,0,null,321,'objeto',true),
('mesa','Mesa','bloco',16,0,null,322,'objeto',true),
('cadeira','Cadeira','bloco',16,0,null,323,'objeto',false),
('cama','Cama','bloco',16,0,null,324,'objeto',true),
('estante','Estante','bloco',16,0,null,325,'objeto',true),
('lampiao','Lampião','bloco',16,0,null,326,'objeto',true),
('vaso_flor','Vaso de flor','bloco',16,0,null,327,'objeto',true),
('arvorezinha','Arvorezinha','bloco',16,0,null,328,'objeto',true),
('balcao','Balcão de loja','bloco',4,0,null,329,'objeto',true)
on conflict (id) do update set nome = excluded.nome, tipo = excluded.tipo, empilha = excluded.empilha, venda = excluded.venda,
  compra = excluded.compra, ordem = excluded.ordem, forma = excluded.forma, solido = excluded.solido;

-- areia: o cacto do deserto solta areia, e o mercadinho vende
update itens set compra = 3 where id = 'areia';
update quebraveis set drops = '[{"i":"cacto","min":1,"max":2},{"i":"areia","min":1,"max":3}]' where tipo = 'cacto';

insert into receitas (id, resultado, qtd, ingredientes, rank_min, grupo, ordem) values
('piso_madeira','piso_madeira',4,'{"tabua":2}',0,'construcao',200),
('piso_pedra','piso_pedra',4,'{"pedra":2}',0,'construcao',201),
('tapete','tapete',2,'{"la":2}',0,'construcao',202),
('canteiro','canteiro',2,'{"terra":1,"fibra":2}',0,'construcao',203),
('tronco','tronco',2,'{"madeira":2}',0,'construcao',210),
('parede_madeira','parede_madeira',4,'{"tabua":4}',0,'construcao',211),
('parede_pedra','parede_pedra',4,'{"pedra":4}',0,'construcao',212),
('parede_reboco','parede_reboco',4,'{"pedra":2,"areia":2}',0,'construcao',213),
('tijolo','tijolo',4,'{"terra":2,"areia":1,"carvao":1}',0,'construcao',214),
('vidro','vidro',4,'{"areia":3,"carvao":1}',0,'construcao',215),
('telha','telha',4,'{"terra":2,"carvao":1}',0,'construcao',216),
('porta','porta',1,'{"tabua":4}',0,'moveis',220),
('cerca','cerca',4,'{"graveto":4,"tabua":1}',0,'moveis',221),
('mesa','mesa',1,'{"tabua":4}',0,'moveis',222),
('cadeira','cadeira',1,'{"tabua":2,"graveto":2}',0,'moveis',223),
('cama','cama',1,'{"tabua":3,"la":3}',0,'moveis',224),
('estante','estante',1,'{"tabua":6}',0,'moveis',225),
('lampiao','lampiao',2,'{"ferro":1,"carvao":1}',0,'moveis',226),
('vaso_flor','vaso_flor',1,'{"terra":1,"frutinha":2}',0,'moveis',227),
('arvorezinha','arvorezinha',1,'{"madeira":2,"fibra":2}',0,'moveis',228),
('balcao','balcao',1,'{"tabua":6,"ferro":1}',0,'moveis',229)
on conflict (id) do update set resultado = excluded.resultado, qtd = excluded.qtd, ingredientes = excluded.ingredientes,
  rank_min = excluded.rank_min, grupo = excluded.grupo, ordem = excluded.ordem;

-- ---------------------------------------------------------------------
-- LOTES (64 pra começar; pra criar mais é só inserir ids novos:
--   insert into lotes (id) select g from generate_series(65, 128) g on conflict do nothing;)
-- ---------------------------------------------------------------------
create table if not exists lotes (
  id      int primary key check (id between 1 and 400),
  dono    int unique references registros(morador_id) on delete set null,
  pego_em timestamptz
);
insert into lotes (id) select g from generate_series(1, 64) g on conflict (id) do nothing;

create table if not exists lote_bloco (
  lote int not null references lotes(id) on delete cascade,
  x    int not null check (x between 0 and 15),
  y    int not null check (y between 0 and 15),
  z    int not null check (z between -1 and 3),        -- -1 = piso
  tipo text not null references itens(id),
  primary key (lote, x, y, z)
);

create table if not exists loja_oferta (
  id        bigserial primary key,
  lote      int not null references lotes(id) on delete cascade,
  item      text not null references itens(id),
  qtd       int not null check (qtd > 0),
  preco     int not null check (preco between 1 and 1000000),   -- por unidade
  dur       int,                                              -- ferramenta/armadura: durabilidade que sobrou
  criado_em timestamptz not null default now()
);
create index if not exists loja_oferta_lote on loja_oferta(lote);
alter table lotes       enable row level security;
alter table lote_bloco  enable row level security;
alter table loja_oferta enable row level security;

-- põe 1 item com durabilidade específica num slot vazio (ferramenta usada)
create or replace function jogo_add_dur(mid int, p_item text, p_dur int) returns boolean language plpgsql security definer set search_path = public as $$
declare s int;
begin
  select g into s from generate_series(0, 35) g where not exists (select 1 from inventario where morador_id = mid and slot = g) order by g limit 1;
  if s is null then return false; end if;
  insert into inventario values (mid, s, p_item, 1, p_dur);
  return true;
end $$;

-- ---------------------------------------------------------------------
-- o que o site chama
-- ---------------------------------------------------------------------
create or replace function lotes_lista() returns json language sql stable security definer set search_path = public as $$
  select coalesce(json_agg(json_build_object('id', l.id, 'dono', l.dono, 'nome', r.nome,
           'loja', (select count(*) from loja_oferta o where o.lote = l.id)) order by l.id), '[]'::json)
    from lotes l left join registros r on r.morador_id = l.dono
$$;

-- blocos de até 12 lotes (os que estão perto de você)
create or replace function lote_blocos(p_lotes int[]) returns json language sql stable security definer set search_path = public as $$
  select coalesce(json_object_agg(lote, b), '{}'::json) from (
    select lote, json_agg(json_build_array(x, y, z, tipo) order by z, y, x) b
      from lote_bloco where lote = any (p_lotes[1:12]) group by lote) t
$$;

create or replace function pegar_lote(p_token text, p_lote int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if exists (select 1 from lotes where dono = mid) then return json_build_object('ok',false,'erro','Você já tem um lote (cada um pode ter 1)'); end if;
  update lotes set dono = mid, pego_em = now() where id = p_lote and dono is null;
  if not found then return json_build_object('ok',false,'erro','Esse lote já tem dono'); end if;
  perform jogo_jogador(mid);
  return json_build_object('ok',true,'lote',p_lote);
end $$;

create or replace function largar_lote(p_token text) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); l int;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select id into l from lotes where dono = mid;
  if l is null then return json_build_object('ok',false,'erro','Você não tem lote'); end if;
  if exists (select 1 from lote_bloco where lote = l) or exists (select 1 from loja_oferta where lote = l) then
    return json_build_object('ok',false,'erro','Desmonte tudo e tire as coisas da loja antes de largar o lote'); end if;
  update lotes set dono = null, pego_em = null where id = l;
  return json_build_object('ok',true);
end $$;

-- põe o bloco que está no slot (barra rápida) na posição do SEU lote
create or replace function construir(p_token text, p_lote int, p_x int, p_y int, p_z int, p_slot int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); inv inventario; it itens; baixo text;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if not exists (select 1 from lotes where id = p_lote and dono = mid) then return json_build_object('ok',false,'erro','Você só constrói no seu lote'); end if;
  if p_x not between 0 and 15 or p_y not between 0 and 15 or p_z not between -1 and 3 then return json_build_object('ok',false,'erro','Fora do lote'); end if;
  select * into inv from inventario where morador_id = mid and slot = p_slot and p_slot between 0 and 8 for update;
  if not found then return json_build_object('ok',false,'erro','Escolha um bloco na barra'); end if;
  select * into it from itens where id = inv.item;
  if it.tipo <> 'bloco' then return json_build_object('ok',false,'erro','Isso não é de construir'); end if;
  if it.forma = 'piso' and p_z <> -1 then return json_build_object('ok',false,'erro','Piso vai no chão'); end if;
  if it.forma <> 'piso' and p_z = -1 then return json_build_object('ok',false,'erro','Posição inválida'); end if;
  if p_z > 0 then
    select i.forma into baixo from lote_bloco b join itens i on i.id = b.tipo where b.lote = p_lote and b.x = p_x and b.y = p_y and b.z = p_z - 1;
    if baixo is distinct from 'cubo' then return json_build_object('ok',false,'erro','Precisa de um bloco embaixo'); end if;
  end if;
  if exists (select 1 from lote_bloco where lote = p_lote and x = p_x and y = p_y and z = p_z) then return json_build_object('ok',false,'erro','Já tem coisa aí'); end if;
  insert into lote_bloco values (p_lote, p_x, p_y, p_z, it.id);
  if inv.qtd = 1 then delete from inventario where morador_id = mid and slot = p_slot;
  else update inventario set qtd = qtd - 1 where morador_id = mid and slot = p_slot; end if;
  return json_build_object('ok',true,'tipo',it.id);
end $$;

-- tira um bloco do SEU lote e devolve pra mochila
create or replace function desmontar(p_token text, p_lote int, p_x int, p_y int, p_z int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); b lote_bloco;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if not exists (select 1 from lotes where id = p_lote and dono = mid) then return json_build_object('ok',false,'erro','Você só desmonta no seu lote'); end if;
  select * into b from lote_bloco where lote = p_lote and x = p_x and y = p_y and z = p_z for update;
  if not found then return json_build_object('ok',false,'erro','Não tem nada aí','sumiu',true); end if;
  if p_z >= 0 and exists (select 1 from lote_bloco where lote = p_lote and x = p_x and y = p_y and z = p_z + 1) then
    return json_build_object('ok',false,'erro','Tire o de cima primeiro'); end if;
  if p_z = -1 and exists (select 1 from lote_bloco where lote = p_lote and x = p_x and y = p_y and z >= 0) then
    return json_build_object('ok',false,'erro','Tire o que está em cima do piso primeiro'); end if;
  if jogo_add(mid, b.tipo, 1) > 0 then return json_build_object('ok',false,'erro','Mochila cheia'); end if;
  delete from lote_bloco where lote = p_lote and x = p_x and y = p_y and z = p_z;
  return json_build_object('ok',true,'tipo',b.tipo);
end $$;

-- ---------------------------------------------------------------------
-- LOJAS DOS JOGADORES (precisa ter um balcão no lote)
-- ---------------------------------------------------------------------
create or replace function loja_ofertas(p_lote int) returns json language sql stable security definer set search_path = public as $$
  select json_build_object('lote', l.id, 'dono', l.dono, 'nome', r.nome,
    'ofertas', coalesce((select json_agg(json_build_object('id', o.id, 'item', o.item, 'qtd', o.qtd, 'preco', o.preco, 'dur', o.dur) order by o.id)
                          from loja_oferta o where o.lote = l.id), '[]'::json))
    from lotes l left join registros r on r.morador_id = l.dono where l.id = p_lote
$$;

-- tudo que está à venda em todos os lotes (a "feira")
create or replace function feira() returns json language sql stable security definer set search_path = public as $$
  select coalesce(json_agg(x), '[]'::json) from (
    select o.id, o.lote, r.nome, o.item, o.qtd, o.preco, o.dur
      from loja_oferta o join lotes l on l.id = o.lote join registros r on r.morador_id = l.dono
     order by o.item, o.preco, o.id limit 300) x
$$;

create or replace function loja_por(p_token text, p_slot int, p_qtd int, p_preco int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); l int; inv inventario; it itens; q int := coalesce(p_qtd, 0);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select id into l from lotes where dono = mid;
  if l is null then return json_build_object('ok',false,'erro','Pegue um lote primeiro'); end if;
  if not exists (select 1 from lote_bloco where lote = l and tipo = 'balcao') then return json_build_object('ok',false,'erro','Coloque um balcão de loja no seu lote'); end if;
  if (select count(*) from loja_oferta where lote = l) >= 12 then return json_build_object('ok',false,'erro','A loja já tem 12 coisas à venda'); end if;
  if p_preco is null or p_preco < 1 or p_preco > 1000000 then return json_build_object('ok',false,'erro','Preço inválido (1 a 1.000.000)'); end if;
  select * into inv from inventario where morador_id = mid and slot = p_slot and p_slot between 0 and 35 for update;
  if not found then return json_build_object('ok',false,'erro','Não tem nada nesse espaço'); end if;
  select * into it from itens where id = inv.item;
  if inv.dur is not null then q := 1; end if;
  if q <= 0 or q > inv.qtd then return json_build_object('ok',false,'erro','Quantidade inválida'); end if;
  if q = inv.qtd then delete from inventario where morador_id = mid and slot = p_slot;
  else update inventario set qtd = qtd - q where morador_id = mid and slot = p_slot; end if;
  insert into loja_oferta (lote, item, qtd, preco, dur) values (l, inv.item, q, p_preco, inv.dur);
  return json_build_object('ok',true);
end $$;

create or replace function loja_tirar(p_token text, p_oferta bigint) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); o loja_oferta;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select o2.* into o from loja_oferta o2 join lotes l on l.id = o2.lote where o2.id = p_oferta and l.dono = mid for update of o2;
  if not found then return json_build_object('ok',false,'erro','Isso não está na sua loja'); end if;
  if o.dur is not null then
    if not jogo_add_dur(mid, o.item, o.dur) then return json_build_object('ok',false,'erro','Mochila cheia'); end if;
  elsif jogo_add(mid, o.item, o.qtd) > 0 then raise exception 'MOCHILA_CHEIA';
  end if;
  delete from loja_oferta where id = o.id;
  return json_build_object('ok',true);
exception when raise_exception then
  return json_build_object('ok',false,'erro','Mochila cheia');
end $$;

create or replace function loja_comprar(p_token text, p_oferta bigint, p_qtd int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); o loja_oferta; dono int; q int := coalesce(p_qtd, 0); custo bigint;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  perform jogo_jogador(mid);
  select * into o from loja_oferta where id = p_oferta for update;
  if not found then return json_build_object('ok',false,'erro','Alguém já comprou','sumiu',true); end if;
  select l.dono into dono from lotes l where l.id = o.lote;
  if dono = mid then return json_build_object('ok',false,'erro','Essa loja é sua'); end if;
  if dono is null then return json_build_object('ok',false,'erro','Loja fechada'); end if;
  if q <= 0 or q > o.qtd then return json_build_object('ok',false,'erro','Só tem ' || o.qtd); end if;
  custo := o.preco::bigint * q;
  update jogador set moedas = moedas - custo where morador_id = mid and moedas >= custo;
  if not found then return json_build_object('ok',false,'erro','Dinheiro insuficiente'); end if;
  if o.dur is not null then
    if not jogo_add_dur(mid, o.item, o.dur) then raise exception 'MOCHILA_CHEIA'; end if;
  elsif jogo_add(mid, o.item, q) > 0 then raise exception 'MOCHILA_CHEIA';
  end if;
  perform jogo_jogador(dono);
  update jogador set moedas = moedas + custo, ganho_total = ganho_total + custo where morador_id = dono;
  if q = o.qtd then delete from loja_oferta where id = o.id; else update loja_oferta set qtd = qtd - q where id = o.id; end if;
  return json_build_object('ok',true,'pagou',custo,'moedas',(select moedas from jogador where morador_id = mid));
exception when raise_exception then
  return json_build_object('ok',false,'erro','Mochila cheia');
end $$;

-- ---------------------------------------------------------------------
-- mudar de casa leva junto o lote (e o resto do jogo)
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

  update registros set usuario = '__mud.' || mid where morador_id = mid;
  insert into registros (morador_id, usuario, nome, pin_hash, aparencia, bio, criado_em, tentativas, bloqueado_ate, oculto, casa_trocada_em)
  values (novo, r.usuario, r.nome, r.pin_hash, p_aparencia, r.bio, r.criado_em, 0, null, r.oculto, now());
  update amizades set de = novo where de = mid;
  update amizades set para = -1   where para = novo;
  update amizades set para = novo where para = mid;
  update amizades set para = mid  where para = -1;
  update sessoes set morador_id = novo where morador_id = mid;
  update chat set morador_id = novo where morador_id = mid;
  update candidaturas set morador_id = novo where morador_id = mid;
  update votos set eleitor = novo where eleitor = mid;
  update eleicao set prefeito = novo where prefeito = mid;
  update jogador set morador_id = novo where morador_id = mid;
  update inventario set morador_id = novo where morador_id = mid;
  update lotes set dono = novo where dono = mid;
  delete from registros where morador_id = mid;
  return json_build_object('ok',true,'morador',novo,'casa',p_casa,'antigo',mid);
end $$;

-- ---------------------------------------------------------------------
-- permissões
-- ---------------------------------------------------------------------
revoke all on function jogo_add_dur(int,text,int) from public, anon, authenticated;
revoke all on function lotes_lista(), lote_blocos(int[]), pegar_lote(text,int), largar_lote(text), construir(text,int,int,int,int,int),
  desmontar(text,int,int,int,int), loja_ofertas(int), feira(), loja_por(text,int,int,int), loja_tirar(text,bigint),
  loja_comprar(text,bigint,int), trocar_casa(text,int,jsonb) from public;
grant execute on function lotes_lista(), lote_blocos(int[]), pegar_lote(text,int), largar_lote(text), construir(text,int,int,int,int,int),
  desmontar(text,int,int,int,int), loja_ofertas(int), feira(), loja_por(text,int,int,int), loja_tirar(text,bigint),
  loja_comprar(text,bigint,int), trocar_casa(text,int,jsonb) to anon, authenticated;
