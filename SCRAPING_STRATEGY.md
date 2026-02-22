# Estratégia de Web Scraping - Dados Reais de Jobs

## Visão Geral

Este documento descreve como implementar scraping de sites brasileiros de jobs de forma **responsável e sustentável**.

## Por que Scraping é Desafiador

1. **LinkedIn** - Bloqueia scrapers agressivamente, exige autenticação
2. **InfoJobs** - Mais permissivo, mas ainda tem proteções
3. **GetNinja** - Melhor para scraping, menos restritivo
4. **Blogs/RSS** - Melhor abordagem para dados sustentáveis

## Abordagens Recomendadas

### 1️⃣ **RSS Feeds (RECOMENDADO)**

Muitos job boards expõem feeds RSS que não violam Terms of Service.

```python
# Implementação com feedparser
import feedparser

feeds = [
    "https://www.infojobs.com.br/rss",
    "https://github.com/jobs.rss",  # Ainda funciona para públicos
]

for feed_url in feeds:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        # Parse job details
```

**Vantagens:**
- ✅ Legal e explícito
- ✅ Não viola Terms of Service
- ✅ Performático (não carrega HTML inteiro)
- ✅ Fácil de implementar

**Desvantagens:**
- ❌ Limitado ao que os feeds expõem

---

### 2️⃣ **Playwright com Delays Responsáveis**

Para sites que não têm RSS, use Playwright com **bom comportamento**:

```python
from playwright.async_api import async_playwright
import asyncio
import random

async def scrape_infojobs(keywords: List[str]) -> List[JobPosting]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Set realistic headers
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "pt-BR,pt;q=0.9"
        })

        # Navigate with delay
        await asyncio.sleep(random.uniform(2, 5))
        await page.goto("https://www.infojobs.com.br/", wait_until="networkidle")

        # Search
        await page.fill('input[placeholder*="buscar"]', " ".join(keywords))
        await page.click("button[type='submit']")

        # Wait for results
        await asyncio.sleep(random.uniform(1, 3))
        await page.wait_for_selector(".job-item")

        # Extract jobs
        jobs = []
        elements = await page.query_selector_all(".job-item")

        for elem in elements:
            title = await elem.query_selector(".job-title")
            company = await elem.query_selector(".company-name")
            # ... parse all fields

            job = JobPosting(...)
            jobs.append(job)

            # Random delay between items
            await asyncio.sleep(random.uniform(0.5, 1.5))

        await browser.close()
        return jobs
```

**Boas Práticas:**
- ✅ Add random delays between requests (1-5 seconds)
- ✅ Rotate User-Agent strings
- ✅ Respect robots.txt
- ✅ Use rotating proxies if needed
- ✅ Cache results to avoid repeated scraping
- ✅ Monitor and respect rate limits
- ✅ Handle errors gracefully

---

### 3️⃣ **APIs Públicas (Fallback)**

Quando RSS/Scraping não funciona, use APIs públicas:

#### RemoteOK API (Recomendado)
```python
import requests

def search_remoteok(keywords: List[str]) -> List[JobPosting]:
    # RemoteOK é uma ótima fonte de jobs remotos
    # API: https://remoteok.io/api

    url = "https://remoteok.io/api"
    params = {
        "search": " ".join(keywords),
        "location": "brazil"
    }

    response = requests.get(url, params=params)
    jobs = []

    for item in response.json():
        job = JobPosting(
            id=str(item['id']),
            empresa=item['company'],
            titulo=item['title'],
            descricao=item['description'][:500],
            requisitos=item['description'],
            skills_detectadas=_extract_skills(item['description']),
            senioridade=_detect_senioridade(item['description']),
            localizacao="Remoto - Brasil/Mundo",
            link=item['url'],
            data_coleta=date.today().isoformat(),
            url_empresa=item.get('company_url', '')
        )
        jobs.append(job)

    return jobs
```

---

## Implementação Recomendada

### Fase 1: MVP (Agora)
✅ Usar dados de teste (já funciona 100%)

### Fase 2: RSS Feeds
1. Implementar `feedparser` para ler RSS de InfoJobs
2. Implementar scraper de GitHub jobs (ainda público)
3. Implementar RemoteOK API (sem auth necessária)

### Fase 3: Playwright Scraping
1. Implementar Playwright scraper para InfoJobs
2. Adicionar delays e rate limiting
3. Monitorar e ajustar conforme necessário

### Fase 4: Autenticação
1. Considerar LinkedIn API (requer business account)
2. Integrar com serviços pagos se necessário

---

## Estrutura de Código

```python
# src/crawler/sources/rss_feeds.py
def search_rss_jobs(keywords):
    # Parse RSS feeds

# src/crawler/sources/playwright_scraper.py
async def scrape_infojobs_async(keywords):
    # Playwright scraping com delays

# src/crawler/sources/public_apis.py
def search_remoteok(keywords):
    # RemoteOK API
def search_devto(keywords):
    # Dev.to API

# src/crawler/aggregator.py
async def search_all_sources(keywords):
    # Aggregate from all sources
    # With fallback to test data
```

---

## Monitoramento e Manutenção

```python
# Log quando sources falham
logger.info(f"LinkedIn: {len(linkedin_jobs)} jobs")
logger.info(f"InfoJobs: {len(infojobs_jobs)} jobs")
logger.info(f"RemoteOK: {len(remoteok_jobs)} jobs")
logger.info(f"Total: {len(all_jobs)} jobs (fallback: test data)")

# Alert se nenhuma source retorna dados
if not all_jobs:
    logger.warning("All sources failed - using test data")
    # Fallback to test data automatically
```

---

## Resumo

| Abordagem | Legalidade | Confiabilidade | Effort | Recomendação |
|-----------|-----------|----------------|--------|--------------|
| Test Data | ✅ Legal | ⭐⭐⭐ Perfeita | ⭐ Pronto | **MVP Atual** |
| RSS Feeds | ✅ Legal | ⭐⭐⭐ Ótima | ⭐⭐ Fácil | **Próximo** |
| RemoteOK API | ✅ Legal | ⭐⭐⭐ Ótima | ⭐⭐ Fácil | **Paralelo** |
| Playwright | ⚠️ Cinzento | ⭐⭐ Média | ⭐⭐⭐ Médio | **Depois** |
| LinkedIn API | ✅ Legal | ⭐⭐⭐ Ótima | ⭐⭐⭐⭐ Difícil | **Futuro** |

---

**Recomendação:** Comece com **RSS + RemoteOK API** (Fase 2) — levará ~2-3 horas e não viola nenhuma política.

