import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time as time_module
import yfinance as yf
import requests
import os
import pytz

st.set_page_config(
    page_title="Tendência Macro | WDO & WIN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
* { box-sizing: border-box; }
.stApp { background: #0a0a0f; color: #e0e0e0; font-family: 'Inter', sans-serif; }
.main-header { text-align: center; padding: 1.5rem 0 0.5rem 0; border-bottom: 1px solid #1e1e2e; margin-bottom: 1.5rem; }
.main-header h1 { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; color: #ffffff; letter-spacing: 0.1em; margin: 0; }
.main-header p { color: #555577; font-size: 0.75rem; letter-spacing: 0.2em; margin: 0.3rem 0 0 0; text-transform: uppercase; }
.metric-card { background: #0f0f1a; border: 1px solid #1e1e2e; border-radius: 6px; padding: 0.8rem 1rem; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.5rem; }
.metric-label { font-size: 0.6rem; color: #444466; letter-spacing: 0.2em; text-transform: uppercase; }
.metric-value { font-size: 1.1rem; font-weight: 600; color: #ffffff; margin-top: 0.2rem; }
.section-title { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #444466; letter-spacing: 0.25em; text-transform: uppercase; margin-bottom: 0.8rem; padding-bottom: 0.3rem; border-bottom: 1px solid #1a1a2a; }
.stButton button { background: #1a1a2e !important; color: #aaaacc !important; border: 1px solid #2a2a4a !important; border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; letter-spacing: 0.1em !important; }
.stButton button:hover { background: #2a2a4e !important; border-color: #4a4a8a !important; color: #ffffff !important; }
div[data-testid="stSelectbox"] label, div[data-testid="stSlider"] label { color: #555577 !important; font-size: 0.7rem !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; font-family: 'JetBrains Mono', monospace !important; }
.timestamp { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #333355; text-align: right; }
.grupo-title { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: #333355; letter-spacing: 0.2em; text-transform: uppercase; margin: 1rem 0 0.4rem 0; padding: 0.3rem 0.6rem; background: #0d0d18; border-left: 2px solid #2a2a4a; }
</style>
""", unsafe_allow_html=True)

BR_TZ = pytz.timezone("America/Sao_Paulo")

# ─────────────────────────────────────────
# PERSISTÊNCIA
# ─────────────────────────────────────────
HISTORICO_FILE = "/tmp/historico_macro.csv"

def carregar_historico():
    try:
        if os.path.exists(HISTORICO_FILE):
            df = pd.read_csv(HISTORICO_FILE)
            hoje = datetime.now(BR_TZ).strftime("%Y-%m-%d")
            if "data" in df.columns:
                df = df[df["data"] == hoje]
            if "rastro" in df.columns:
                return df.to_dict("records")
    except:
        pass
    return []

def salvar_historico(historico):
    try:
        if historico:
            pd.DataFrame(historico).to_csv(HISTORICO_FILE, index=False)
    except:
        pass

if "historico" not in st.session_state:
    st.session_state.historico = carregar_historico()
if "ultimo_update" not in st.session_state:
    st.session_state.ultimo_update = None

# ─────────────────────────────────────────
# DEFINIÇÃO DOS FATORES EXPANDIDOS
# ─────────────────────────────────────────
FATORES = {
    # EUA — Renda variável
    "SP500":     {"ticker": "ES=F",       "nome": "S&P 500 Futuros",       "grupo": "🇺🇸 EUA — Bolsas",      "direcao": "direto",   "peso_wdo": 2, "peso_win": 3},
    "NASDAQ":    {"ticker": "NQ=F",       "nome": "Nasdaq Futuros",         "grupo": "🇺🇸 EUA — Bolsas",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 3},
    "DOW":       {"ticker": "YM=F",       "nome": "Dow Jones Futuros",      "grupo": "🇺🇸 EUA — Bolsas",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    "RUSSELL":   {"ticker": "RTY=F",      "nome": "Russell 2000",           "grupo": "🇺🇸 EUA — Bolsas",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    "VIX":       {"ticker": "^VIX",       "nome": "VIX — Volatilidade",     "grupo": "🇺🇸 EUA — Bolsas",      "direcao": "inverso",  "peso_wdo": 2, "peso_win": 3},
    # EUA — Juros
    "T2Y":       {"ticker": "^IRX",       "nome": "Treasury 2 anos",        "grupo": "🇺🇸 EUA — Juros",       "direcao": "inverso",  "peso_wdo": 2, "peso_win": 1},
    "T5Y":       {"ticker": "^FVX",       "nome": "Treasury 5 anos",        "grupo": "🇺🇸 EUA — Juros",       "direcao": "inverso",  "peso_wdo": 2, "peso_win": 1},
    "T10Y":      {"ticker": "^TNX",       "nome": "Treasury 10 anos",       "grupo": "🇺🇸 EUA — Juros",       "direcao": "inverso",  "peso_wdo": 2, "peso_win": 2},
    "T30Y":      {"ticker": "^TYX",       "nome": "Treasury 30 anos",       "grupo": "🇺🇸 EUA — Juros",       "direcao": "inverso",  "peso_wdo": 1, "peso_win": 1},
    # Dólar e Câmbio
    "DXY":       {"ticker": "DX-Y.NYB",   "nome": "DXY — Índice do Dólar",  "grupo": "💵 Câmbio Global",      "direcao": "inverso",  "peso_wdo": 3, "peso_win": 1},
    "EUR":       {"ticker": "EURUSD=X",   "nome": "EUR/USD",                "grupo": "💵 Câmbio Global",      "direcao": "direto",   "peso_wdo": 2, "peso_win": 1},
    "JPY":       {"ticker": "JPY=X",      "nome": "USD/JPY",                "grupo": "💵 Câmbio Global",      "direcao": "inverso",  "peso_wdo": 1, "peso_win": 1},
    "BRL":       {"ticker": "BRL=X",      "nome": "USD/BRL",                "grupo": "💵 Câmbio Global",      "direcao": "inverso",  "peso_wdo": 3, "peso_win": 1},
    # Commodities
    "PETR_WTI":  {"ticker": "CL=F",       "nome": "Petróleo WTI",           "grupo": "🛢 Commodities",        "direcao": "ambiguo",  "peso_wdo": 1, "peso_win": 1},
    "PETR_BRENT":{"ticker": "BZ=F",       "nome": "Petróleo Brent",         "grupo": "🛢 Commodities",        "direcao": "ambiguo",  "peso_wdo": 1, "peso_win": 1},
    "OURO":      {"ticker": "GC=F",       "nome": "Ouro",                   "grupo": "🛢 Commodities",        "direcao": "inverso",  "peso_wdo": 1, "peso_win": 1},
    "PRATA":     {"ticker": "SI=F",       "nome": "Prata",                  "grupo": "🛢 Commodities",        "direcao": "inverso",  "peso_wdo": 1, "peso_win": 1},
    "COBRE":     {"ticker": "HG=F",       "nome": "Cobre",                  "grupo": "🛢 Commodities",        "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    "SOJA":      {"ticker": "ZS=F",       "nome": "Soja",                   "grupo": "🛢 Commodities",        "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    "MILHO":     {"ticker": "ZC=F",       "nome": "Milho",                  "grupo": "🛢 Commodities",        "direcao": "direto",   "peso_wdo": 1, "peso_win": 1},
    "GAS":       {"ticker": "NG=F",       "nome": "Gás Natural",            "grupo": "🛢 Commodities",        "direcao": "ambiguo",  "peso_wdo": 1, "peso_win": 1},
    # Brasil
    "IBOV":      {"ticker": "^BVSP",      "nome": "Ibovespa",               "grupo": "🇧🇷 Brasil",            "direcao": "direto",   "peso_wdo": 1, "peso_win": 3},
    "VALE3":     {"ticker": "VALE3.SA",   "nome": "VALE3",                  "grupo": "🇧🇷 Brasil",            "direcao": "direto",   "peso_wdo": 1, "peso_win": 3},
    "PETR4":     {"ticker": "PETR4.SA",   "nome": "PETR4",                  "grupo": "🇧🇷 Brasil",            "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    # Europa
    "DAX":       {"ticker": "^GDAXI",     "nome": "DAX — Alemanha",         "grupo": "🌍 Europa & Ásia",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    "CAC":       {"ticker": "^FCHI",      "nome": "CAC 40 — França",        "grupo": "🌍 Europa & Ásia",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 1},
    "FTSE":      {"ticker": "^FTSE",      "nome": "FTSE 100 — UK",          "grupo": "🌍 Europa & Ásia",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 1},
    # Ásia
    "NIKKEI":    {"ticker": "^N225",      "nome": "Nikkei — Japão",         "grupo": "🌍 Europa & Ásia",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    "HANGSENG":  {"ticker": "^HSI",       "nome": "Hang Seng — HK",         "grupo": "🌍 Europa & Ásia",      "direcao": "direto",   "peso_wdo": 1, "peso_win": 2},
    # Sentimento / Risco emergente
    "EEM":       {"ticker": "EEM",        "nome": "ETF Emergentes (EEM)",   "grupo": "📡 Sentimento Global",  "direcao": "direto",   "peso_wdo": 2, "peso_win": 2},
    "HYG":       {"ticker": "HYG",        "nome": "ETF High Yield (HYG)",   "grupo": "📡 Sentimento Global",  "direcao": "direto",   "peso_wdo": 2, "peso_win": 2},
    "TIP":       {"ticker": "TIP",        "nome": "ETF TIPS (Inflação EUA)","grupo": "📡 Sentimento Global",  "direcao": "inverso",  "peso_wdo": 1, "peso_win": 1},
}

LIMIAR_PADRAO = 0.3
LIMIARES = {"VIX": 1.5, "PETR_WTI": 1.0, "PETR_BRENT": 1.0, "GAS": 1.5, "PRATA": 0.6, "OURO": 0.4}

# ─────────────────────────────────────────
# BUSCA DE DADOS
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def buscar_dados_mercado():
    dados = {}
    tickers = {k: v["ticker"] for k, v in FATORES.items()}
    for nome, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d", interval="5m")
            if len(hist) >= 2:
                atual    = float(hist["Close"].iloc[-1])
                abertura = float(hist["Close"].iloc[0])
                var_pct  = ((atual - abertura) / abertura) * 100 if abertura != 0 else 0
                dados[nome] = {"atual": round(atual, 4), "var_pct": round(var_pct, 4), "abertura": round(abertura, 4), "ok": True}
            else:
                dados[nome] = {"atual": None, "var_pct": 0, "abertura": None, "ok": False}
        except:
            dados[nome] = {"atual": None, "var_pct": 0, "abertura": None, "ok": False}
    return dados

@st.cache_data(ttl=3600)
def buscar_selic_bcb():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/5?formato=json"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            dados = r.json()
            if dados:
                return float(dados[-1]["valor"])
    except:
        pass
    return None

# ─────────────────────────────────────────
# CLASSIFICAÇÃO DE FATORES
# ─────────────────────────────────────────
def classificar_fator(var_pct, chave):
    direcao = FATORES[chave]["direcao"]
    limiar  = LIMIARES.get(chave, LIMIAR_PADRAO)

    if direcao == "ambiguo":
        # Petróleo e Gás: alta forte = inflação = pessimista
        if var_pct > limiar * 2:   return "pessimista"
        elif var_pct < -limiar * 2: return "otimista"
        return "neutro"

    if abs(var_pct) < limiar:
        return "neutro"

    if direcao == "direto":
        return "otimista" if var_pct > 0 else "pessimista"
    else:  # inverso
        return "pessimista" if var_pct > 0 else "otimista"

# ─────────────────────────────────────────
# DIFERENCIAL DE JUROS
# ─────────────────────────────────────────
def calcular_diferencial_juros(dados, selic):
    resultado = {"diferencial_atual": None, "var_diferencial": None,
                 "curva_us": None, "var_curva_us": None,
                 "spread_2_10": None,
                 "sinal": "neutro", "intensidade": 0, "descricao": "dados insuficientes"}

    t2y  = dados.get("T2Y",  {})
    t10y = dados.get("T10Y", {})
    t5y  = dados.get("T5Y",  {})

    # Curva americana 10y - 2y
    if t2y.get("atual") and t10y.get("atual"):
        spread_atual = t10y["atual"] - t2y["atual"]
        spread_aber  = (t10y.get("abertura", t10y["atual"]) - t2y.get("abertura", t2y["atual"]))
        resultado["curva_us"]     = round(spread_atual, 3)
        resultado["var_curva_us"] = round(spread_atual - spread_aber, 3)
        resultado["spread_2_10"]  = round(spread_atual, 3)

    # Diferencial Brasil x EUA
    if selic and t10y.get("atual"):
        dif = selic - t10y["atual"]
        var_dif = -(t10y["var_pct"] * t10y["atual"] / 100) if t10y.get("atual") else 0
        resultado["diferencial_atual"] = round(dif, 2)
        resultado["var_diferencial"]   = round(var_dif, 4)

    # Montar sinal
    intensidade = 0
    votos = []

    if resultado["var_diferencial"] is not None:
        vd = resultado["var_diferencial"]
        if vd > 0.05:   votos.append("pessimista"); intensidade += 2
        elif vd > 0.02: votos.append("pessimista"); intensidade += 1
        elif vd < -0.05: votos.append("otimista"); intensidade += 2
        elif vd < -0.02: votos.append("otimista"); intensidade += 1

    if resultado["var_curva_us"] is not None:
        vc = resultado["var_curva_us"]
        if vc < -0.04:   votos.append("pessimista"); intensidade += 1
        elif vc > 0.04:  votos.append("otimista");   intensidade += 1

    if t2y.get("var_pct"):
        v2 = t2y["var_pct"]
        if v2 > 0.5:    votos.append("pessimista"); intensidade += 1
        elif v2 < -0.5: votos.append("otimista");   intensidade += 1

    if votos:
        from collections import Counter
        sinal = Counter(votos).most_common(1)[0][0]
        resultado["sinal"]     = sinal
        resultado["intensidade"] = min(intensidade, 5)
        resultado["descricao"] = (
            "dif. fechando / curva achatando → pressão cambial"
            if sinal == "pessimista" else
            "dif. abrindo / curva inclinando → suporte ao real"
        )
    return resultado

# ─────────────────────────────────────────
# CÁLCULO DE SCORES
# ─────────────────────────────────────────
def calcular_scores(dados, di_juros):
    resultado = {}
    for ativo in ["WDO", "WIN"]:
        pess, otim, neu = 0.0, 0.0, 0.0
        peso_key = f"peso_{ativo.lower()}"
        for chave, info in FATORES.items():
            d = dados.get(chave, {})
            if not d.get("ok"):
                continue
            var    = d.get("var_pct", 0)
            peso   = info[peso_key]
            classif = classificar_fator(var, chave)
            if classif == "pessimista":   pess += peso
            elif classif == "otimista":   otim += peso
            else:                         neu  += peso

        # Diferencial de juros como fator extra
        di_peso = 4 if ativo == "WDO" else 2
        intens  = min(di_juros["intensidade"], 3) / 3
        if di_juros["sinal"] == "pessimista":   pess += di_peso * intens
        elif di_juros["sinal"] == "otimista":   otim += di_peso * intens

        total = pess + otim + neu if (pess + otim + neu) > 0 else 1
        resultado[ativo] = {
            "pessimismo": round(pess / total * 10, 2),
            "otimismo":   round(otim / total * 10, 2),
            "neutro":     round(neu  / total * 10, 2),
            "spread":     round((pess - otim) / total * 10, 2),
        }
    return resultado

def gerar_sinal(scores, threshold, ativo):
    s = scores[ativo]["spread"]
    if s > threshold:
        return ("🟢 COMPRA WDO", "#00ff78", "pessimismo domina") if ativo == "WDO" else ("🔴 VENDA WIN", "#ff5050", "pessimismo domina")
    elif s < -threshold:
        return ("🔴 VENDA WDO", "#ff5050", "otimismo domina") if ativo == "WDO" else ("🟢 COMPRA WIN", "#00ff78", "otimismo domina")
    return ("⚪ NEUTRO", "#8888aa", "sem confluência")

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>TENDÊNCIA MACRO</h1>
    <p>Mini Dólar · Mini Índice · 30+ Fatores Globais · Diferencial de Juros</p>
</div>
""", unsafe_allow_html=True)

col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 1])
with col_ctrl1:
    ativo_sel = st.selectbox("Ativo", ["WDO — Mini Dólar", "WIN — Mini Índice"])
    ativo = "WDO" if "WDO" in ativo_sel else "WIN"
with col_ctrl2:
    threshold = st.slider("Threshold do sinal", 0.5, 4.0, 2.0, 0.5)
with col_ctrl3:
    st.markdown("<br>", unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto (5min)", value=False)

st.markdown("<hr style='border-color:#1a1a2a; margin: 0.5rem 0 1rem 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# BUSCAR DADOS
# ─────────────────────────────────────────
with st.spinner("Buscando 30+ fatores globais..."):
    dados  = buscar_dados_mercado()
    selic  = buscar_selic_bcb()
    di_juros = calcular_diferencial_juros(dados, selic)
    scores = calcular_scores(dados, di_juros)
    st.session_state.ultimo_update = datetime.now(BR_TZ).strftime("%H:%M:%S")

    # Rastro = sinal independente do diferencial de juros
    intens = di_juros["intensidade"]
    sinal_di = di_juros["sinal"]
    rastro = intens if sinal_di == "pessimista" else (-intens if sinal_di == "otimista" else 0.0)

    entrada = {
        "hora": datetime.now(BR_TZ).strftime("%H:%M"),
        "data": datetime.now(BR_TZ).strftime("%Y-%m-%d"),
        "pessimismo_wdo": scores["WDO"]["pessimismo"],
        "otimismo_wdo":   scores["WDO"]["otimismo"],
        "neutro_wdo":     scores["WDO"]["neutro"],
        "spread_wdo":     scores["WDO"]["spread"],
        "pessimismo_win": scores["WIN"]["pessimismo"],
        "otimismo_win":   scores["WIN"]["otimismo"],
        "neutro_win":     scores["WIN"]["neutro"],
        "spread_win":     scores["WIN"]["spread"],
        "rastro":         rastro,
    }

    if st.session_state.historico and "rastro" not in st.session_state.historico[0]:
        st.session_state.historico = []
    if not st.session_state.historico or st.session_state.historico[-1]["hora"] != entrada["hora"]:
        st.session_state.historico.append(entrada)
        if len(st.session_state.historico) > 120:
            st.session_state.historico = st.session_state.historico[-120:]
        salvar_historico(st.session_state.historico)

fatores_ok  = sum(1 for d in dados.values() if d.get("ok"))
fatores_tot = len(FATORES)

# ─────────────────────────────────────────
# DIFERENCIAL DE JUROS
# ─────────────────────────────────────────
st.markdown("""<div class="section-title">● DIFERENCIAL DE JUROS — BRASIL x EUA (GATILHO AUTOMÁTICO)</div>""", unsafe_allow_html=True)

cor_di   = "#00ff78" if di_juros["sinal"] == "pessimista" else ("#ff5050" if di_juros["sinal"] == "otimista" else "#8888aa")
selic_s  = f"{selic:.2f}%" if selic else "—"
t2y_v    = dados.get("T2Y",  {}).get("atual")
t10y_v   = dados.get("T10Y", {}).get("atual")
t10y_var = dados.get("T10Y", {}).get("var_pct", 0)
t2y_var  = dados.get("T2Y",  {}).get("var_pct", 0)

col_j = st.columns(5)
juros_cards = [
    ("Selic (BCB)", selic_s, "taxa anual", 0),
    ("Treasury 2a", f"{t2y_v:.2f}%" if t2y_v else "—", f"{t2y_var:+.2f}% no dia", t2y_var),
    ("Treasury 10a", f"{t10y_v:.2f}%" if t10y_v else "—", f"{t10y_var:+.2f}% no dia", t10y_var),
    ("Diferencial BR-EUA", f"{di_juros['diferencial_atual']:+.2f}pp" if di_juros['diferencial_atual'] else "—",
     f"var: {di_juros['var_diferencial']:+.4f}" if di_juros['var_diferencial'] else "—", di_juros.get('var_diferencial', 0) or 0),
    ("Curva EUA 10y-2y", f"{di_juros['curva_us']:+.3f}pp" if di_juros['curva_us'] else "—",
     "achatamento = pessimista", di_juros.get('var_curva_us', 0) or 0),
]
for i, (label, val, sub, var) in enumerate(juros_cards):
    cor = "#ff5050" if var > 0.02 else ("#00ff78" if var < -0.02 else "#8888aa")
    with col_j[i]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{cor}">{val}</div>
            <div style="font-size:0.6rem;color:#333355;font-family:'JetBrains Mono'">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:#0d0d1a;border:1px solid {cor_di}33;border-left:3px solid {cor_di};border-radius:6px;padding:0.7rem 1.2rem;margin-bottom:1rem;font-family:'JetBrains Mono',monospace;">
    <span style="font-size:0.6rem;color:#444466;letter-spacing:0.2em;text-transform:uppercase">SINAL AUTOMÁTICO DO DIFERENCIAL</span><br>
    <span style="color:{cor_di};font-size:0.9rem;font-weight:700">{di_juros['sinal'].upper()}</span>
    <span style="color:#555577;font-size:0.75rem;margin-left:1rem">{di_juros['descricao']}</span>
    <span style="color:#333355;font-size:0.65rem;margin-left:1rem">intensidade: {di_juros['intensidade']}/5</span>
    <span style="color:#222244;font-size:0.6rem;float:right">{fatores_ok}/{fatores_tot} fatores ativos · BRT {st.session_state.ultimo_update}</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1a1a2a; margin: 0.5rem 0 1rem 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SINAIS PRINCIPAIS
# ─────────────────────────────────────────
sinal_wdo, cor_wdo, desc_wdo = gerar_sinal(scores, threshold, "WDO")
sinal_win, cor_win, desc_win = gerar_sinal(scores, threshold, "WIN")
spread_val = scores[ativo]["spread"]
cor_sp = "#00ff78" if spread_val > 0 else ("#ff5050" if spread_val < 0 else "#8888aa")
brl_var = dados.get("BRL", {}).get("var_pct", 0)
cor_brl = "#00ff78" if brl_var > 0 else ("#ff5050" if brl_var < 0 else "#8888aa")

col_s = st.columns(4)
with col_s[0]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Sinal WDO</div>
        <div class="metric-value" style="color:{cor_wdo};font-size:1rem">{sinal_wdo}</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">{desc_wdo}</div>
    </div>""", unsafe_allow_html=True)
with col_s[1]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Sinal WIN</div>
        <div class="metric-value" style="color:{cor_win};font-size:1rem">{sinal_win}</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">{desc_win}</div>
    </div>""", unsafe_allow_html=True)
with col_s[2]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Spread {ativo}</div>
        <div class="metric-value" style="color:{cor_sp}">{spread_val:+.2f}</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">threshold: ±{threshold}</div>
    </div>""", unsafe_allow_html=True)
with col_s[3]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">USD/BRL variação</div>
        <div class="metric-value" style="color:{cor_brl}">{brl_var:+.2f}%</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">hoje vs. abertura</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# GRÁFICO
# ─────────────────────────────────────────
st.markdown(f"""<div class="section-title">● GRÁFICO — {ativo_sel.upper()}</div>""", unsafe_allow_html=True)

if len(st.session_state.historico) >= 2:
    df   = pd.DataFrame(st.session_state.historico)
    horas = df["hora"].tolist()
    suf  = ativo.lower()
    fig  = go.Figure()

    fig.add_hrect(y0=threshold, y1=10, fillcolor="rgba(0,255,120,0.03)", line_width=0)
    fig.add_hrect(y0=-10, y1=-threshold, fillcolor="rgba(255,80,80,0.03)", line_width=0)
    fig.add_hline(y=threshold,  line_dash="dot", line_color="rgba(255,200,0,0.3)", line_width=1)
    fig.add_hline(y=-threshold, line_dash="dot", line_color="rgba(255,200,0,0.3)", line_width=1)
    fig.add_hline(y=0, line_color="rgba(100,100,140,0.4)", line_width=1)

    fig.add_trace(go.Scatter(x=horas, y=df[f"pessimismo_{suf}"], name="Pessimismo", mode="lines",
        line=dict(color="#00ff78", width=2.5), fill="tozeroy", fillcolor="rgba(0,255,120,0.04)"))
    fig.add_trace(go.Scatter(x=horas, y=[-v for v in df[f"otimismo_{suf}"]], name="Otimismo", mode="lines",
        line=dict(color="#ff5050", width=2.5), fill="tozeroy", fillcolor="rgba(255,80,80,0.04)"))
    fig.add_trace(go.Scatter(x=horas, y=df[f"neutro_{suf}"], name="Neutro", mode="lines",
        line=dict(color="#555577", width=1, dash="dot")))

    rastro_vals = df["rastro"].tolist() if "rastro" in df.columns else [0]*len(horas)
    simbolos = ["triangle-up" if v > 0 else ("triangle-down" if v < 0 else "circle") for v in rastro_vals]
    fig.add_trace(go.Scatter(x=horas, y=rastro_vals, name="Rastro do Macro (Juros)", mode="lines+markers",
        line=dict(color="#4488ff", width=2.5),
        marker=dict(size=6, color="#4488ff", symbol=simbolos)))

    fig.update_layout(
        paper_bgcolor="#0a0a0f", plot_bgcolor="#0d0d18",
        font=dict(family="JetBrains Mono", color="#555577", size=11),
        height=380, margin=dict(l=10, r=10, t=20, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9)),
        yaxis=dict(showgrid=True, gridcolor="#111122", zeroline=False, tickfont=dict(size=9), range=[-11, 11]),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;margin-top:-0.5rem">
        <span style="font-size:0.65rem;color:#222244;font-family:'JetBrains Mono'">
            Verde acima = pessimismo → {'COMPRA WDO' if ativo=='WDO' else 'VENDA WIN'} &nbsp;|&nbsp;
            Vermelho abaixo = otimismo → {'VENDA WDO' if ativo=='WDO' else 'COMPRA WIN'} &nbsp;|&nbsp;
            Azul = rastro do diferencial de juros
        </span>
        <span class="timestamp">BRT {st.session_state.ultimo_update}</span>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div style="text-align:center;padding:3rem;color:#333355;font-family:'JetBrains Mono';font-size:0.8rem">
        AGUARDANDO DADOS...<br><span style="font-size:0.65rem">O gráfico será construído nas próximas leituras automáticas</span>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TABELA DE FATORES POR GRUPO
# ─────────────────────────────────────────
st.markdown("""<div class="section-title">● FATORES DE MERCADO — VARIAÇÃO NO DIA</div>""", unsafe_allow_html=True)

grupos = {}
for chave, info in FATORES.items():
    g = info["grupo"]
    if g not in grupos:
        grupos[g] = []
    grupos[g].append(chave)

for grupo, chaves in grupos.items():
    st.markdown(f'<div class="grupo-title">{grupo}</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, chave in enumerate(chaves):
        info = FATORES[chave]
        d    = dados.get(chave, {})
        var  = d.get("var_pct", 0)
        ok   = d.get("ok", False)
        classif = classificar_fator(var, chave) if ok else "—"
        cor_var = "#00ff78" if var > 0 else ("#ff5050" if var < 0 else "#555577")
        cor_cl  = "#00ff78" if classif == "otimista" else ("#ff5050" if classif == "pessimista" else "#555577")
        seta    = "▲" if var > 0 else ("▼" if var < 0 else "—")
        val_str = f"{seta} {var:+.2f}%" if ok else "sem dados"

        with cols[i % 3]:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-label">{info['nome']}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.3rem">
                    <span style="font-family:'JetBrains Mono';font-size:1rem;color:{cor_var};font-weight:600">{val_str}</span>
                    <span style="font-size:0.65rem;color:{cor_cl};font-family:'JetBrains Mono'">{classif.upper()}</span>
                </div>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# RODAPÉ
# ─────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:1rem 0;border-top:1px solid #1a1a2a;margin-top:1rem">
    <span style="font-family:'JetBrains Mono';font-size:0.6rem;color:#222244;letter-spacing:0.2em">
        {fatores_ok}/{fatores_tot} FATORES ATIVOS · YAHOO FINANCE (~15MIN DELAY) · SELIC: BCB · HORÁRIO: BRT · NÃO CONSTITUI RECOMENDAÇÃO DE INVESTIMENTO
    </span>
</div>
""", unsafe_allow_html=True)

if auto_refresh:
    time_module.sleep(300)
    st.rerun()
