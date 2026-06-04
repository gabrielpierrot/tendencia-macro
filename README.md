# Rastreador Macro — WDO & WIN

Painel de fatores macroeconômicos em tempo real para day trade no Mini Dólar (WDO) e Mini Índice (WIN).

## Como fazer o deploy no Streamlit Cloud

### Passo 1 — Criar repositório no GitHub
1. Acesse github.com e faça login
2. Clique em **"New repository"** (botão verde)
3. Nome sugerido: `rastreador-macro`
4. Deixe como **Public**
5. Clique em **"Create repository"**

### Passo 2 — Enviar os arquivos
1. Na página do repositório criado, clique em **"uploading an existing file"**
2. Arraste os 3 arquivos: `app.py`, `requirements.txt`, `README.md`
3. Clique em **"Commit changes"**

### Passo 3 — Deploy no Streamlit Cloud
1. Acesse **share.streamlit.io**
2. Clique em **"New app"**
3. Selecione o repositório `rastreador-macro`
4. Em **"Main file path"**, coloque: `app.py`
5. Clique em **"Deploy!"**

Pronto! Em ~2 minutos você terá uma URL pública para acessar o painel de qualquer dispositivo.

---

## Como usar no pregão

### Fatores automáticos (atualizam sozinhos)
- DXY, VIX, S&P 500, Petróleo, VALE3, USD/BRL

### DI Futuro (input manual — gatilho operacional)
Acompanhe o DI1F pelo TradingView (ticker: `BMF:DI1F26`) e clique:
- **DI SUBIU** → pressiona WIN, apoia WDO
- **DI CAIU** → apoia WIN, pressiona WDO
- **DI NEUTRO** → sem sinal do gatilho

### Leitura do gráfico
- **Verde acima** = pessimismo domina → Compra WDO / Venda WIN
- **Vermelho abaixo** = otimismo domina → Venda WDO / Compra WIN
- **Linha azul (Rastro do Macro)** = spread resultante
- **Linha amarela** = threshold configurável — sinal só é gerado quando o rastro cruza

---

## Fontes de dados
- Yahoo Finance (delay ~15min) — DXY, VIX, S&P, Petróleo, VALE3, BRL
- Input manual — DI Futuro (via TradingView: BMF:DI1F26)

*Não constitui recomendação de investimento.*
