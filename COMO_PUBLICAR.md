# Como rodar e publicar o site da vila

## 1. Rodar no seu PC (porta 3003)

Precisa só do Node instalado (já tem). Na pasta do projeto:

```
node servidor_local.js
```

Abre **http://localhost:3003**. Nesse modo tudo é salvo em `banco_local.json`
(é só pra testar; esse arquivo não vai pro GitHub).

Pra ver no celular na mesma rede Wi-Fi: descubra o IP do PC (`ipconfig`, linha
"Endereço IPv4", ex. 192.168.0.10) e abra `http://192.168.0.10:3003` no celular.
Se não abrir, libere o Node no Firewall do Windows quando ele perguntar.

---

## 2. Criar o banco no Supabase (grátis, ~5 minutos)

1. Entre em **https://supabase.com** → **Start your project** → entre com o GitHub.
2. **New project**:
   - Name: `cidade-dos-seguidores`
   - Database Password: clique em *Generate* e **guarde essa senha** num lugar seguro
   - Region: **South America (São Paulo)**
   - Clique **Create new project** e espere uns 2 minutos.
3. No menu da esquerda, abra **SQL Editor** → **New query**.
4. Abra o arquivo `supabase/1_criar_banco.sql` deste projeto, copie **tudo**, cole lá e clique **Run**.
   Tem que aparecer *"Success. No rows returned"*.
5. **New query** de novo → copie tudo de `supabase/2_palavras_bloqueadas.sql` → cole → **Run**.
   (Lista de nomes proibidos: palavrões, ofensas e termos pejorativos.)
6. **New query** de novo → copie tudo de `site/dados/novos_moradores.sql` → cole → **Run**.
   (Isso cria os 370 moradores.)
   Depois rode também `supabase/3_contador.sql` (contador de seguidores ao vivo no topo do site).
   Pra atualizar o número à mão: `update contador set seguidores = 381, atualizado_em = now() where id = 1;`

   Por último `supabase/5_bio_e_pedidos.sql` (frase de bio de cada morador + botão Recusar nos pedidos de amizade).

### Contador automático pelo YouTube (a cada 10 min)
1. **Chave do Google:** console.cloud.google.com → crie um projeto (ex. "cidade-seguidores") →
   **APIs e serviços → Biblioteca** → procure **YouTube Data API v3** → **Ativar** →
   **Credenciais → Criar credenciais → Chave de API** → copie.
   Em **Editar chave → Restrições de API**, marque só **YouTube Data API v3** e salve.
2. **Guardar a chave no cofre do Supabase** (SQL Editor, troque pelo sua chave):
   `select vault.create_secret('SUA_CHAVE_AQUI', 'youtube_api_key');`
3. Rode `supabase/4_contador_youtube.sql`.
4. Espere uns segundos e rode `select contador_youtube();` de novo → o número aparece no site.
   Pra ver se deu algum erro: `select ultimo_erro, conferido_em from contador_config;`

Obs.: acima de 1.000 inscritos o YouTube arredonda o número (1.234 aparece como 1.230).
Trocar a chave depois: `select vault.update_secret((select id from vault.secrets where name = 'youtube_api_key'), 'CHAVE_NOVA');`
7. Confira: menu **Table Editor** → tabela `moradores` deve ter 370 linhas.

### Pegar as chaves
8. Menu **Project Settings** (engrenagem) → **API** (ou **Data API**).
9. Copie:
   - **Project URL** (ex: `https://abcdefgh.supabase.co`)
   - **anon public** key (um texto enorme começando com `eyJ...`)
     → nos projetos novos pode aparecer como **Publishable key** (`sb_publishable_...`); serve igual.
10. Cole as duas no arquivo `site/config.js`:

```js
window.VILA_CONFIG = {
  SUPABASE_URL: 'https://abcdefgh.supabase.co',
  SUPABASE_ANON_KEY: 'eyJhbGciOi...',
};
```

> A chave **anon/publishable** pode ficar no site, ela é pública. **Nunca** coloque a
> chave `service_role` / `secret` no site.

Pronto: rodando `node servidor_local.js` de novo, o site já usa o Supabase
(o console do navegador deixa de mostrar "modo LOCAL").

---

## 3. Colocar o site no ar (Vercel, grátis)

O site é só a pasta `site/` (HTML + JS + imagens). O mais fácil:

1. Entre em **https://vercel.com** com o GitHub.
2. **Add New… → Project** → escolha o repositório **seguidorescity** → **Import**.
3. Em **Root Directory** clique **Edit** e escolha a pasta **`site`**.
4. Framework Preset: **Other**. Não precisa de build. Clique **Deploy**.
5. Em 1 minuto ele te dá um link tipo `seguidorescity.vercel.app` → esse é o **link da bio**.

Toda vez que você der `git push`, a Vercel atualiza o site sozinha.

(Alternativa: Netlify ou Cloudflare Pages funcionam igual — "publish directory" = `site`.)

### Domínio próprio (opcional)
Vercel → seu projeto → **Settings → Domains** → digite o domínio e siga as instruções de DNS.

---

## 4. A cada episódio novo

1. Gere os arquivos: `cd codigo` e `python3 exportar_site.py ../site`
2. No Supabase → SQL Editor → rode o `site/dados/novos_moradores.sql` novo
   (pode rodar de novo à vontade: ele ignora quem já existe).
3. `git add . && git commit -m "ep. 4" && git push` → a Vercel publica.

Os registros antigos continuam: o morador 205 é sempre o 205, com o nome e o visual que o dono salvou.

---

## 5. Moderação (no SQL Editor do Supabase)

```sql
-- esconder o nome de alguém (o boneco volta a ser "Morador #id")
update registros set oculto = true where usuario = 'fulano';
-- liberar o morador de novo (apaga o registro e as amizades dele)
delete from registros where usuario = 'fulano';
-- adicionar palavra proibida na hora (sem acento, minúsculo)
insert into palavras_bloqueadas values ('palavra');
-- pra ficar permanente: coloque na lista PROPRIA de supabase/gerar_palavras.js,
-- rode "npm install" (1 vez) e "npm run palavras", e rode o 2_palavras_bloqueadas.sql de novo
-- alguém esqueceu o PIN: apague o registro e peça pra registrar de novo
```

## O que o site faz
- Mapa ao vivo pela hora de Brasília (dia/noite), arrastar e pinça/roda pra zoom.
- Menu: **Buscar** (nome, @ ou número), **Moradores** (na rua agora, com nome, livres, meus amigos),
  **Registrar** (escolher no mapa / aleatório → personalizar → nome, @ e PIN), **Eu/Entrar**.
- **Personalizar**: pele, cabelo, cor do cabelo, óculos, barba, chapéu, roupa, estampa, cores, sapato.
  Nada é salvo sozinho: só quando aperta **💾 Salvar** (e o site avisa se você tentar sair sem salvar).
- **Amigos** (logado): adicionar/remover, amizade mútua ★, nível de amizade (❤) pelos dias em que as
  rotinas se cruzaram, "hoje vocês estão juntos na praça às 10:20", e corações no mapa quando
  seu morador encontra um amigo.
- Link direto: `seusite/?m=205` abre seguindo o morador 205.
