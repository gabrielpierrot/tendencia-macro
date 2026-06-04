import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, time
import time as time_module
import yfinance as yf
import requests

st.set_page_config(
    page_title="Rastreador Macro | WDO & WIN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

* { box-sizing: border-box; }

.stApp {
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'Inter', sans-serif;
}

.main-header {
    text-align: center;
    padding: 1.5rem 0 0.5rem 0;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 1.5rem;
}

.main-header h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.1em;
    margin: 0;
}

.main-header p {
    color: #555577;
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    margin: 0.3rem 0 0 0;
    text-transform: uppercase;
}

.signal-box {
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid;
    font-family: 'JetBrains Mono', monospace;
}

.signal-compra-wdo {
    background: rgba(0, 255, 120, 0.06);
    border-color: rgba(0, 255, 120, 0.3);
}

.signal-venda-wdo {
    background: rgba(255, 80, 80, 0.06);
    border-color: rgba(255, 80, 80, 0.3);
}

.signal-neutro {
    background: rgba(120, 120, 160, 0.06);
    border-color: rgba(120, 120, 160, 0.3);
}

.signal-label {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #555577;
    margin-bottom: 0.3rem;
}

.signal-value {
    font-size: 1.3rem;
    font-weight: 700;
    letter-spacing: 0.05em;
}

.metric-card {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-family: 'JetBrains Mono', monospace;
}

.metric-label {
    font-size: 0.6rem;
    color: #444466;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}

.metric-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: #ffffff;
    margin-top: 0.2rem;
}

.metric-delta-pos { color: #00cc66; }
.metric-delta-neg { color: #ff4444; }
.metric-delta-neu { color: #888899; }

.factor-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #12121e;
    font-size: 0.85rem;
}

.di-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.1em;
}

.di-sobe { background: rgba(0,255,120,0.15); color: #00ff78; border: 1px solid rgba(0,255,120,0.3); }
.di-cai  { background: rgba(255,80,80,0.15);  color: #ff5050; border: 1px solid rgba(255,80,80,0.3); }
.di-neu  { background: rgba(120,120,160,0.15); color: #8888aa; border: 1px solid rgba(120,120,160,0.3); }

.stButton button {
    background: #1a1a2e !important;
    color: #aaaacc !important;
    border: 1px solid #2a2a4a !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    transition: all 0.2s !important;
}

.stButton button:hover {
    background: #2a2a4e !important;
    border-color: #4a4a8a !important;
    color: #ffffff !important;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label {
    color: #555577 !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}

.timestamp {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #333355;
    text-align: right;
}

.section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #444466;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #1a1a2a;
}

.di-manual-area {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

.alert-threshold {
    background: rgba(255, 200, 0, 0.05);
    border: 1px solid rgba(255, 200, 0, 0.2);
    border-radius: 6px;
    padding: 0.6rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #ccaa00;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# ESTADO DA SESSÃO
# ─────────────────────────────────────────
if "historico" not in st.session_state:
    st.session_state.historico = []
if "di_estado" not in st.session_state:
    st.session_state.di_estado = "neutro"
if "ultimo_update" not in st.session_state:
    st.session_state.ultimo_update = None


# ─────────────────────────────────────────
# FUNÇÕES DE DADOS
# ─────────────────────────────────────────
@st.cache_data(ttl=60)
def buscar_dados_mercado():
    tickers = {
        "DXY":  "DX-Y.NYB",
        "VIX":  "^VIX",
        "SP500": "ES=F",
        "PETROLEO": "CL=F",
        "MINERIO": "VALE3.SA",
        "BRL":  "BRL=X",
    }
    dados = {}
    for nome, ticker in tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d", interval="1m")
            if len(hist) >= 2:
                atual = hist["Close"].iloc[-1]
                abertura = hist["Close"].iloc[0]
                var_pct = ((atual - abertura) / abertura) * 100
                dados[nome] = {"atual": atual, "var_pct": var_pct}
            else:
                dados[nome] = {"atual": None, "var_pct": 0}
        except:
            dados[nome] = {"atual": None, "var_pct": 0}
    return dados


@st.cache_data(ttl=300)
def buscar_di_bcb():
    """Tenta buscar taxa Selic/DI via API do BCB como proxy"""
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/2?formato=json"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            dados = r.json()
            if len(dados) >= 2:
                atual = float(dados[-1]["valor"])
                anterior = float(dados[-2]["valor"])
                return {"atual": atual, "anterior": anterior, "var": atual - anterior}
    except:
        pass
    return None


def classificar_fator(var_pct, fator):
    """Classifica cada fator como pessimista, neutro ou otimista para o mercado BR"""
    limiar = 0.3

    # Fatores que sobem = pessimismo (dólar sobe, risco aumenta)
    fatores_inversos = ["DXY", "VIX", "PETROLEO_NEG"]
    # Fatores que sobem = otimismo
    fatores_diretos = ["SP500", "MINERIO", "BRL_INV"]

    if fator in ["DXY", "VIX"]:
        # Sobe = pessimismo
        if var_pct > limiar: return "pessimista"
        elif var_pct < -limiar: return "otimista"
        else: return "neutro"
    elif fator in ["SP500", "MINERIO"]:
        # Sobe = otimismo
        if var_pct > limiar: return "otimista"
        elif var_pct < -limiar: return "pessimista"
        else: return "neutro"
    elif fator == "PETROLEO":
        # Ambíguo: sobe = inflação (ruim para BR) mas também crescimento
        if var_pct > 1.0: return "pessimista"
        elif var_pct < -1.0: return "otimista"
        else: return "neutro"
    elif fator == "BRL":
        # BRL=X é USD/BRL: sobe = dólar subiu = pessimismo
        if var_pct > limiar: return "pessimista"
        elif var_pct < -limiar: return "otimista"
        else: return "neutro"
    return "neutro"


def calcular_scores(dados_mercado, di_estado):
    """
    Calcula scores ponderados para WDO e WIN.
    Retorna pessimismo, otimismo, neutro e spread.
    """
    pesos_wdo = {"DXY": 3, "VIX": 2, "SP500": 2, "PETROLEO": 1, "MINERIO": 1, "BRL": 2}
    pesos_win = {"DXY": 2, "VIX": 2, "SP500": 3, "PETROLEO": 1, "MINERIO": 2, "BRL": 1}

    resultado = {"WDO": {}, "WIN": {}}

    for ativo, pesos in [("WDO", pesos_wdo), ("WIN", pesos_win)]:
        pess, otim, neu = 0, 0, 0
        for fator, peso in pesos.items():
            if fator not in dados_mercado:
                continue
            var = dados_mercado[fator]["var_pct"]
            classif = classificar_fator(var, fator)
            if classif == "pessimista":
                pess += peso
            elif classif == "otimista":
                otim += peso
            else:
                neu += peso

        # DI como fator adicional de peso alto
        di_peso = 3
        if di_estado == "sobe":
            pess += di_peso  # DI sobe = pessimismo para WIN, altista para WDO
        elif di_estado == "cai":
            otim += di_peso

        total = pess + otim + neu if (pess + otim + neu) > 0 else 1
        resultado[ativo] = {
            "pessimismo": round(pess / total * 10, 2),
            "otimismo": round(otim / total * 10, 2),
            "neutro": round(neu / total * 10, 2),
            "spread": round((pess - otim) / total * 10, 2),
        }

    return resultado


def gerar_sinal(scores, threshold, ativo):
    spread = scores[ativo]["spread"]
    if spread > threshold:
        if ativo == "WDO":
            return "🟢 COMPRA WDO", "#00ff78", "pessimismo domina"
        else:
            return "🔴 VENDA WIN", "#ff5050", "pessimismo domina"
    elif spread < -threshold:
        if ativo == "WDO":
            return "🔴 VENDA WDO", "#ff5050", "otimismo domina"
        else:
            return "🟢 COMPRA WIN", "#00ff78", "otimismo domina"
    else:
        return "⚪ NEUTRO", "#8888aa", "sem confluência"


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>RASTREADOR MACRO</h1>
    <p>Mini Dólar · Mini Índice · Fatores Macro em Tempo Real</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONTROLES
# ─────────────────────────────────────────
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 1])

with col_ctrl1:
    ativo_selecionado = st.selectbox("Ativo", ["WDO — Mini Dólar", "WIN — Mini Índice"], label_visibility="visible")
    ativo = "WDO" if "WDO" in ativo_selecionado else "WIN"

with col_ctrl2:
    threshold = st.slider("Threshold do sinal", min_value=0.5, max_value=4.0, value=2.0, step=0.5)

with col_ctrl3:
    st.markdown("<br>", unsafe_allow_html=True)
    auto_refresh = st.toggle("Auto (60s)", value=False)

# ─────────────────────────────────────────
# DI FUTURO — INPUT MANUAL EM DESTAQUE
# ─────────────────────────────────────────
st.markdown("""<div class="section-title">● DI FUTURO — GATILHO OPERACIONAL</div>""", unsafe_allow_html=True)

col_di1, col_di2, col_di3, col_di4 = st.columns([1, 1, 1, 2])
with col_di1:
    if st.button("⬆ DI SUBIU", use_container_width=True):
        st.session_state.di_estado = "sobe"
with col_di2:
    if st.button("⬇ DI CAIU", use_container_width=True):
        st.session_state.di_estado = "cai"
with col_di3:
    if st.button("➡ DI NEUTRO", use_container_width=True):
        st.session_state.di_estado = "neutro"
with col_di4:
    di = st.session_state.di_estado
    badge_class = "di-sobe" if di == "sobe" else ("di-cai" if di == "cai" else "di-neu")
    di_texto = "DI SUBINDO → pessimista (↑WDO / ↓WIN)" if di == "sobe" else (
               "DI CAINDO → otimista (↓WDO / ↑WIN)" if di == "cai" else
               "DI NEUTRO → sem sinal do gatilho")
    st.markdown(f"""
    <div style="padding-top:0.5rem">
        <span class="di-badge {badge_class}">{di.upper()}</span>
        <span style="font-size:0.75rem; color:#666688; margin-left:0.5rem; font-family:'JetBrains Mono',monospace">{di_texto}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='border-color:#1a1a2a; margin: 1rem 0'>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# BUSCAR DADOS
# ─────────────────────────────────────────
with st.spinner("Atualizando dados de mercado..."):
    dados = buscar_dados_mercado()
    scores = calcular_scores(dados, st.session_state.di_estado)
    st.session_state.ultimo_update = datetime.now().strftime("%H:%M:%S")

    # Registrar no histórico automaticamente
    entrada = {
        "hora": datetime.now().strftime("%H:%M"),
        "pessimismo_wdo": scores["WDO"]["pessimismo"],
        "otimismo_wdo":   scores["WDO"]["otimismo"],
        "neutro_wdo":     scores["WDO"]["neutro"],
        "spread_wdo":     scores["WDO"]["spread"],
        "pessimismo_win": scores["WIN"]["pessimismo"],
        "otimismo_win":   scores["WIN"]["otimismo"],
        "neutro_win":     scores["WIN"]["neutro"],
        "spread_win":     scores["WIN"]["spread"],
    }
    # Evita duplicatas no mesmo minuto
    if not st.session_state.historico or st.session_state.historico[-1]["hora"] != entrada["hora"]:
        st.session_state.historico.append(entrada)
        if len(st.session_state.historico) > 120:
            st.session_state.historico = st.session_state.historico[-120:]

# ─────────────────────────────────────────
# SINAIS E SCORES
# ─────────────────────────────────────────
sinal_wdo, cor_wdo, desc_wdo = gerar_sinal(scores, threshold, "WDO")
sinal_win, cor_win, desc_win = gerar_sinal(scores, threshold, "WIN")

col_s1, col_s2, col_s3, col_s4 = st.columns(4)

with col_s1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sinal WDO</div>
        <div class="metric-value" style="color:{cor_wdo}; font-size:1rem">{sinal_wdo}</div>
        <div style="font-size:0.65rem; color:#444466; margin-top:0.2rem; font-family:'JetBrains Mono'">{desc_wdo}</div>
    </div>
    """, unsafe_allow_html=True)

with col_s2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sinal WIN</div>
        <div class="metric-value" style="color:{cor_win}; font-size:1rem">{sinal_win}</div>
        <div style="font-size:0.65rem; color:#444466; margin-top:0.2rem; font-family:'JetBrains Mono'">{desc_win}</div>
    </div>
    """, unsafe_allow_html=True)

with col_s3:
    spread_val = scores[ativo]["spread"]
    cor_spread = "#00ff78" if spread_val > 0 else ("#ff5050" if spread_val < 0 else "#8888aa")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Spread {ativo}</div>
        <div class="metric-value" style="color:{cor_spread}">{spread_val:+.2f}</div>
        <div style="font-size:0.65rem; color:#444466; margin-top:0.2rem; font-family:'JetBrains Mono'">threshold: ±{threshold}</div>
    </div>
    """, unsafe_allow_html=True)

with col_s4:
    brl_var = dados.get("BRL", {}).get("var_pct", 0)
    cor_brl = "#00ff78" if brl_var > 0 else ("#ff5050" if brl_var < 0 else "#8888aa")
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">USD/BRL variação</div>
        <div class="metric-value" style="color:{cor_brl}">{brl_var:+.2f}%</div>
        <div style="font-size:0.65rem; color:#444466; margin-top:0.2rem; font-family:'JetBrains Mono'">hoje vs. abertura</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# GRÁFICO PRINCIPAL
# ─────────────────────────────────────────
st.markdown(f"""<div class="section-title">● GRÁFICO — {ativo_selecionado.upper()}</div>""", unsafe_allow_html=True)

if len(st.session_state.historico) >= 2:
    df = pd.DataFrame(st.session_state.historico)
    horas = df["hora"].tolist()
    suf = ativo.lower()

    fig = go.Figure()

    # Área de fundo para spread positivo/negativo
    fig.add_hrect(y0=threshold, y1=10, fillcolor="rgba(0,255,120,0.03)", line_width=0)
    fig.add_hrect(y0=-10, y1=-threshold, fillcolor="rgba(255,80,80,0.03)", line_width=0)

    # Linha threshold
    fig.add_hline(y=threshold, line_dash="dot", line_color="rgba(255,200,0,0.3)", line_width=1)
    fig.add_hline(y=-threshold, line_dash="dot", line_color="rgba(255,200,0,0.3)", line_width=1)
    fig.add_hline(y=0, line_color="rgba(100,100,140,0.4)", line_width=1)

    # Pessimismo (verde)
    fig.add_trace(go.Scatter(
        x=horas, y=df[f"pessimismo_{suf}"],
        name="Pessimismo", mode="lines",
        line=dict(color="#00ff78", width=2.5),
        fill="tozeroy", fillcolor="rgba(0,255,120,0.04)"
    ))

    # Otimismo (vermelho)
    fig.add_trace(go.Scatter(
        x=horas, y=[-v for v in df[f"otimismo_{suf}"]],
        name="Otimismo", mode="lines",
        line=dict(color="#ff5050", width=2.5),
        fill="tozeroy", fillcolor="rgba(255,80,80,0.04)"
    ))

    # Neutro (cinza)
    fig.add_trace(go.Scatter(
        x=horas, y=df[f"neutro_{suf}"],
        name="Neutro", mode="lines",
        line=dict(color="#555577", width=1, dash="dot"),
    ))

    # Rastro do Macro (azul)
    fig.add_trace(go.Scatter(
        x=horas, y=df[f"spread_{suf}"],
        name="Rastro do Macro", mode="lines+markers",
        line=dict(color="#4488ff", width=2, dash="dash"),
        marker=dict(size=5, color="#4488ff"),
    ))

    fig.update_layout(
        paper_bgcolor="#0a0a0f",
        plot_bgcolor="#0d0d18",
        font=dict(family="JetBrains Mono", color="#555577", size=11),
        height=380,
        margin=dict(l=10, r=10, t=20, b=30),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            font=dict(size=10), bgcolor="rgba(0,0,0,0)"
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=9), linecolor="#1e1e2e"
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#111122", zeroline=False,
            tickfont=dict(size=9), range=[-11, 11]
        ),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:-0.5rem">
        <span style="font-size:0.65rem; color:#222244; font-family:'JetBrains Mono'">
            Verde acima = pessimismo domina → {'COMPRA WDO' if ativo=='WDO' else 'VENDA WIN'} &nbsp;|&nbsp;
            Vermelho abaixo = otimismo domina → {'VENDA WDO' if ativo=='WDO' else 'COMPRA WIN'} &nbsp;|&nbsp;
            Azul cruza threshold = sinal ativo
        </span>
        <span class="timestamp">atualizado: {st.session_state.ultimo_update}</span>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center; padding: 3rem; color:#333355; font-family:'JetBrains Mono'; font-size:0.8rem">
        AGUARDANDO DADOS... <br><span style="font-size:0.65rem">O gráfico será construído conforme as leituras forem registradas</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# FATORES DE MERCADO
# ─────────────────────────────────────────
st.markdown("""<div class="section-title">● FATORES DE MERCADO — VARIAÇÃO NO DIA</div>""", unsafe_allow_html=True)

fatores_info = {
    "DXY":     ("DXY — Índice do Dólar",    "↑ pessimista (dólar forte)"),
    "VIX":     ("VIX — Volatilidade S&P",   "↑ pessimista (risco aversão)"),
    "SP500":   ("S&P 500 Futuros",           "↑ otimista (apetite a risco)"),
    "PETROLEO":("Petróleo WTI",              "↑ inflação / ambíguo"),
    "MINERIO": ("VALE3 (proxy minério)",     "↑ otimista (commodities)"),
    "BRL":     ("USD/BRL",                  "↑ pessimista (dólar subiu)"),
}

cols_fat = st.columns(3)
for i, (chave, (nome, desc)) in enumerate(fatores_info.items()):
    d = dados.get(chave, {})
    var = d.get("var_pct", 0)
    classif = classificar_fator(var, chave)
    cor = "#00ff78" if classif == "otimista" else ("#ff5050" if classif == "pessimista" else "#555577")
    seta = "▲" if var > 0 else ("▼" if var < 0 else "—")

    with cols_fat[i % 3]:
        st.markdown(f"""
        <div class="metric-card" style="margin-bottom:0.5rem">
            <div class="metric-label">{nome}</div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.3rem">
                <span style="font-family:'JetBrains Mono'; font-size:1rem; color:{cor}; font-weight:600">{seta} {var:+.2f}%</span>
                <span style="font-size:0.65rem; color:{cor}; font-family:'JetBrains Mono'">{classif.upper()}</span>
            </div>
            <div style="font-size:0.6rem; color:#333355; margin-top:0.15rem; font-family:'JetBrains Mono'">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────
# RODAPÉ
# ─────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding: 1rem 0; border-top: 1px solid #1a1a2a; margin-top:1rem">
    <span style="font-family:'JetBrains Mono'; font-size:0.6rem; color:#222244; letter-spacing:0.2em">
        DADOS VIA YAHOO FINANCE (DELAY ~15MIN) · DI VIA INPUT MANUAL · NÃO CONSTITUI RECOMENDAÇÃO DE INVESTIMENTO
    </span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────
if auto_refresh:
    time_module.sleep(60)
    st.rerun()
