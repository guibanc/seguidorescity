-- =====================================================================
--  JOGO (fase 1): inventário, dinheiro, ranks, crafting, lojas,
--  mundo do EXPLORAR (compartilhado) e MINAS em camadas que regeneram.
--  Rode no SQL Editor do Supabase (depois dos arquivos 1 a 7).
--  Depois rode o 9_mundo_explorar.sql (os objetos do mundo) e o
--  10_minas_cron.sql (regenera a mina sozinho a cada 15 min).
--
--  Tudo que dá item ou dinheiro passa por estas funções: o navegador
--  só pede, o banco confere (tempo pra quebrar, ferramenta, rank,
--  espaço na mochila, preço) e decide.
-- =====================================================================

-- ---------------------------------------------------------------------
-- CATÁLOGO
-- ---------------------------------------------------------------------
create table if not exists itens (
  id            text primary key,
  nome          text not null,
  tipo          text not null check (tipo in ('material','ferramenta','arma','armadura','comida')),
  ferramenta    text check (ferramenta in ('picareta','machado','espada')),
  nivel         int  not null default 0,          -- 1 madeira · 2 pedra · 3 ferro · 4 cristal
  slot_armadura text check (slot_armadura in ('cabeca','peito','pernas','pes')),
  defesa        int  not null default 0,
  dano          int  not null default 1,
  durabilidade  int  not null default 0,
  cura          int  not null default 0,          -- comida: quanto de vida volta
  empilha       int  not null default 64,
  venda         int  not null default 0,          -- quanto as lojas pagam
  compra        int,                              -- preço no mercadinho (null = não vende)
  mina          boolean not null default false,   -- a loja da mina compra?
  ordem         int  not null default 0
);

insert into itens (id, nome, tipo, ferramenta, nivel, slot_armadura, defesa, dano, durabilidade, cura, empilha, venda, compra, mina, ordem) values
-- materiais
('madeira','Madeira','material',null,0,null,0,1,0,0,64,1,4,false,10),
('tabua','Tábua','material',null,0,null,0,1,0,0,64,1,null,false,11),
('graveto','Graveto','material',null,0,null,0,1,0,0,64,0,null,false,12),
('fibra','Fibra','material',null,0,null,0,1,0,0,64,1,null,false,13),
('pedra','Pedra','material',null,0,null,0,1,0,0,64,1,null,true,20),
('terra','Terra','material',null,0,null,0,1,0,0,64,0,null,true,21),
('areia','Areia','material',null,0,null,0,1,0,0,64,0,3,false,22),
('carvao','Carvão','material',null,0,null,0,1,0,0,64,4,null,true,30),
('minerio_ferro','Minério de ferro','material',null,0,null,0,1,0,0,64,8,null,true,31),
('ferro','Barra de ferro','material',null,0,null,0,1,0,0,64,16,null,true,32),
('minerio_ouro','Minério de ouro','material',null,0,null,0,1,0,0,64,20,null,true,33),
('ouro','Barra de ouro','material',null,0,null,0,1,0,0,64,40,null,true,34),
('cristal','Cristal','material',null,0,null,0,1,0,0,64,75,null,true,35),
('rubi','Rubi','material',null,0,null,0,1,0,0,64,150,null,true,36),
('couro','Couro','material',null,0,null,0,1,0,0,64,6,null,false,40),
('la','Lã','material',null,0,null,0,1,0,0,64,4,null,false,41),
('pena','Pena','material',null,0,null,0,1,0,0,64,2,null,false,42),
('cacto','Cacto','material',null,0,null,0,1,0,0,64,2,null,false,43),
('gosma','Gosma','material',null,0,null,0,1,0,0,64,5,null,true,44),
('osso','Osso','material',null,0,null,0,1,0,0,64,3,null,true,45),
-- comida
('maca','Maçã','comida',null,0,null,0,1,0,8,64,2,6,false,50),
('frutinha','Frutinhas','comida',null,0,null,0,1,0,5,64,1,null,false,51),
('carne_crua','Carne crua','comida',null,0,null,0,1,0,4,64,3,null,false,52),
('carne_assada','Carne assada','comida',null,0,null,0,1,0,25,64,10,18,false,53),
('frango_cru','Frango cru','comida',null,0,null,0,1,0,3,64,2,null,false,54),
('frango_assado','Frango assado','comida',null,0,null,0,1,0,18,64,7,14,false,55),
('carne_podre','Carne podre','comida',null,0,null,0,1,0,2,64,1,null,true,56),
('pao','Pão','comida',null,0,null,0,1,0,12,64,4,9,false,57),
('suco','Suco de frutas','comida',null,0,null,0,1,0,30,64,12,null,false,58),
-- ferramentas (velocidade cresce com o nível; durabilidade = quantos usos)
('picareta_madeira','Picareta de madeira','ferramenta','picareta',1,null,0,2,60,0,1,3,null,false,100),
('picareta_pedra','Picareta de pedra','ferramenta','picareta',2,null,0,3,130,0,1,8,null,false,101),
('picareta_ferro','Picareta de ferro','ferramenta','picareta',3,null,0,4,250,0,1,40,null,false,102),
('picareta_cristal','Picareta de cristal','ferramenta','picareta',4,null,0,5,600,0,1,200,null,false,103),
('machado_madeira','Machado de madeira','ferramenta','machado',1,null,0,3,60,0,1,3,null,false,110),
('machado_pedra','Machado de pedra','ferramenta','machado',2,null,0,4,130,0,1,8,null,false,111),
('machado_ferro','Machado de ferro','ferramenta','machado',3,null,0,5,250,0,1,40,null,false,112),
('machado_cristal','Machado de cristal','ferramenta','machado',4,null,0,6,600,0,1,200,null,false,113),
('espada_madeira','Espada de madeira','arma','espada',1,null,0,4,60,0,1,3,null,false,120),
('espada_pedra','Espada de pedra','arma','espada',2,null,0,6,130,0,1,8,null,false,121),
('espada_ferro','Espada de ferro','arma','espada',3,null,0,8,250,0,1,40,null,false,122),
('espada_cristal','Espada de cristal','arma','espada',4,null,0,11,600,0,1,200,null,false,123),
-- armaduras (defesa: cada ponto tira 4% do dano)
('capacete_couro','Capacete de couro','armadura',null,1,'cabeca',1,1,80,0,1,10,null,false,200),
('peitoral_couro','Peitoral de couro','armadura',null,1,'peito',3,1,80,0,1,16,null,false,201),
('calca_couro','Calça de couro','armadura',null,1,'pernas',2,1,80,0,1,14,null,false,202),
('botas_couro','Botas de couro','armadura',null,1,'pes',1,1,80,0,1,8,null,false,203),
('capacete_ferro','Capacete de ferro','armadura',null,3,'cabeca',2,1,200,0,1,60,null,false,210),
('peitoral_ferro','Peitoral de ferro','armadura',null,3,'peito',6,1,200,0,1,100,null,false,211),
('calca_ferro','Calça de ferro','armadura',null,3,'pernas',5,1,200,0,1,85,null,false,212),
('botas_ferro','Botas de ferro','armadura',null,3,'pes',2,1,200,0,1,50,null,false,213),
('capacete_cristal','Capacete de cristal','armadura',null,4,'cabeca',3,1,500,0,1,300,null,false,220),
('peitoral_cristal','Peitoral de cristal','armadura',null,4,'peito',8,1,500,0,1,500,null,false,221),
('calca_cristal','Calça de cristal','armadura',null,4,'pernas',6,1,500,0,1,420,null,false,222),
('botas_cristal','Botas de cristal','armadura',null,4,'pes',3,1,500,0,1,250,null,false,223)
on conflict (id) do update set nome = excluded.nome, tipo = excluded.tipo, ferramenta = excluded.ferramenta, nivel = excluded.nivel,
  slot_armadura = excluded.slot_armadura, defesa = excluded.defesa, dano = excluded.dano, durabilidade = excluded.durabilidade,
  cura = excluded.cura, empilha = excluded.empilha, venda = excluded.venda, compra = excluded.compra, mina = excluded.mina, ordem = excluded.ordem;

-- receitas (ingredientes = {"item": quantidade})
create table if not exists receitas (
  id           text primary key,
  resultado    text not null references itens(id),
  qtd          int  not null default 1,
  ingredientes jsonb not null,
  rank_min     int  not null default 0,
  grupo        text not null default 'basico',
  ordem        int  not null default 0
);
insert into receitas (id, resultado, qtd, ingredientes, rank_min, grupo, ordem) values
('tabua','tabua',4,'{"madeira":1}',0,'basico',1),
('graveto','graveto',4,'{"tabua":2}',0,'basico',2),
('picareta_madeira','picareta_madeira',1,'{"tabua":3,"graveto":2}',0,'ferramentas',10),
('machado_madeira','machado_madeira',1,'{"tabua":3,"graveto":2}',0,'ferramentas',11),
('espada_madeira','espada_madeira',1,'{"tabua":2,"graveto":1}',0,'ferramentas',12),
('picareta_pedra','picareta_pedra',1,'{"pedra":3,"graveto":2}',0,'ferramentas',20),
('machado_pedra','machado_pedra',1,'{"pedra":3,"graveto":2}',0,'ferramentas',21),
('espada_pedra','espada_pedra',1,'{"pedra":2,"graveto":1}',0,'ferramentas',22),
('ferro','ferro',1,'{"minerio_ferro":1,"carvao":1}',0,'fornalha',30),
('ouro','ouro',1,'{"minerio_ouro":1,"carvao":1}',0,'fornalha',31),
('carne_assada','carne_assada',1,'{"carne_crua":1,"carvao":1}',0,'fornalha',32),
('frango_assado','frango_assado',1,'{"frango_cru":1,"carvao":1}',0,'fornalha',33),
('picareta_ferro','picareta_ferro',1,'{"ferro":3,"graveto":2}',4,'ferramentas',40),
('machado_ferro','machado_ferro',1,'{"ferro":3,"graveto":2}',4,'ferramentas',41),
('espada_ferro','espada_ferro',1,'{"ferro":2,"graveto":1}',4,'ferramentas',42),
('picareta_cristal','picareta_cristal',1,'{"cristal":3,"ouro":1,"graveto":2}',20,'ferramentas',50),
('machado_cristal','machado_cristal',1,'{"cristal":3,"ouro":1,"graveto":2}',20,'ferramentas',51),
('espada_cristal','espada_cristal',1,'{"cristal":2,"ouro":1,"graveto":1}',20,'ferramentas',52),
('capacete_couro','capacete_couro',1,'{"couro":5}',0,'armaduras',60),
('peitoral_couro','peitoral_couro',1,'{"couro":8}',0,'armaduras',61),
('calca_couro','calca_couro',1,'{"couro":7}',0,'armaduras',62),
('botas_couro','botas_couro',1,'{"couro":4}',0,'armaduras',63),
('capacete_ferro','capacete_ferro',1,'{"ferro":5}',4,'armaduras',70),
('peitoral_ferro','peitoral_ferro',1,'{"ferro":8}',4,'armaduras',71),
('calca_ferro','calca_ferro',1,'{"ferro":7}',4,'armaduras',72),
('botas_ferro','botas_ferro',1,'{"ferro":4}',4,'armaduras',73),
('capacete_cristal','capacete_cristal',1,'{"cristal":5,"couro":2}',20,'armaduras',80),
('peitoral_cristal','peitoral_cristal',1,'{"cristal":8,"couro":3}',20,'armaduras',81),
('calca_cristal','calca_cristal',1,'{"cristal":7,"couro":2}',20,'armaduras',82),
('botas_cristal','botas_cristal',1,'{"cristal":4,"couro":2}',20,'armaduras',83),
('pao','pao',1,'{"fibra":3}',0,'cozinha',90),
('suco','suco',1,'{"frutinha":4,"maca":1}',0,'cozinha',91)
on conflict (id) do update set resultado = excluded.resultado, qtd = excluded.qtd, ingredientes = excluded.ingredientes,
  rank_min = excluded.rank_min, grupo = excluded.grupo, ordem = excluded.ordem;

-- ranks (subir custa dinheiro; libera camadas da mina, receitas e bônus de venda)
create table if not exists ranks (
  nivel       int primary key,
  nome        text not null,
  custo       bigint not null,
  camada_max  int not null,
  bonus_venda int not null default 0,         -- % a mais quando vende
  cor         text not null default '#9aa'
);
-- 40 ranks: o custo cresce 22% por rank; a cada 4 ranks libera mais 1 camada da mina;
-- cada rank dá +1,5% na venda; a cor muda a cada 5 ranks
insert into ranks (nivel, nome, custo, camada_max, bonus_venda, cor)
select n - 1, nome,
       case when n = 1 then 0 else (round(300 * power(1.22, n - 2) / 50) * 50)::bigint end,
       least(11, 3 + (n - 1) / 4), floor((n - 1) * 1.5)::int,
       (array['#b8b0a0','#7fb069','#4fa3d1','#d4a72c','#c9643b','#e0457b','#a855f7','#f6c836'])[1 + (n - 1) / 5]
  from unnest(array['Morador','Aprendiz','Lenhador','Catador','Minerador','Escavador','Ferreiro','Artesão','Carpinteiro','Pedreiro',
                    'Construtor','Mercador','Comerciante','Negociante','Lojista','Empresário','Mestre de Obras','Joalheiro','Banqueiro','Investidor',
                    'Fidalgo','Coronel','Barão','Visconde','Conde','Marquês','Duque','Arquiduque','Príncipe','Rei',
                    'Imperador','Magnata','Milionário','Bilionário','Lenda','Mito','Titã','Colosso','Divindade','Dono da Cidade'])
       with ordinality as t(nome, n)
on conflict (nivel) do update set nome = excluded.nome, custo = excluded.custo, camada_max = excluded.camada_max,
  bonus_venda = excluded.bonus_venda, cor = excluded.cor;

-- o que dá pra quebrar (explorar e minas): tempo na mão, ferramenta certa, nível mínimo e drops
-- drops: [{"i": item, "min": n, "max": n, "p": chance 0..1}]
create table if not exists quebraveis (
  tipo        text primary key,
  dureza      numeric not null,          -- segundos na mão (ferramenta certa divide)
  ferramenta  text,                      -- 'machado' | 'picareta' | null (qualquer coisa)
  nivel_min   int not null default 0,    -- picareta mínima pra dar drop (0 = mão serve)
  respawn_s   int not null default 300,  -- explorar: volta a nascer depois disso
  drops       jsonb not null
);
insert into quebraveis values
('carvalho',3.0,'machado',0,360,'[{"i":"madeira","min":3,"max":5},{"i":"maca","min":1,"max":1,"p":0.25},{"i":"graveto","min":1,"max":2,"p":0.4}]'),
('pinheiro',3.5,'machado',0,360,'[{"i":"madeira","min":4,"max":6},{"i":"graveto","min":1,"max":3,"p":0.5}]'),
('palmeira',2.5,'machado',0,360,'[{"i":"madeira","min":2,"max":4},{"i":"frutinha","min":1,"max":3,"p":0.5}]'),
('arbusto',0.8,null,0,180,'[{"i":"frutinha","min":1,"max":3},{"i":"fibra","min":0,"max":1}]'),
('capim',0.4,null,0,120,'[{"i":"fibra","min":1,"max":2,"p":0.7}]'),
('cacto',1.2,null,0,240,'[{"i":"cacto","min":1,"max":2},{"i":"areia","min":1,"max":3}]'),
('rocha',3.0,'picareta',1,420,'[{"i":"pedra","min":2,"max":4},{"i":"carvao","min":1,"max":1,"p":0.2}]'),
('rocha_carvao',3.5,'picareta',1,600,'[{"i":"carvao","min":2,"max":3},{"i":"pedra","min":1,"max":2}]'),
('rocha_ferro',4.5,'picareta',2,900,'[{"i":"minerio_ferro","min":1,"max":2},{"i":"pedra","min":1,"max":1}]'),
-- blocos da mina (respawn não vale: a mina inteira regenera)
('b_terra',0.8,null,0,0,'[{"i":"terra","min":1,"max":1}]'),
('b_pedra',2.5,'picareta',1,0,'[{"i":"pedra","min":1,"max":1}]'),
('b_carvao',3.0,'picareta',1,0,'[{"i":"carvao","min":1,"max":2}]'),
('b_ferro',4.0,'picareta',2,0,'[{"i":"minerio_ferro","min":1,"max":1}]'),
('b_ouro',5.0,'picareta',3,0,'[{"i":"minerio_ouro","min":1,"max":1}]'),
('b_cristal',6.0,'picareta',3,0,'[{"i":"cristal","min":1,"max":2}]'),
('b_rubi',7.5,'picareta',4,0,'[{"i":"rubi","min":1,"max":1}]')
on conflict (tipo) do update set dureza = excluded.dureza, ferramenta = excluded.ferramenta, nivel_min = excluded.nivel_min,
  respawn_s = excluded.respawn_s, drops = excluded.drops;

-- bichos (o navegador simula; o banco só entrega o drop, com limite de tempo)
create table if not exists bichos (
  tipo      text primary key,
  intervalo numeric not null,     -- segundos mínimos entre dois abates
  drops     jsonb not null
);
insert into bichos values
('galinha',2,'[{"i":"frango_cru","min":1,"max":1},{"i":"pena","min":0,"max":2}]'),
('vaca',3,'[{"i":"carne_crua","min":1,"max":2},{"i":"couro","min":1,"max":2}]'),
('ovelha',3,'[{"i":"carne_crua","min":1,"max":1},{"i":"la","min":1,"max":2}]'),
('zumbi',3,'[{"i":"carne_podre","min":1,"max":2},{"i":"osso","min":0,"max":1,"p":0.5},{"i":"minerio_ferro","min":1,"max":1,"p":0.05}]'),
('gosma',2.5,'[{"i":"gosma","min":1,"max":2}]'),
('esqueleto',3,'[{"i":"osso","min":1,"max":3},{"i":"carvao","min":0,"max":1,"p":0.4}]')
on conflict (tipo) do update set intervalo = excluded.intervalo, drops = excluded.drops;

-- ---------------------------------------------------------------------
-- JOGADOR E INVENTÁRIO  (slots 0–8 = barra rápida, 9–35 = mochila,
--                        36 cabeça · 37 peito · 38 pernas · 39 pés)
-- ---------------------------------------------------------------------
create table if not exists jogador (
  morador_id     int primary key references registros(morador_id) on delete cascade on update cascade,
  moedas         bigint not null default 0 check (moedas >= 0),
  rank           int not null default 0,
  ganho_total    bigint not null default 0,
  ultima_quebra  timestamptz not null default now() - interval '1 hour',
  ultimo_abate   timestamptz not null default now() - interval '1 hour',
  criado_em      timestamptz not null default now()
);
create table if not exists inventario (
  morador_id  int not null references registros(morador_id) on delete cascade on update cascade,
  slot        int not null check (slot between 0 and 39),
  item        text not null references itens(id),
  qtd         int not null check (qtd > 0),
  dur         int,
  primary key (morador_id, slot)
);
alter table itens       enable row level security;
alter table receitas    enable row level security;
alter table ranks       enable row level security;
alter table quebraveis  enable row level security;
alter table bichos      enable row level security;
alter table jogador     enable row level security;
alter table inventario  enable row level security;

-- garante a linha do jogador (kit inicial: nada — começa quebrando arbusto e árvore na mão)
create or replace function jogo_jogador(mid int) returns jogador language plpgsql security definer set search_path = public as $$
declare j jogador;
begin
  insert into jogador (morador_id) values (mid) on conflict (morador_id) do nothing;
  select * into j from jogador where morador_id = mid;
  return j;
end $$;

-- põe itens na mochila (empilha, depois slots vazios 0..35). Devolve quanto NÃO coube.
create or replace function jogo_add(mid int, p_item text, p_qtd int) returns int language plpgsql security definer set search_path = public as $$
declare it itens; resto int := p_qtd; s int; cabe int; r record;
begin
  if p_qtd <= 0 then return 0; end if;
  select * into it from itens where id = p_item;
  if not found then raise exception 'item % não existe', p_item; end if;
  if it.empilha > 1 then
    for r in select slot, qtd from inventario where morador_id = mid and item = p_item and slot <= 35 and qtd < it.empilha order by slot loop
      cabe := least(resto, it.empilha - r.qtd);
      update inventario set qtd = qtd + cabe where morador_id = mid and slot = r.slot;
      resto := resto - cabe; exit when resto = 0;
    end loop;
  end if;
  while resto > 0 loop
    select g into s from generate_series(0, 35) g where not exists (select 1 from inventario where morador_id = mid and slot = g) order by g limit 1;
    exit when s is null;
    cabe := least(resto, it.empilha);
    insert into inventario values (mid, s, p_item, cabe, case when it.durabilidade > 0 then it.durabilidade end);
    resto := resto - cabe;
  end loop;
  return resto;
end $$;

-- tira itens (de qualquer slot da mochila, não da armadura). true se tinha o suficiente.
create or replace function jogo_tirar(mid int, p_item text, p_qtd int) returns boolean language plpgsql security definer set search_path = public as $$
declare total int; resto int := p_qtd; r record; t int;
begin
  select coalesce(sum(qtd), 0) into total from inventario where morador_id = mid and item = p_item and slot <= 35;
  if total < p_qtd then return false; end if;
  for r in select slot, qtd from inventario where morador_id = mid and item = p_item and slot <= 35 order by slot desc loop
    t := least(resto, r.qtd);
    if t = r.qtd then delete from inventario where morador_id = mid and slot = r.slot;
    else update inventario set qtd = qtd - t where morador_id = mid and slot = r.slot; end if;
    resto := resto - t; exit when resto = 0;
  end loop;
  return true;
end $$;

-- sorteia os drops e põe na mochila; erro se não couber (a ação inteira é desfeita)
create or replace function jogo_dar_drops(mid int, p_drops jsonb) returns jsonb language plpgsql security definer set search_path = public as $$
declare d jsonb; n int; ganhos jsonb := '{}'::jsonb;
begin
  for d in select * from jsonb_array_elements(p_drops) loop
    if d ? 'p' and random() > (d->>'p')::numeric then continue; end if;
    n := (d->>'min')::int + floor(random() * ((d->>'max')::int - (d->>'min')::int + 1))::int;
    if n <= 0 then continue; end if;
    if jogo_add(mid, d->>'i', n) > 0 then raise exception 'MOCHILA_CHEIA'; end if;
    ganhos := ganhos || jsonb_build_object(d->>'i', coalesce((ganhos->>(d->>'i'))::int, 0) + n);
  end loop;
  return ganhos;
end $$;

-- gasta 1 de durabilidade da ferramenta do slot (some quando acaba)
create or replace function jogo_gastar(mid int, p_slot int) returns void language plpgsql security definer set search_path = public as $$
begin
  update inventario set dur = dur - 1 where morador_id = mid and slot = p_slot and dur is not null;
  delete from inventario where morador_id = mid and slot = p_slot and dur is not null and dur <= 0;
end $$;

-- tempo pra quebrar com a ferramenta do slot (ou erro se precisar de ferramenta melhor)
create or replace function jogo_tempo(mid int, q quebraveis, p_slot int, out tempo numeric, out erro text, out usou boolean)
language plpgsql stable security definer set search_path = public as $$
declare inv inventario; it itens;
begin
  usou := false; erro := null;
  select * into inv from inventario where morador_id = mid and slot = p_slot and p_slot between 0 and 8;
  if found then select * into it from itens where id = inv.item; end if;
  if q.nivel_min > 0 and (it.id is null or it.ferramenta is distinct from q.ferramenta or it.nivel < q.nivel_min) then
    erro := 'Precisa de ' || q.ferramenta || ' de ' || (array['madeira','pedra','ferro','cristal'])[q.nivel_min] || ' ou melhor'; return;
  end if;
  if it.id is not null and q.ferramenta is not null and it.ferramenta = q.ferramenta then
    tempo := q.dureza / (1 + it.nivel * 1.25); usou := true;
  else
    tempo := q.dureza * (case when q.ferramenta is null then 1 else 1.6 end);
  end if;
end $$;

-- ---------------------------------------------------------------------
-- MUNDO DO EXPLORAR (compartilhado: o que um quebra some pra todos)
-- os objetos vêm do 9_mundo_explorar.sql (gerado junto com o site)
-- ---------------------------------------------------------------------
create table if not exists mundo_obj (
  id           int primary key,
  x            int not null,
  y            int not null,
  tipo         text not null references quebraveis(tipo),
  quebrado_ate timestamptz
);
alter table mundo_obj enable row level security;

-- ---------------------------------------------------------------------
-- MINAS: 12 camadas de 25x25. Regenera inteira de tempos em tempos.
-- tipo 'ar' = vazio (poço da escada, sala de entrada, já minerado)
-- ---------------------------------------------------------------------
create table if not exists mina (
  z int not null, x int not null, y int not null,
  tipo text not null,
  quebrado boolean not null default false,
  primary key (z, x, y)
);
create table if not exists mina_estado (
  id int primary key default 1 check (id = 1),
  gerada_em timestamptz not null default now(),
  intervalo_min int not null default 15
);
insert into mina_estado (id) values (1) on conflict (id) do nothing;
alter table mina        enable row level security;
alter table mina_estado enable row level security;

create or replace function gerar_mina() returns void language plpgsql security definer set search_path = public as $$
begin
  delete from mina;
  insert into mina (z, x, y, tipo)
  select z, x, y,
    case
      when x = 12 and y = 12 then 'ar'                                   -- poço da escada (todas as camadas)
      when z = 0 and abs(x - 12) <= 2 and abs(y - 12) <= 2 then 'ar'      -- sala de entrada
      else (select case
              when z >= 10 and r < 0.015 then 'b_rubi'
              when z >= 8  and r < 0.045 then 'b_cristal'
              when z >= 5  and r < 0.085 then 'b_ouro'
              when z >= 2  and r < 0.16  then 'b_ferro'
              when z <= 7  and r < 0.28  then 'b_carvao'
              when z <= 1  and r < 0.50  then 'b_terra'
              else 'b_pedra' end
            from (select random() as r) s)
    end
  from generate_series(0, 11) z, generate_series(0, 24) x, generate_series(0, 24) y;
  update mina_estado set gerada_em = now() where id = 1;
end $$;
do $$ begin if not exists (select 1 from mina) then perform gerar_mina(); end if; end $$;

-- ---------------------------------------------------------------------
-- FUNÇÕES QUE O SITE CHAMA
-- ---------------------------------------------------------------------
create or replace function jogo_catalogo() returns json language sql stable security definer set search_path = public as $$
  select json_build_object(
    'itens', (select json_agg(row_to_json(i) order by i.ordem) from itens i),
    'receitas', (select json_agg(row_to_json(r) order by r.ordem) from receitas r),
    'ranks', (select json_agg(row_to_json(k) order by k.nivel) from ranks k),
    'quebraveis', (select json_object_agg(q.tipo, json_build_object('dureza', q.dureza, 'ferramenta', q.ferramenta, 'nivel_min', q.nivel_min)) from quebraveis q))
$$;

create or replace function meu_jogo(p_token text) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  j := jogo_jogador(mid);
  return json_build_object('ok',true,'moedas',j.moedas,'rank',j.rank,
    'inv', coalesce((select json_agg(json_build_object('s',slot,'i',item,'q',qtd,'d',dur) order by slot) from inventario where morador_id = mid), '[]'::json));
end $$;

-- mover/juntar/trocar itens entre slots (36–39 só aceitam a armadura certa)
create or replace function mover_item(p_token text, p_de int, p_para int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); a inventario; b inventario; ia itens; ib itens; cabe int;
  slots_arm text[] := array['cabeca','peito','pernas','pes'];
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if p_de = p_para or p_de not between 0 and 39 or p_para not between 0 and 39 then return json_build_object('ok',false,'erro','Movimento inválido'); end if;
  select * into a from inventario where morador_id = mid and slot = p_de;
  if not found then return json_build_object('ok',false,'erro','Não tem nada aí'); end if;
  select * into b from inventario where morador_id = mid and slot = p_para;
  select * into ia from itens where id = a.item;
  if p_para >= 36 and (ia.tipo <> 'armadura' or ia.slot_armadura <> slots_arm[p_para - 35]) then return json_build_object('ok',false,'erro','Isso não vai nesse lugar'); end if;
  if b.item is not null then
    select * into ib from itens where id = b.item;
    if p_de >= 36 and (ib.tipo <> 'armadura' or ib.slot_armadura <> slots_arm[p_de - 35]) then return json_build_object('ok',false,'erro','Isso não vai nesse lugar'); end if;
    if b.item = a.item and ia.empilha > 1 then                         -- junta pilhas
      cabe := least(a.qtd, ia.empilha - b.qtd);
      update inventario set qtd = qtd + cabe where morador_id = mid and slot = p_para;
      if cabe = a.qtd then delete from inventario where morador_id = mid and slot = p_de;
      else update inventario set qtd = qtd - cabe where morador_id = mid and slot = p_de; end if;
      return json_build_object('ok',true);
    end if;
    delete from inventario where morador_id = mid and slot = p_para;            -- troca de lugar
  end if;
  update inventario set slot = p_para where morador_id = mid and slot = p_de;
  if b.item is not null then insert into inventario values (mid, p_de, b.item, b.qtd, b.dur); end if;
  return json_build_object('ok',true);
end $$;

create or replace function descartar_item(p_token text, p_slot int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  delete from inventario where morador_id = mid and slot = p_slot;
  return json_build_object('ok',true);
end $$;

create or replace function craftar(p_token text, p_receita text, p_vezes int default 1) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador; rc receitas; ing record; v int := greatest(1, least(coalesce(p_vezes,1), 64));
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  j := jogo_jogador(mid);
  select * into rc from receitas where id = p_receita;
  if not found then return json_build_object('ok',false,'erro','Receita não existe'); end if;
  if j.rank < rc.rank_min then return json_build_object('ok',false,'erro','Precisa do rank ' || (select nome from ranks where nivel = rc.rank_min)); end if;
  begin
    for ing in select key, value::int as n from jsonb_each_text(rc.ingredientes) loop
      if not jogo_tirar(mid, ing.key, ing.n * v) then raise exception 'FALTA:%', ing.key; end if;
    end loop;
    if jogo_add(mid, rc.resultado, rc.qtd * v) > 0 then raise exception 'MOCHILA_CHEIA'; end if;
  exception when raise_exception then
    if sqlerrm like 'FALTA:%' then return json_build_object('ok',false,'erro','Falta ' || (select nome from itens where id = substr(sqlerrm, 7))); end if;
    return json_build_object('ok',false,'erro','Mochila cheia');
  end;
  return json_build_object('ok',true,'item',rc.resultado,'qtd',rc.qtd * v);
end $$;

-- vender na loja: 'mercado' (cidade, compra tudo que tem preço) ou 'mina' (só minérios e coisas da mina)
create or replace function vender(p_token text, p_item text, p_qtd int, p_loja text) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador; it itens; bonus int; valor bigint; q int := coalesce(p_qtd, 0);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if q <= 0 or q > 2304 then return json_build_object('ok',false,'erro','Quantidade inválida'); end if;
  j := jogo_jogador(mid);
  select * into it from itens where id = p_item;
  if not found or it.venda <= 0 then return json_build_object('ok',false,'erro','A loja não compra isso'); end if;
  if p_loja = 'mina' and not it.mina then return json_build_object('ok',false,'erro','A loja da mina só compra minérios'); end if;
  if p_loja not in ('mercado','mina') then return json_build_object('ok',false,'erro','Loja inválida'); end if;
  -- ferramenta/armadura gasta vale proporcional ao que sobrou
  if it.durabilidade > 0 then
    if q <> 1 then return json_build_object('ok',false,'erro','Venda uma por vez'); end if;
    select floor(it.venda * dur::numeric / it.durabilidade) into valor from inventario
     where morador_id = mid and item = p_item and slot <= 35 order by dur desc limit 1;
    if valor is null then return json_build_object('ok',false,'erro','Você não tem isso'); end if;
  else valor := it.venda::bigint * q; end if;
  if not jogo_tirar(mid, p_item, q) then return json_build_object('ok',false,'erro','Você não tem isso tudo'); end if;
  select bonus_venda into bonus from ranks where nivel = j.rank;
  valor := floor(valor * (100 + coalesce(bonus, 0)) / 100.0);
  update jogador set moedas = moedas + valor, ganho_total = ganho_total + valor where morador_id = mid;
  return json_build_object('ok',true,'ganhou',valor,'moedas',(select moedas from jogador where morador_id = mid));
end $$;

create or replace function comprar(p_token text, p_item text, p_qtd int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); it itens; custo bigint; q int := coalesce(p_qtd, 0);
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  if q <= 0 or q > 64 then return json_build_object('ok',false,'erro','Quantidade inválida'); end if;
  perform jogo_jogador(mid);
  select * into it from itens where id = p_item;
  if not found or it.compra is null then return json_build_object('ok',false,'erro','O mercadinho não vende isso'); end if;
  custo := it.compra::bigint * q;
  update jogador set moedas = moedas - custo where morador_id = mid and moedas >= custo;
  if not found then return json_build_object('ok',false,'erro','Dinheiro insuficiente'); end if;
  if jogo_add(mid, p_item, q) > 0 then raise exception 'MOCHILA_CHEIA'; end if;
  return json_build_object('ok',true,'moedas',(select moedas from jogador where morador_id = mid));
exception when raise_exception then
  return json_build_object('ok',false,'erro','Mochila cheia');
end $$;

create or replace function rankup(p_token text) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador; prox ranks;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  j := jogo_jogador(mid);
  select * into prox from ranks where nivel = j.rank + 1;
  if not found then return json_build_object('ok',false,'erro','Você já está no rank máximo!'); end if;
  update jogador set moedas = moedas - prox.custo, rank = rank + 1 where morador_id = mid and moedas >= prox.custo and rank = j.rank;
  if not found then return json_build_object('ok',false,'erro','Faltam ' || (prox.custo - j.moedas) || ' moedas'); end if;
  return json_build_object('ok',true,'rank',prox.nivel,'nome',prox.nome);
end $$;

create or replace function ranking() returns json language sql stable security definer set search_path = public as $$
  select json_build_object(
    'ricos', coalesce((select json_agg(x) from (
       select j.morador_id as m, r.nome, j.moedas, j.rank from jogador j join registros r on r.morador_id = j.morador_id
        where not r.oculto and j.moedas > 0 order by j.moedas desc, j.morador_id limit 20) x), '[]'::json),
    'ranks', coalesce((select json_agg(x) from (
       select j.morador_id as m, r.nome, j.rank, j.ganho_total from jogador j join registros r on r.morador_id = j.morador_id
        where not r.oculto and j.rank > 0 order by j.rank desc, j.ganho_total desc limit 20) x), '[]'::json))
$$;

create or replace function usar_item(p_token text, p_slot int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); inv inventario; it itens;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  select * into inv from inventario where morador_id = mid and slot = p_slot;
  if not found then return json_build_object('ok',false,'erro','Não tem nada aí'); end if;
  select * into it from itens where id = inv.item;
  if it.tipo <> 'comida' then return json_build_object('ok',false,'erro','Isso não se come'); end if;
  if inv.qtd = 1 then delete from inventario where morador_id = mid and slot = p_slot;
  else update inventario set qtd = qtd - 1 where morador_id = mid and slot = p_slot; end if;
  return json_build_object('ok',true,'cura',it.cura,'item',it.id);
end $$;

-- quem quebrou o quê no explorar (o navegador esconde esses)
create or replace function explorar_estado() returns json language sql stable security definer set search_path = public as $$
  select coalesce(json_agg(id), '[]'::json) from mundo_obj where quebrado_ate > now()
$$;

create or replace function quebrar_obj(p_token text, p_obj int, p_slot int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador; o mundo_obj; q quebraveis; t record; ganhos jsonb;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  j := jogo_jogador(mid);
  select * into o from mundo_obj where id = p_obj for update;
  if not found then return json_build_object('ok',false,'erro','Isso não existe'); end if;
  if o.quebrado_ate is not null and o.quebrado_ate > now() then return json_build_object('ok',false,'erro','Alguém já quebrou','sumiu',true); end if;
  select * into q from quebraveis where tipo = o.tipo;
  select * into t from jogo_tempo(mid, q, p_slot);
  if t.erro is not null then return json_build_object('ok',false,'erro',t.erro); end if;
  if now() - j.ultima_quebra < make_interval(secs => (t.tempo * 0.6)::float8) then return json_build_object('ok',false,'erro','Calma, mais devagar'); end if;
  begin
    ganhos := jogo_dar_drops(mid, q.drops);
  exception when raise_exception then return json_build_object('ok',false,'erro','Mochila cheia'); end;
  if t.usou then perform jogo_gastar(mid, p_slot); end if;
  update mundo_obj set quebrado_ate = now() + make_interval(secs => q.respawn_s::float8) where id = p_obj;
  update jogador set ultima_quebra = now() where morador_id = mid;
  return json_build_object('ok',true,'ganhou',ganhos);
end $$;

-- duas camadas da mina (a sua e a de baixo, que é o chão). '.' = vazio
create or replace function mina_camadas(p_z int) returns json language sql stable security definer set search_path = public as $$
  select json_build_object(
    'gerada_em', (select gerada_em from mina_estado where id = 1),
    'proxima_em', (select gerada_em + make_interval(mins => intervalo_min) from mina_estado where id = 1),
    'camadas', (select json_object_agg(z, s) from (
        select z, string_agg(case when quebrado or tipo = 'ar' then '.' else
                 case tipo when 'b_terra' then 't' when 'b_pedra' then 'p' when 'b_carvao' then 'c' when 'b_ferro' then 'f'
                           when 'b_ouro' then 'o' when 'b_cristal' then 'k' when 'b_rubi' then 'r' else 'p' end end, '' order by y, x) s
          from mina where z between p_z and p_z + 1 group by z) c))
$$;

create or replace function minerar(p_token text, p_z int, p_x int, p_y int, p_slot int) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador; b mina; q quebraveis; t record; ganhos jsonb; cmax int;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  j := jogo_jogador(mid);
  select camada_max into cmax from ranks where nivel = j.rank;
  if p_z > cmax then return json_build_object('ok',false,'erro','Seu rank só deixa cavar até a camada ' || cmax); end if;
  select * into b from mina where z = p_z and x = p_x and y = p_y for update;
  if not found or b.quebrado or b.tipo = 'ar' then return json_build_object('ok',false,'erro','Já está vazio','sumiu',true); end if;
  select * into q from quebraveis where tipo = b.tipo;
  select * into t from jogo_tempo(mid, q, p_slot);
  if t.erro is not null then return json_build_object('ok',false,'erro',t.erro); end if;
  if now() - j.ultima_quebra < make_interval(secs => (t.tempo * 0.6)::float8) then return json_build_object('ok',false,'erro','Calma, mais devagar'); end if;
  begin
    ganhos := jogo_dar_drops(mid, q.drops);
  exception when raise_exception then return json_build_object('ok',false,'erro','Mochila cheia'); end;
  if t.usou then perform jogo_gastar(mid, p_slot); end if;
  update mina set quebrado = true where z = p_z and x = p_x and y = p_y;
  update jogador set ultima_quebra = now() where morador_id = mid;
  return json_build_object('ok',true,'ganhou',ganhos);
end $$;

create or replace function abater(p_token text, p_tipo text) returns json language plpgsql security definer set search_path = public as $$
declare mid int := sessao_morador(p_token); j jogador; bc bichos; ganhos jsonb;
begin
  if mid is null then return json_build_object('ok',false,'erro','Entre de novo'); end if;
  j := jogo_jogador(mid);
  select * into bc from bichos where tipo = p_tipo;
  if not found then return json_build_object('ok',false,'erro','Bicho desconhecido'); end if;
  if now() - j.ultimo_abate < make_interval(secs => bc.intervalo::float8) then return json_build_object('ok',false,'erro','Calma, mais devagar'); end if;
  begin
    ganhos := jogo_dar_drops(mid, bc.drops);
  exception when raise_exception then return json_build_object('ok',false,'erro','Mochila cheia'); end;
  update jogador set ultimo_abate = now() where morador_id = mid;
  return json_build_object('ok',true,'ganhou',ganhos);
end $$;

-- ---------------------------------------------------------------------
-- mudar de casa leva junto o jogo (dinheiro, rank, inventário)
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
  if to_regclass('public.lotes') is not null then execute 'update lotes set dono = $1 where dono = $2' using novo, mid; end if;   -- 11_terrenos.sql
  delete from registros where morador_id = mid;
  return json_build_object('ok',true,'morador',novo,'casa',p_casa,'antigo',mid);
end $$;

-- ---------------------------------------------------------------------
-- permissões: o site só chama estas
-- ---------------------------------------------------------------------
revoke all on function jogo_jogador(int), jogo_add(int,text,int), jogo_tirar(int,text,int), jogo_dar_drops(int,jsonb), jogo_gastar(int,int),
  jogo_tempo(int,quebraveis,int), gerar_mina() from public, anon, authenticated;
revoke all on function jogo_catalogo(), meu_jogo(text), mover_item(text,int,int), descartar_item(text,int), craftar(text,text,int),
  vender(text,text,int,text), comprar(text,text,int), rankup(text), ranking(), usar_item(text,int), explorar_estado(),
  quebrar_obj(text,int,int), mina_camadas(int), minerar(text,int,int,int,int), abater(text,text), trocar_casa(text,int,jsonb) from public;
grant execute on function jogo_catalogo(), meu_jogo(text), mover_item(text,int,int), descartar_item(text,int), craftar(text,text,int),
  vender(text,text,int,text), comprar(text,text,int), rankup(text), ranking(), usar_item(text,int), explorar_estado(),
  quebrar_obj(text,int,int), mina_camadas(int), minerar(text,int,int,int,int), abater(text,text), trocar_casa(text,int,jsonb) to anon, authenticated;
