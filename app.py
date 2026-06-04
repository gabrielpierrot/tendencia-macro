import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, time
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

.juros-card { background: #0d0d1a; border: 1px solid #2a2a4a; border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1rem; }
.juros-valor { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; }
.juros-label { font-size: 0.6rem; color: #444466; letter-spacing: 0.2em; text-transform: uppercase; font-family: 'JetBrains Mono', monospace; }
.juros-desc { font-size: 0.7rem; color: #555577; margin-top: 0.3rem; font-family: 'JetBrains Mono', monospace; }

.stButton button { background: #1a1a2e !important; color: #aaaacc !important; border: 1px solid #2a2a4a !important; border-radius: 6px !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.75rem !important; letter-spacing: 0.1em !important; }
.stButton button:hover { background: #2a2a4e !important; border-color: #4a4a8a !important; color: #ffffff !important; }

div[data-testid="stSelectbox"] label, div[data-testid="stSlider"] label { color: #555577 !important; font-size: 0.7rem !important; letter-spacing: 0.15em !important; text-transform: uppercase !important; font-family: 'JetBrains Mono', monospace !important; }

.timestamp { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #333355; text-align: right; }
.signal-chip { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.7rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.1em; }
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

# ─────────────────────────────────────────
# ESTADO
# ─────────────────────────────────────────
if "historico" not in st.session_state:
    st.session_state.historico = carregar_historico()
if "ultimo_update" not in st.session_state:
    st.session_state.ultimo_update = None


# ─────────────────────────────────────────
# BUSCA DE DADOS
# ─────────────────────────────────────────
@st.cache_data(ttl=300)
def buscar_dados_mercado():
    tickers = {
        "DXY":       "DX-Y.NYB",
        "VIX":       "^VIX",
        "SP500":     "ES=F",
        "PETROLEO":  "CL=F",
        "MINERIO":   "VALE3.SA",
        "BRL":       "BRL=X",
        "OURO":      "GC=F",
        "COBRE":     "HG=F",
        "IBOV":      "^BVSP",
        "NASDAQ":    "NQ=F",
        "T2Y":       "^IRX",   # Treasury 2 anos
        "T10Y":      "^TNX",   # Treasury 10 anos
        "T30Y":      "^TYX",   # Treasury 30 anos
    }
    dados = {}
    for nome, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="5d", interval="5m")
            if len(hist) >= 2:
                atual = float(hist["Close"].iloc[-1])
                abertura = float(hist["Close"].iloc[0])
                var_pct = ((atual - abertura) / abertura) * 100 if abertura != 0 else 0
                dados[nome] = {"atual": round(atual, 4), "var_pct": round(var_pct, 4), "abertura": round(abertura, 4)}
            else:
                dados[nome] = {"atual": None, "var_pct": 0, "abertura": None}
        except:
            dados[nome] = {"atual": None, "var_pct": 0, "abertura": None}
    return dados


@st.cache_data(ttl=3600)
def buscar_selic_bcb():
    """Taxa Selic via API do Banco Central"""
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
# LÓGICA DO DIFERENCIAL DE JUROS
# ─────────────────────────────────────────
def calcular_diferencial_juros(dados, selic):
    """
    Calcula o diferencial Brasil x EUA e a inclinação da curva americana.
    Retorna sinal, intensidade e descrição.
    """
    resultado = {
        "diferencial_atual": None,
        "var_diferencial": None,
        "curva_us": None,          # spread 10y - 2y
        "var_curva_us": None,
        "sinal": "neutro",
        "intensidade": 0,
        "descricao": "dados insuficientes",
    }

    t2y = dados.get("T2Y", {})
    t10y = dados.get("T10Y", {})

    # Curva americana: spread 10y - 2y
    if t2y.get("atual") and t10y.get("atual"):
        spread_us_atual = t10y["atual"] - t2y["atual"]
        spread_us_aber  = t10y["abertura"] - t2y["abertura"]
        var_curva = spread_us_atual - spread_us_aber
        resultado["curva_us"] = round(spread_us_atual, 3)
        resultado["var_curva_us"] = round(var_curva, 3)

    # Diferencial Brasil - EUA (usando Selic vs T10Y como proxy)
    if selic and t10y.get("atual"):
        # Selic é anual %; T10Y também é % anual
        dif_atual = selic - t10y["atual"]
        # Variação do diferencial no dia: Selic não muda intraday,
        # então a variação vem da mudança no Treasury
        dif_var = -(t10y["var_pct"] * t10y["atual"] / 100) if t10y.get("atual") else 0
        resultado["diferencial_atual"] = round(dif_atual, 2)
        resultado["var_diferencial"]   = round(dif_var, 4)

    # ── Sinal do diferencial ──
    # Diferencial abrindo (T10Y cai = spread BR-EUA cresce) → real aprecia → pessimista WDO
    # Diferencial fechando (T10Y sobe = spread BR-EUA encolhe) → real deprecia → otimista WDO
    intensidade = 0
    sinais = []

    if resultado["var_diferencial"] is not None:
        vd = resultado["var_diferencial"]
        if vd > 0.05:
            sinais.append("pessimista")
            intensidade += 2
        elif vd > 0.02:
            sinais.append("pessimista")
            intensidade += 1
        elif vd < -0.05:
            sinais.append("otimista")
            intensidade += 2
        elif vd < -0.02:
            sinais.append("otimista")
            intensidade += 1

    # Curva americana achatando = risco de recessão = pessimista para ativos de risco
    if resultado["var_curva_us"] is not None:
        vc = resultado["var_curva_us"]
        if vc < -0.03:
            sinais.append("pessimista")
            intensidade += 1
        elif vc > 0.03:
            sinais.append("otimista")
            intensidade += 1

    # Treasury 2y subindo forte = aperto monetário = pessimista global
    if t2y.get("var_pct"):
        if t2y["var_pct"] > 0.5:
            sinais.append("pessimista")
            intensidade += 1
        elif t2y["var_pct"] < -0.5:
            sinais.append("otimista")
            intensidade += 1

    if sinais:
        from collections import Counter
        mais_comum = Counter(sinais).most_common(1)[0][0]
        resultado["sinal"] = mais_comum
        resultado["intensidade"] = min(intensidade, 5)

        if mais_comum == "pessimista":
            resultado["descricao"] = "diferencial fechando / curva achatando → pressão no WDO / WIN"
        else:
            resultado["descricao"] = "diferencial abrindo / curva inclinando → suporte ao real"
    else:
        resultado["sinal"] = "neutro"
        resultado["descricao"] = "curva de juros sem sinal direcional claro"

    return resultado


# ─────────────────────────────────────────
# CLASSIFICAÇÃO DOS FATORES
# ─────────────────────────────────────────
def classificar_fator(var_pct, fator):
    limiares = {
        "DXY": 0.2, "VIX": 1.0, "SP500": 0.3, "NASDAQ": 0.3,
        "PETROLEO": 0.8, "MINERIO": 0.5, "BRL": 0.2,
        "OURO": 0.4, "COBRE": 0.5, "IBOV": 0.3,
        "T2Y": 0.3, "T10Y": 0.3,
    }
    limiar = limiares.get(fator, 0.3)

    # Fatores onde alta = pessimismo para BR
    pessimistas_na_alta = {"DXY", "VIX", "BRL", "T2Y", "T10Y"}
    # Fatores onde alta = otimismo para BR
    otimistas_na_alta   = {"SP500", "NASDAQ", "MINERIO", "IBOV", "COBRE"}
    # Petróleo: ambíguo
    # Ouro: alta = aversão a risco = pessimista

    if fator in pessimistas_na_alta:
        if var_pct > limiar: return "pessimista"
        elif var_pct < -limiar: return "otimista"
    elif fator in otimistas_na_alta:
        if var_pct > limiar: return "otimista"
        elif var_pct < -limiar: return "pessimista"
    elif fator == "OURO":
        if var_pct > limiar: return "pessimista"
        elif var_pct < -limiar: return "otimista"
    elif fator == "PETROLEO":
        if var_pct > 1.5: return "pessimista"
        elif var_pct < -1.5: return "otimista"
    return "neutro"


# ─────────────────────────────────────────
# CÁLCULO DE SCORES
# ─────────────────────────────────────────
def calcular_scores(dados, di_juros):
    """
    Pesos por ativo. O diferencial de juros entra com peso alto no WDO.
    """
    pesos_wdo = {
        "DXY": 3, "VIX": 2, "SP500": 2, "NASDAQ": 1,
        "PETROLEO": 1, "MINERIO": 1, "BRL": 2,
        "OURO": 1, "COBRE": 1, "IBOV": 1,
        "T2Y": 2, "T10Y": 2,
    }
    pesos_win = {
        "DXY": 1, "VIX": 2, "SP500": 3, "NASDAQ": 2,
        "PETROLEO": 1, "MINERIO": 2, "BRL": 1,
        "OURO": 1, "COBRE": 2, "IBOV": 3,
        "T2Y": 1, "T10Y": 2,
    }

    resultado = {}
    for ativo, pesos in [("WDO", pesos_wdo), ("WIN", pesos_win)]:
        pess, otim, neu = 0, 0, 0
        for fator, peso in pesos.items():
            if fator not in dados:
                continue
            var = dados[fator].get("var_pct", 0)
            classif = classificar_fator(var, fator)
            if classif == "pessimista":   pess += peso
            elif classif == "otimista":   otim += peso
            else:                         neu  += peso

        # Diferencial de juros — peso maior no WDO
        di_peso = 4 if ativo == "WDO" else 2
        if di_juros["sinal"] == "pessimista":
            pess += di_peso * min(di_juros["intensidade"], 3) / 3
        elif di_juros["sinal"] == "otimista":
            otim += di_peso * min(di_juros["intensidade"], 3) / 3

        total = pess + otim + neu if (pess + otim + neu) > 0 else 1
        resultado[ativo] = {
            "pessimismo": round(pess / total * 10, 2),
            "otimismo":   round(otim / total * 10, 2),
            "neutro":     round(neu  / total * 10, 2),
            "spread":     round((pess - otim) / total * 10, 2),
        }
    return resultado


def gerar_sinal(scores, threshold, ativo):
    spread = scores[ativo]["spread"]
    if spread > threshold:
        return ("🟢 COMPRA WDO", "#00ff78", "pessimismo domina") if ativo == "WDO" else ("🔴 VENDA WIN", "#ff5050", "pessimismo domina")
    elif spread < -threshold:
        return ("🔴 VENDA WDO", "#ff5050", "otimismo domina") if ativo == "WDO" else ("🟢 COMPRA WIN", "#00ff78", "otimismo domina")
    return ("⚪ NEUTRO", "#8888aa", "sem confluência")


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>TENDÊNCIA MACRO</h1>
    <p>Mini Dólar · Mini Índice · Diferencial de Juros · Tempo Real</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONTROLES
# ─────────────────────────────────────────
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
with st.spinner("Atualizando dados de mercado..."):
    dados = buscar_dados_mercado()
    selic = buscar_selic_bcb()
    di_juros = calcular_diferencial_juros(dados, selic)
    scores = calcular_scores(dados, di_juros)
    st.session_state.ultimo_update = datetime.now(BR_TZ).strftime("%H:%M:%S")

    # Rastro do Macro = sinal independente baseado no diferencial de juros
    # Normalizado: intensidade (-5 a +5) com sinal do diferencial
    di_intensidade = di_juros["intensidade"]  # 0-5
    di_sinal = di_juros["sinal"]
    if di_sinal == "pessimista":
        rastro = di_intensidade          # positivo = pessimismo domina = compra WDO
    elif di_sinal == "otimista":
        rastro = -di_intensidade         # negativo = otimismo domina = venda WDO
    else:
        rastro = 0.0

    entrada = {
        "hora":           datetime.now(BR_TZ).strftime("%H:%M"),
        "data":           datetime.now(BR_TZ).strftime("%Y-%m-%d"),
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

    # Limpa histórico se formato antigo (sem coluna rastro)
    if st.session_state.historico and "rastro" not in st.session_state.historico[0]:
        st.session_state.historico = []

    if not st.session_state.historico or st.session_state.historico[-1]["hora"] != entrada["hora"]:
        st.session_state.historico.append(entrada)
        if len(st.session_state.historico) > 120:
            st.session_state.historico = st.session_state.historico[-120:]
        salvar_historico(st.session_state.historico)

# ─────────────────────────────────────────
# BLOCO DE DIFERENCIAL DE JUROS
# ─────────────────────────────────────────
st.markdown("""<div class="section-title">● DIFERENCIAL DE JUROS — BRASIL x EUA (GATILHO AUTOMÁTICO)</div>""", unsafe_allow_html=True)

cor_di = "#00ff78" if di_juros["sinal"] == "pessimista" else ("#ff5050" if di_juros["sinal"] == "otimista" else "#8888aa")
selic_str  = f"{selic:.2f}%" if selic else "—"
t10y_atual = dados.get("T10Y", {}).get("atual")
t2y_atual  = dados.get("T2Y",  {}).get("atual")
t10y_str   = f"{t10y_atual:.2f}%" if t10y_atual else "—"
t2y_str    = f"{t2y_atual:.2f}%"  if t2y_atual  else "—"
dif_str    = f"{di_juros['diferencial_atual']:+.2f}pp" if di_juros["diferencial_atual"] is not None else "—"
curva_str  = f"{di_juros['curva_us']:+.3f}pp" if di_juros["curva_us"] is not None else "—"
var_dif_str = f"{di_juros['var_diferencial']:+.4f}" if di_juros["var_diferencial"] is not None else "—"

col_j1, col_j2, col_j3, col_j4, col_j5 = st.columns(5)

with col_j1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Selic (BCB)</div>
        <div class="metric-value">{selic_str}</div>
        <div style="font-size:0.6rem;color:#333355;font-family:'JetBrains Mono'">taxa anual</div>
    </div>""", unsafe_allow_html=True)

with col_j2:
    t2y_var = dados.get("T2Y", {}).get("var_pct", 0)
    cor_t2y = "#ff5050" if t2y_var > 0.3 else ("#00ff78" if t2y_var < -0.3 else "#8888aa")
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Treasury 2 anos</div>
        <div class="metric-value" style="color:{cor_t2y}">{t2y_str}</div>
        <div style="font-size:0.6rem;color:#333355;font-family:'JetBrains Mono'">{t2y_var:+.2f}% no dia</div>
    </div>""", unsafe_allow_html=True)

with col_j3:
    t10y_var = dados.get("T10Y", {}).get("var_pct", 0)
    cor_t10y = "#ff5050" if t10y_var > 0.3 else ("#00ff78" if t10y_var < -0.3 else "#8888aa")
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Treasury 10 anos</div>
        <div class="metric-value" style="color:{cor_t10y}">{t10y_str}</div>
        <div style="font-size:0.6rem;color:#333355;font-family:'JetBrains Mono'">{t10y_var:+.2f}% no dia</div>
    </div>""", unsafe_allow_html=True)

with col_j4:
    cor_dif = "#00ff78" if di_juros.get("var_diferencial", 0) and di_juros["var_diferencial"] > 0 else ("#ff5050" if di_juros.get("var_diferencial", 0) and di_juros["var_diferencial"] < 0 else "#8888aa")
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Diferencial BR-EUA</div>
        <div class="metric-value" style="color:{cor_dif}">{dif_str}</div>
        <div style="font-size:0.6rem;color:#333355;font-family:'JetBrains Mono'">var. dia: {var_dif_str}</div>
    </div>""", unsafe_allow_html=True)

with col_j5:
    cor_curva = "#00ff78" if di_juros.get("var_curva_us", 0) and di_juros["var_curva_us"] > 0 else ("#ff5050" if di_juros.get("var_curva_us", 0) and di_juros["var_curva_us"] < 0 else "#8888aa")
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Curva EUA (10y-2y)</div>
        <div class="metric-value" style="color:{cor_curva}">{curva_str}</div>
        <div style="font-size:0.6rem;color:#333355;font-family:'JetBrains Mono'">achatamento = pessimista</div>
    </div>""", unsafe_allow_html=True)

# Sinal do diferencial
st.markdown(f"""
<div style="background:#0d0d1a; border:1px solid {cor_di}33; border-left: 3px solid {cor_di}; border-radius:6px; padding:0.7rem 1.2rem; margin-bottom:1rem; font-family:'JetBrains Mono', monospace;">
    <span style="font-size:0.6rem; color:#444466; letter-spacing:0.2em; text-transform:uppercase">SINAL AUTOMÁTICO DO DIFERENCIAL</span><br>
    <span style="color:{cor_di}; font-size:0.9rem; font-weight:700">{di_juros['sinal'].upper()}</span>
    <span style="color:#555577; font-size:0.75rem; margin-left:1rem">{di_juros['descricao']}</span>
    <span style="color:#333355; font-size:0.65rem; margin-left:1rem">intensidade: {di_juros['intensidade']}/5</span>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1a1a2a; margin: 0.5rem 0 1rem 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SINAIS PRINCIPAIS
# ─────────────────────────────────────────
sinal_wdo, cor_wdo, desc_wdo = gerar_sinal(scores, threshold, "WDO")
sinal_win, cor_win, desc_win = gerar_sinal(scores, threshold, "WIN")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)
with col_s1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Sinal WDO</div>
        <div class="metric-value" style="color:{cor_wdo};font-size:1rem">{sinal_wdo}</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">{desc_wdo}</div>
    </div>""", unsafe_allow_html=True)

with col_s2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Sinal WIN</div>
        <div class="metric-value" style="color:{cor_win};font-size:1rem">{sinal_win}</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">{desc_win}</div>
    </div>""", unsafe_allow_html=True)

with col_s3:
    spread_val = scores[ativo]["spread"]
    cor_sp = "#00ff78" if spread_val > 0 else ("#ff5050" if spread_val < 0 else "#8888aa")
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Spread {ativo}</div>
        <div class="metric-value" style="color:{cor_sp}">{spread_val:+.2f}</div>
        <div style="font-size:0.65rem;color:#444466;margin-top:0.2rem;font-family:'JetBrains Mono'">threshold: ±{threshold}</div>
    </div>""", unsafe_allow_html=True)

with col_s4:
    brl_var = dados.get("BRL", {}).get("var_pct", 0)
    cor_brl = "#00ff78" if brl_var > 0 else ("#ff5050" if brl_var < 0 else "#8888aa")
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
    df = pd.DataFrame(st.session_state.historico)
    horas = df["hora"].tolist()
    suf = ativo.lower()

    fig = go.Figure()
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
    # Rastro do Macro: sinal independente do diferencial de juros
    rastro_vals = df["rastro"].tolist() if "rastro" in df.columns else [0]*len(horas)
    fig.add_trace(go.Scatter(x=horas, y=rastro_vals, name="Rastro do Macro (Juros)", mode="lines+markers",
        line=dict(color="#4488ff", width=2.5), marker=dict(size=6, color="#4488ff",
        symbol=["triangle-up" if v > 0 else ("triangle-down" if v < 0 else "circle") for v in rastro_vals])))

    fig.update_layout(
        paper_bgcolor="#0a0a0f", plot_bgcolor="#0d0d18",
        font=dict(family="JetBrains Mono", color="#555577", size=11),
        height=380, margin=dict(l=10, r=10, t=20, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9), linecolor="#1e1e2e"),
        yaxis=dict(showgrid=True, gridcolor="#111122", zeroline=False, tickfont=dict(size=9), range=[-11, 11]),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; margin-top:-0.5rem">
        <span style="font-size:0.65rem;color:#222244;font-family:'JetBrains Mono'">
            Verde acima = pessimismo → {'COMPRA WDO' if ativo=='WDO' else 'VENDA WIN'} &nbsp;|&nbsp;
            Vermelho abaixo = otimismo → {'VENDA WDO' if ativo=='WDO' else 'COMPRA WIN'} &nbsp;|&nbsp;
            Azul cruza threshold = sinal ativo
        </span>
        <span class="timestamp">BRT {st.session_state.ultimo_update}</span>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div style="text-align:center;padding:3rem;color:#333355;font-family:'JetBrains Mono';font-size:0.8rem">
        AGUARDANDO DADOS...<br><span style="font-size:0.65rem">O gráfico será construído nas próximas leituras</span>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# FATORES DE MERCADO
# ─────────────────────────────────────────
st.markdown("""<div class="section-title">● FATORES DE MERCADO — VARIAÇÃO NO DIA</div>""", unsafe_allow_html=True)

fatores_info = {
    "DXY":     ("DXY — Índice do Dólar",     "↑ pessimista"),
    "VIX":     ("VIX — Volatilidade S&P",    "↑ pessimista"),
    "SP500":   ("S&P 500 Futuros",            "↑ otimista"),
    "NASDAQ":  ("Nasdaq Futuros",             "↑ otimista"),
    "IBOV":    ("Ibovespa",                   "↑ otimista"),
    "PETROLEO":("Petróleo WTI",               "ambíguo"),
    "MINERIO": ("VALE3 (proxy minério)",      "↑ otimista"),
    "OURO":    ("Ouro",                       "↑ pessimista (risco)"),
    "COBRE":   ("Cobre (proxy crescimento)",  "↑ otimista"),
    "BRL":     ("USD/BRL",                    "↑ pessimista"),
    "T2Y":     ("Treasury 2 anos",            "↑ pessimista"),
    "T10Y":    ("Treasury 10 anos",           "↑ aperto global"),
}

cols = st.columns(3)
for i, (chave, (nome, desc)) in enumerate(fatores_info.items()):
    d = dados.get(chave, {})
    var = d.get("var_pct", 0)
    classif = classificar_fator(var, chave)
    cor = "#00ff78" if classif == "otimista" else ("#ff5050" if classif == "pessimista" else "#555577")
    seta = "▲" if var > 0 else ("▼" if var < 0 else "—")
    with cols[i % 3]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">{nome}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.3rem">
                <span style="font-family:'JetBrains Mono';font-size:1rem;color:{cor};font-weight:600">{seta} {var:+.2f}%</span>
                <span style="font-size:0.65rem;color:{cor};font-family:'JetBrains Mono'">{classif.upper()}</span>
            </div>
            <div style="font-size:0.6rem;color:#333355;margin-top:0.15rem;font-family:'JetBrains Mono'">{desc}</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# RODAPÉ
# ─────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:1rem 0;border-top:1px solid #1a1a2a;margin-top:1rem">
    <span style="font-family:'JetBrains Mono';font-size:0.6rem;color:#222244;letter-spacing:0.2em">
        DADOS: YAHOO FINANCE (~15MIN DELAY) · SELIC: BCB · HORÁRIO: BRT · NÃO CONSTITUI RECOMENDAÇÃO DE INVESTIMENTO
    </span>
</div>
""", unsafe_allow_html=True)

if auto_refresh:
    time_module.sleep(300)
    st.rerun()
