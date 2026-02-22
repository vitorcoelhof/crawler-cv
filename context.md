# PRD — Plataforma de Match Automático de Currículo com Vagas Remotas

## 1. Visão Geral do Produto

### Objetivo

Construir uma aplicação que:

1. Recebe um currículo (PDF ou TXT)
2. Analisa e extrai qualificações, palavras-chave e área de atuação
3. Busca automaticamente vagas abertas nos sites das empresas listadas em:
   https://github.com/lerrua/remote-jobs-brazil
4. Retorna vagas compatíveis com o perfil do candidato

---

## 2. Problema

Candidatos precisam:

- Entrar manualmente em dezenas de sites
- Filtrar vagas manualmente
- Ler descrições extensas
- Verificar compatibilidade manualmente

Isso consome tempo e gera frustração.

---

## 3. Proposta de Solução

Criar um motor automatizado de matching de currículo com vagas remotas brasileiras, contendo:

- Extração semântica de perfil via IA
- Crawling inteligente de páginas de carreiras (rodando em GitHub Actions)
- Matching por NLP local
- Ranking de compatibilidade
- CLI Python para uso local
- Output HTML interativo com filtros

---

## 4. Persona

Profissional Tech brasileiro:

- Desenvolvedor
- Produto
- Design
- Marketing
- Dados

Que busca vagas remotas e quer agilidade no processo.

---

## 5. Abordagem Técnica

### 5.1 Arquitetura Geral (CLI Python + Crawler GitHub Actions)

**Fluxo:**

```
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions (Daily Cron)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Clonar repo lerrua/remote-jobs-brazil             │ │
│  │  2. Extrair lista de empresas e URLs                  │ │
│  │  3. Fazer crawl de cada site (Playwright + BS4)       │ │
│  │  4. Salvar vagas coletadas em data/jobs.json          │ │
│  │  5. Commit e push automático                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               Git Repository (seu projeto)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  data/jobs.json  ← Cache de vagas coletadas           │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           CLI Local: python cli.py resume.pdf              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Parse PDF → extrai texto do currículo             │ │
│  │  2. Análise via Groq → extrai skills, senioridade    │ │
│  │  3. Lê data/jobs.json                                 │ │
│  │  4. Matching: compara perfil vs cada vaga             │ │
│  │  5. Ranking por compatibilidade %                     │ │
│  │  6. Gera HTML interativo → abre no browser            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Funcionalidades

### 6.1 Crawler (GitHub Actions)

#### Requisitos Funcionais

- **RF1:** Clonar repositório lerrua/remote-jobs-brazil
- **RF2:** Extrair lista de empresas e URLs oficiais
- **RF3:** Detectar página de carreiras (Trabalhe Conosco, Vagas, Careers, etc.)
- **RF4:** Fazer scraping de vagas abertas com Playwright (JS rendering) + BeautifulSoup
- **RF5:** Detectar ATS automaticamente (Greenhouse, Gupy, Lever, Workable, Kenoby)
- **RF6:** Normalizar e estruturar dados de vagas
- **RF7:** Salvar em `data/jobs.json`
- **RF8:** Commit automático ao repositório

#### Requisitos Não-Funcionais

- **RNF1:** Execução diária (cron às 09:00 UTC)
- **RNF2:** Tempo de execução < 10 minutos
- **RNF3:** Tratamento de falhas com retry (max 3 tentativas por site)
- **RNF4:** Rotação de User-Agent
- **RNF5:** Rate limiting (1 req/segundo por site)
- **RNF6:** Cache de páginas já processadas (evita re-scraping)

#### Estrutura de Dados — `data/jobs.json`

```json
[
  {
    "id": "uuid-string",
    "empresa": "Empresa X",
    "titulo": "Backend Developer",
    "descricao": "Descrição completa da vaga...",
    "requisitos": "Python, AWS, Docker, PostgreSQL",
    "skills_detectadas": ["Python", "AWS", "Docker", "PostgreSQL"],
    "senioridade": "Pleno",
    "localizacao": "Remoto - Brasil",
    "link": "https://empresa.com/vagas/123",
    "data_coleta": "2026-02-22",
    "ats": "Greenhouse",
    "url_empresa": "https://empresa.com",
    "salario_min": null,
    "salario_max": null
  }
]
```

---

### 6.2 Parser de Currículo (CLI Local)

#### Requisitos Funcionais

- **RF1:** Upload/leitura de PDF
- **RF2:** Upload/leitura de TXT
- **RF3:** Extração de texto bruto
- **RF4:** Normalização de texto

#### Requisitos Não-Funcionais

- **RNF1:** Tempo de parse < 2 segundos
- **RNF2:** Suporte a arquivos até 5MB
- **RNF3:** Tratamento de erros com mensagens claras

---

### 6.3 Análise de Currículo (Groq API)

#### Objetivo

Extrair automaticamente:

- Área principal (ex: Backend, Frontend, Data, Product, Design, QA)
- Hard skills (tecnologias)
- Soft skills
- Senioridade (Junior, Pleno, Senior, Lead)
- Stack tecnológica
- Anos de experiência
- Palavras-chave principais

#### Técnicas

- LLM (Groq Llama 3.3 70B) com response_format JSON
- Prompt em PT-BR

#### Output Estruturado

```json
{
  "area": "Backend",
  "senioridade": "Pleno",
  "skills": ["Python", "Django", "AWS", "PostgreSQL"],
  "soft_skills": ["Liderança", "Comunicação"],
  "anos_experiencia": 4,
  "keywords": ["Python", "Backend", "AWS", "Django", "REST API"],
  "empresas_anteriores": ["Empresa A", "Empresa B"]
}
```

---

### 6.4 Matching & Scoring

#### Algoritmo

```python
score = (
  0.5 * overlap_skills(profile.skills, job.skills) +
  0.3 * senioridade_match(profile.senioridade, job.senioridade) +
  0.2 * semantic_similarity(profile.keywords, job.description)
)
```

- **Overlap de Skills** (50%): Quantas skills do currículo aparecem na vaga
- **Match de Senioridade** (30%): Se a senioridade é compatível ou próxima
- **Similaridade Semântica** (20%): Embedding-based similarity (sentence-transformers)

#### Output

```json
{
  "matches": [
    {
      "vaga": {...},
      "score": 0.87,
      "motivo": "Match de 5 skills, senioridade compatível"
    }
  ],
  "rank_position": 1
}
```

---

### 6.5 Output HTML Interativo

#### Requisitos

- Tabela com colunas: Empresa | Título | Compatibilidade % | Habilidades Detectadas | Link
- Filtros interativos:
  - Por empresa
  - Por skill
  - Por senioridade
  - Por compatibilidade mínima (range slider)
- Cards expansíveis com descrição completa da vaga
- Links diretos para candidatura
- Número total de matches
- Resumo do perfil do candidato (lado esquerdo)

#### Stack

- **Gerador:** Jinja2 templates
- **Interatividade:** HTML5 + Alpine.js (leve) ou vanilla JS
- **Estilo:** Tailwind CSS

---

## 7. Stack Técnico

### Backend (Python)

```
Crawler:
├── playwright         → Navegação e JS rendering
├── beautifulsoup4     → Parsing HTML
├── pdfplumber         → Extração de texto de PDF
├── requests           → HTTP client
├── groq-sdk           → Análise de currículo

Matching & Analysis:
├── sentence-transformers → Embeddings semânticos
└── scikit-learn       → (opcional) ML utilities

CLI & Output:
├── click ou typer     → Framework CLI
├── jinja2             → Template HTML
└── rich               → Tabelas e colors no terminal
```

### Automação

- **GitHub Actions:** Cron + Workflow YAML
- **Node.js:** Trigger de crawling (opcional)

---

## 8. Estrutura de Pastas

```
crawler-cv/
├── data/
│   └── jobs.json          ← Cache de vagas (gerado pelo crawler)
├── .github/workflows/
│   └── crawl.yml          ← Cron diário para fazer crawling
├── src/
│   ├── cli.py             ← Entrada principal: `python cli.py resume.pdf`
│   ├── crawler/
│   │   ├── companies.py   ← Parser do repositório lerrua
│   │   ├── scraper.py     ← Lógica de scraping (Playwright + BS4)
│   │   └── ats.py         ← Detecção de Greenhouse, Gupy, etc.
│   ├── resume/
│   │   ├── parser.py      ← Extração de texto (PDF + TXT)
│   │   └── analyzer.py    ← Análise via Groq (skills, senioridade)
│   ├── matching/
│   │   ├── scorer.py      ← Lógica de ranking de compatibilidade
│   │   └── embeddings.py  ← Similaridade semântica
│   └── output/
│       ├── html.py        ← Gerador de HTML interativo
│       └── templates/
│           └── results.html
├── requirements.txt
├── .env.example
└── README.md
```

---

## 9. Fluxo Detalhado

### 9.1 Crawler (Executa no GitHub Actions — Daily)

1. **Setup:** Clone do repo lerrua/remote-jobs-brazil
2. **Extração de Empresas:** Parse de README ou arquivo estruturado
3. **Para cada empresa:**
   - Normalizar URL oficial
   - Testar heurísticas de carreiras (careers.*, jobs.*, /careers, /vagas, etc.)
   - Fazer request para detectar página de carreiras
4. **Scraping:**
   - Detectar ATS (Greenhouse, Gupy, Lever, etc.)
   - Se ATS detectado: tentar endpoint público ou JSON API
   - Se não: usar Playwright + BeautifulSoup
5. **Normalização:** Extrair título, descrição, requisitos, senioridade
6. **Armazenamento:** Merge com `data/jobs.json` existente (evita duplicatas por URL)
7. **Commit:** Git add, commit, push automático

### 9.2 CLI Local — Comando: `python cli.py resume.pdf`

1. **Parse do Currículo:**
   - Se PDF: `pdfplumber.open(resume.pdf)` → extrai texto
   - Se TXT: lê arquivo direto
   - Normaliza whitespace

2. **Análise via Groq:**
   ```
   Prompt (PT-BR):
   "Analise este currículo e retorne um JSON com:
   - area (Backend/Frontend/Data/etc)
   - senioridade (Junior/Pleno/Senior)
   - skills (lista)
   - soft_skills (lista)
   - anos_experiencia (número)
   - keywords (lista de termos principais)

   Currículo:
   {raw_text}"
   ```

3. **Carrega vagas:** Lê `data/jobs.json`

4. **Scoring:** Para cada vaga, calcula score (0.0 - 1.0)

5. **Ranking:** Ordena por score desc, filtra >= 0.5 (configurável)

6. **Geração HTML:** Jinja2 template com os matches

7. **Output:** Salva em `results_[timestamp].html` e abre automaticamente no browser

---

## 10. Requisitos Não-Funcionais Gerais

| Requisito | Meta |
|-----------|------|
| Upload de CV | Até 5MB, PDF e TXT |
| Parse do CV | < 2 segundos |
| Análise via Groq | < 10 segundos |
| Matching | < 1 segundo (JSON em memória) |
| Geração HTML | < 500ms |
| **Total CLI** | **< 15 segundos** |
| Crawling (daily) | < 10 minutos |
| Disponibilidade crawler | 99% (GitHub Actions) |
| Retenção de dados | Histórico de vagas último 30 dias |

---

## 11. MVP (Mínimo Viável)

**Escopo da V1:**

- ✅ Crawler funcionando (extrai ~500-1000 vagas)
- ✅ Parser de currículo (PDF + TXT)
- ✅ Análise via Groq
- ✅ Matching & scoring básico
- ✅ HTML com tabela filtrada

**Fora do MVP (V2+):**

- ❌ Autenticação de usuários
- ❌ Histórico de buscas
- ❌ Favoritas/wishlist
- ❌ Notificações de novas vagas
- ❌ App mobile
- ❌ Web interface (deploy em servidor)

---

## 12. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|--------|-----------|
| Sites bloqueiam bot | Alta | Alto | Rotação de User-Agent, delays entre requests, Playwright headless |
| Estrutura HTML muda | Alta | Médio | CSS selectors fallback, ATS detection, monitoring |
| Groq API rate limit | Média | Médio | Caching de análises, batch processing |
| Arquivo JSON muito grande | Baixa | Médio | Compressão, histórico com data_coleta |
| GitHub Actions timeout | Baixa | Alto | Split em múltiplos jobs, paralelização por região |

---

## 13. Métricas de Sucesso

- ✅ Crawler coleta > 500 vagas por execução
- ✅ Acurácia do matching > 70% (validação manual)
- ✅ CLI executa em < 15 segundos
- ✅ 0 crashes na análise de CVs com formato livre
- ✅ HTML carrega e filtra sem lag

---

## 14. Próximos Passos

1. **Planning:** Quebrar em fases e tarefas específicas
2. **Implementação:** Começar pelo parser de currículo (mais simples)
3. **Depois:** Crawler (mais complexo)
4. **Testes:** Validar com 10-20 CVs reais
5. **Launch:** V1 no repositório público
