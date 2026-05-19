# Handover — Dashboard Alvorada
**Responsável atual:** Luca  
**Responsável novo:** Mateus  
**Data:** Maio 2026

---

## 1. Visão Geral do Sistema

O dashboard é uma aplicação web que roda na nuvem e exibe:
- Notícias da Venezuela, mercado global, petróleo & gás e OFAC/sanções
- Cotação Brent e WTI em tempo real
- Gráfico de produção diária do campo (GED-14)
- KPIs do mês e registro de falhas

**URL pública:** https://alvorada.onrender.com  
**Atualização automática:** a cada 10 minutos  

**Infraestrutura:**
| Componente | Plataforma | Observação |
|---|---|---|
| Aplicação web | Render (Docker) | Gratuito; pode demorar ~30s para carregar se ficar inativo |
| Banco de dados | Render PostgreSQL | Gratuito; **expira em 90 dias** — ver Seção 6 |
| Código-fonte | GitHub | Repositório: `Lucamb0207/alvorada` |

---

## 2. O que o LUCA precisa fazer (transferência de acessos)

### 2.1 GitHub — Adicionar Mateus como colaborador
1. Acesse https://github.com/Lucamb0207/alvorada
2. Clique em **Settings → Collaborators → Add people**
3. Busque o usuário GitHub do Mateus e adicione com permissão **Write**
4. Mateus vai receber um e-mail de convite para aceitar

### 2.2 Render — Adicionar Mateus à conta
1. Acesse https://render.com → sua conta
2. Vá em **Account Settings → Teams** (ou convide via e-mail)
3. Adicione o e-mail do Mateus como membro do time
4. Se preferir, pode criar uma conta Render para o Mateus e transferir o serviço depois

### 2.3 DATABASE_URL — Compartilhar com segurança
A string de conexão com o banco contém senha e não deve ser enviada por WhatsApp ou e-mail comum.  
**Forma segura de compartilhar:**
- Usar um gerenciador de senhas (ex: Bitwarden gratuito, 1Password)
- Ou entregar pessoalmente / por ligação de vídeo

Para encontrar a URL:
1. Acesse https://render.com → **Dashboard → seu serviço PostgreSQL**
2. Clique em **Connect → External Database URL**
3. Copie a string completa (começa com `postgresql://...`)

---

## 3. O que o MATEUS precisa instalar no PC

### 3.1 Python 3.11
1. Acesse https://www.python.org/downloads/
2. Baixe a versão **3.11.x** (não use versões mais recentes por compatibilidade)
3. Durante a instalação: **marque a opção "Add Python to PATH"**
4. Para verificar: abra o PowerShell e digite `python --version`

### 3.2 Git
1. Acesse https://git-scm.com/download/win
2. Instale com as opções padrão
3. Para verificar: `git --version`

### 3.3 Clonar o repositório
Abra o PowerShell e rode:
```powershell
git clone https://github.com/Lucamb0207/alvorada.git
cd alvorada
pip install -r requirements.txt
```

### 3.4 Configurar a DATABASE_URL
No PowerShell, antes de rodar os scripts, sempre defina a variável:
```powershell
$env:DATABASE_URL = "postgresql://usuario:senha@host/banco"
```
> Substitua pela URL completa fornecida pelo Luca (ver Seção 2.3).
> Essa variável não fica salva — precisa ser definida toda vez que abrir um novo terminal.

**Opcional — salvar permanentemente no Windows:**
1. Busque "Variáveis de ambiente" no menu Iniciar
2. Em "Variáveis do usuário", clique em **Novo**
3. Nome: `DATABASE_URL` / Valor: a string completa
4. Assim não precisa digitar toda vez

---

## 4. Rotina Diária — Alimentar o banco de dados

### 4.1 Um relatório por vez (`parse_report.py`)
Use quando receber o relatório do dia e quiser processar imediatamente.

```powershell
python parse_report.py
```
1. Cole o texto do WhatsApp
2. Pressione **Enter**, depois **Ctrl+Z**, depois **Enter** novamente
3. O script mostra o preview dos dados extraídos
4. Digite `s` para confirmar e salvar

### 4.2 Vários relatórios de uma vez (`batch_import.py`)
Use para importar vários dias históricos de uma vez.

```powershell
python batch_import.py
```
1. Cole todos os relatórios, separados por uma linha contendo apenas `===`

**Exemplo de formato:**
```
*Fecha: 01-05-2026*
PB: 2.825 bls
PN: 2.793 bls
...
===
*Fecha: 03-05-2026*
PB: 2.902 bls
PN: 2.834 bls
...
```

2. Pressione **Enter → Ctrl+Z → Enter**
3. O script mostra um resumo de todos os dias encontrados
4. Digite `s` para salvar todos

### 4.3 O que o relatório precisa ter para ser lido corretamente
O parser busca os seguintes campos (aceita variações de maiúsculas/minúsculas):

| Campo no relatório | Exemplo |
|---|---|
| `Fecha:` | `Fecha: 19-05-2026` |
| `PB:` (bruto) | `PB: 3.013 bls` |
| `PN:` (neto) | `PN: 2.953 bls` |
| `OFERTA:` | `OFERTA: 2.950 bls` |
| `MES Operada BN:` | `MES Operada BN: 2790` |
| `MES Fiscalizada BN:` | `MES Fiscalizada BN: 2813` |
| `PDT) BN:` | `PDT) BN: 3041` |
| `VAR:` (vs PDT) | `VAR: - 88 BLS` |
| `Explicaciones:` | seguido de bullet points com as falhas |

> Se algum campo não for encontrado, ele fica como vazio no banco — não causa erro.

---

## 5. Estrutura do Projeto

```
dashboard/
├── app.py             # Aplicação principal (layout + callbacks)
├── fetchers.py        # Busca de notícias, Brent, WTI
├── db.py              # Conexão e queries no PostgreSQL
├── parse_report.py    # Parser de relatório individual
├── batch_import.py    # Importação em lote
├── requirements.txt   # Dependências Python
├── Dockerfile         # Configuração do container no Render
└── render.yaml        # Configuração do Render (referência)
```

### Como fazer alterações e publicar
1. Edite os arquivos com qualquer editor de texto (VS Code recomendado)
2. No PowerShell, dentro da pasta do projeto:
```powershell
git add .
git commit -m "Descrição da mudança"
git push
```
3. Acesse https://render.com → serviço **alvorada-dashboard**
4. Clique em **Manual Deploy → Deploy latest commit**
5. Aguarde ~3 minutos para o deploy concluir

---

## 6. Avisos Importantes

### Banco de dados expira em 90 dias (plano gratuito do Render)
O PostgreSQL gratuito do Render é apagado automaticamente após 90 dias.  
**Ações antes do vencimento:**
- Fazer backup dos dados: no Render, acesse o banco → **PSQL Command** → exporte com `pg_dump`
- Ou migrar para o plano pago ($7/mês) para evitar interrupção
- Ou recriar o banco gratuito e reimportar os dados via `batch_import.py`

### Dashboard pode demorar para carregar
No plano gratuito, o serviço web "dorme" após 15 minutos sem acesso.  
Na primeira visita do dia, pode levar até 60 segundos para carregar. Isso é normal.  
Para eliminar esse comportamento: upgrade para o plano pago do Render (~$7/mês).

### Nunca compartilhe a DATABASE_URL publicamente
Essa string contém usuário e senha do banco. Não coloque no GitHub, WhatsApp, ou e-mail.

---

## 7. Contato e Suporte

Em caso de dúvidas técnicas, o histórico completo do desenvolvimento está disponível  
no repositório GitHub e na conversa com o Claude Code (Anthropic).

Para reabrir uma conversa de suporte técnico, acesse https://claude.ai e descreva o problema  
mencionando que o projeto é o **dashboard Alvorada** hospedado no Render.
