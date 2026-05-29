# Tendências de Mercado

Dashboard de tendências do mercado de trabalho brasileiro.  
Coleta dados reais da **Adzuna API** e **Jooble API**, normaliza e armazena no **PostgreSQL**.

---

## Estrutura

```
tendencia-mercado/
├── coleta/
│   ├── main.py          ← executa o pipeline completo
│   ├── coletor.py       ← coleta da Adzuna e Jooble
│   ├── normalizador.py  ← normaliza os dados
│   ├── carregador.py    ← salva no PostgreSQL
│   ├── requirements.txt ← dependências Python
│   └── .env             ← chaves de API e banco
├── prisma/
│   └── schema.prisma    ← estrutura do banco para o Next.js
└── src/app/
    └── page.tsx         ← dashboard Next.js
```

---

## Como rodar

### 1. Instale as dependências Python

Abra um PowerShell na pasta `coleta/`:

```powershell
cd coleta
pip install -r requirements.txt
```

### 2. Configure o `.env`

Edite o arquivo `coleta/.env` com suas chaves e senha do banco.

### 3. Teste a conexão com o banco

```powershell
python carregador.py
```

Deve aparecer: `✅ Conexão com o banco OK!`

### 4. Execute o pipeline completo

```powershell
python main.py
```

Isso vai:
- Coletar vagas das duas APIs
- Normalizar os dados
- Salvar no PostgreSQL

### 5. Rode o Next.js (outro PowerShell)

```powershell
cd ..
npm install
npm run dev
```

Acesse: `http://localhost:3000`

---

## Observações

- Vagas com mais de 1 ano são automaticamente descartadas
- Duplicatas entre Adzuna e Jooble são removidas por título + empresa
- O banco é atualizado incrementalmente (sem apagar dados antigos)
