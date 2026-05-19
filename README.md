# Alvorada Intelligence Dashboard

Dashboard de monitoramento com notícias Venezuela O&G, mercado global, Brent e action items do Gmail.
Refresh automático a cada 10 minutos.

## Requisitos

- Node.js (v16+)
- Chave da API Anthropic com acesso ao Gmail MCP

## Setup

### 1. Baixe os arquivos

Coloque `server.js` e `index.html` na mesma pasta.

### 2. Defina sua API key

```bash
export ANTHROPIC_API_KEY=sk-ant-SUA_CHAVE_AQUI
```

### 3. Rode o servidor

```bash
node server.js
```

### 4. Abra no browser

```
http://localhost:3737
```

---

## Como funciona

- `server.js` → servidor Node.js puro (sem dependências npm) que proxeia chamadas à Anthropic API, resolvendo CORS
- `index.html` → dashboard completo com Chart.js via CDN

## Módulos

| Painel | Fonte | Intervalo |
|---|---|---|
| Venezuela O&G | Web search (Reuters, Argus, S&P Global) | 10 min |
| Mercado Global O&G | Web search | 10 min |
| Geopolítica & Macro | Web search | 10 min |
| Brent Crude | Web search + histórico 7d | 10 min |
| Agenda O&G | Hardcoded (Mai–Jun 2026) | Estático |
| Action Items | Gmail MCP | 10 min |

## Personalização

Para ajustar o intervalo de refresh, mude `600` (segundos) em `index.html`:
```js
let secondsLeft = 600;  // ← 600s = 10 min
```
