# CV Matcher - Job Aggregator & Resume Analyzer

Uma ferramenta em Python que analisa seu currículo e matcheia contra vagas remotas de múltiplas fontes.

## Uso Rápido

```bash
# Atualizar vagas
python -m src.crawler.main

# Analisar currículo
python -m src.cli seu_curriculo.pdf
```

## Instalação

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Editar .env com GROQ_API_KEY
```

## Features

- Análise inteligente de currículo com IA (Groq)
- Múltiplas fontes: RemoteOK, InfoJobs, RSS feeds
- Score de compatibilidade em HTML interativo
- CLI simples

## Fontes de Vagas

- RemoteOK API (22 vagas)
- InfoJobs com Playwright (1+ vagas)
- RSS feeds comunitários (1+ vagas)

## Algoritmo de Scoring

Score = 50% Skills + 30% Senioridade + 20% Similaridade

## Configuração

GROQ_API_KEY obtida em: https://console.groq.com

## Arquivos Ignorados

results_*.html - Resultados gerados (locais)
data/*.pdf, data/*.txt - Currículos
.env - Chaves secretas

## Licença

MIT
