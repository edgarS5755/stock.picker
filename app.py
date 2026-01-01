import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION (FULL DARK MODE) ---
st.set_page_config(page_title="FHi - Market Intelligence", layout="wide", page_icon="🌐")

# --- CSS PRO (STYLE Bloomberg) ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #e1e3e6; }
    
    /* Input Search amélioré */
    .stTextInput > div > div > input {
        background-color: #1e2329; color: white; border: 1px solid #363c45; border-radius: 8px;
    }
    
    /* Onglets du haut */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #2d333b; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: #161b22; color: #8b949e; border-radius: 6px; border: 1px solid #30363d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2962ff !important; color: white !important; font-weight: 600;
    }
    
    /* Cartes Métriques */
    .metric-container {
        background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px;
    }
    div[data-testid="stMetricValue"] { color: #fff; }
    
    /* Sidebar Logo */
    [data-testid="stSidebar"] img { opacity: 0.9; margin: 0 auto 20px auto; display: block; }
</style>
""", unsafe_allow_html=True)

# --- DONNÉES & MAPPING ---
# Base élargie pour la reconnaissance de noms
TICKER_MAP = {
    "APPLE": "AAPL", "MICROSOFT": "MSFT", "NVIDIA": "NVDA", "GOOGLE": "GOOGL", "AMAZON": "AMZN", "META": "META", "TESLA": "TSLA",
    "LVMH": "MC.PA", "HERMES": "RMS.PA", "LOREAL": "OR.PA", "TOTAL": "TTE.PA", "AIRBUS": "AIR.PA", "SANOFI": "SAN.PA",
    "COINBASE": "COIN", "BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD", "PALANTIR": "PLTR", "AMD": "AMD"
}

# Mapping des concurrents par secteur (Pour l'IA)
SECTOR_PEERS = {
    "Technology": ["MSFT", "AAPL", "NVDA", "ORCL"],
    "Financial Services": ["JPM", "BAC", "V", "MA"],
    "Healthcare": ["JNJ", "PFE", "LLY", "UNH"],
    "Consumer Cyclical": ["AMZN", "TSLA", "TM", "NKE"],
    "Energy": ["XOM", "CVX", "SHEL", "TTE.PA"],
    "Communication Services": ["GOOGL", "META", "NFLX", "DIS"]
}

# --- FONCTIONS ---

def safe_format(value, format_str="{}", fallback="—"):
    if value is None or value == "None" or value == "N/A":
        return fallback
    try:
        return format_str.format(value)
    except:
        return fallback

@st.cache_data(ttl=1800)
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist, stock
    except:
        return None, None, None

def get_peer_comparison(sector, current_ticker):
    """Trouve des rivaux et compare les chiffres clés"""
    peers = SECTOR_PEERS.get(sector, [])
    # Si on ne trouve pas le secteur exact, on prend des rivaux génériques ou on annule
    if not peers:
        # Tentative de mapping flou ou retour vide
        if "Tech" in str(sector): peers = SECTOR_PEERS["Technology"]
        else: return []
    
    # On retire l'action actuelle de la liste des rivaux
    peers = [p for p in peers if p != current_ticker]
    
    comparison_data = []
    for p in peers[:2]: # On compare avec les 2 premiers trouvés pour la rapidité
        try:
            p_info = yf.Ticker(p).fast_info
            # On utilise fast_info pour la rapidité, ou info si besoin
            p_pe = yf.Ticker(p).info.get('trailingPE', 0)
            comparison_data.append({
                "ticker": p,
                "pe": p_pe,
                "cap": p_info.market_cap
            })
        except:
            continue
    return comparison_data

def local_ai_logic(user_query, info, ticker):
    """Cerveau amélioré du Bot"""
    query = user_query.lower()
    name = info.get('shortName', ticker)
    sector = info.get('sector', 'Unknown')
    summary = info.get('longBusinessSummary', "Pas d'historique disponible.")
    
    # 1. HISTOIRE / ACTIVITÉ
    if any(x in query for x in ["histoire", "history", "fait quoi", "activite", "entreprise", "business"]):
        return f"**À propos de {name} :**\n\n{summary[:800]}..."
    
    # 2. CONCURRENTS / RIVAUX
    elif any(x in query for x in ["concurrent", "rival", "competitor", "mieux que", "comparaison"]):
        peers_data = get_peer_comparison(sector, ticker)
        if not peers_data:
            return f"{name} opère dans le secteur '{sector}'. Je n'ai pas de données précises sur ses rivaux directs dans ma base immédiate, mais vous pouvez regarder les leaders de ce secteur."
        
        response = f"**Analyse Concurrentielle ({sector}) :**\n\n"
        current_pe = info.get('trailingPE', 0)
        
        for p in peers_data:
            rival_pe = p['pe']
            rival_name = p['ticker']
            
            response += f"- **Vs {rival_name}** : "
            if current_pe and rival_pe:
                diff = ((current_pe - rival_pe) / rival_pe) * 100
                if diff > 0:
                    response += f"{name} est plus chère (PER {current_pe:.1f} vs {rival_pe:.1f}). "
                else:
                    response += f"{name} est plus abordable (PER {current_pe:.1f} vs {rival_pe:.1f}). "
            else:
                response += "Données de comparaison incomplètes. "
            response += "\n"
            
        return response

    # 3. ANALYSE FINANCIÈRE / CONSEIL
    elif any(x in query for x in ["acheter", "buy", "avis", "vendre", "bon moment"]):
        target = info.get('targetMeanPrice')
        price = info.get('currentPrice')
        recom = info.get('recommendationKey', 'none').upper()
        
        if target and price:
            upside = ((target - price) / price) * 100
            sentiment = "HAUSSIER" if upside > 10 else "NEUTRE/BAISSIER"
            return f"**Conseil FHi :**\n\nLes analystes sont majoritairement **{recom}**.\nObjectif moyen : {target} (Potentiel {upside:+.1f}%).\n\nMon analyse : Le sentiment est {sentiment}. Vérifiez le contexte macro-économique avant d'investir."
        else:
            return "Je manque de données analystes pour émettre un conseil fiable sur cette action."

    # DEFAULT
    return f"Je suis l'assistant dédié à {name}. Posez-moi des questions sur son **histoire**, ses **concurrents** ou demandez un **avis d'investissement**."

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("image_2.png", width=140)
    except:
        st.header("FHi")
    
    st.markdown("### 🔍 Recherche Universelle")
    search_input = st.text_input("Symbole ou Nom", placeholder="Apple, Air Liquide, BTC-USD...").upper()
    
    # Logique de résolution de symbole
    selected_ticker = None
    if search_input:
        # 1. Check Map
        for key, val in TICKER_MAP.items():
            if search_input in key:
                selected_ticker = val
                break
        # 2. Fallback direct (Access to everything)
        if not selected_ticker:
            selected_ticker = search_input

    st.markdown("---")
    st.markdown("### 🔐 Espace Pro")
    pwd = st.text_input("Licence Key", type="password")
    IS_PREMIUM = pwd == "PRO2026"
    
    if IS_PREMIUM:
        st.success("Mode Trader Actif")

# --- INTERFACE PRINCIPALE ---
st.title("FHi Market Intelligence")

# Compartiments Sectoriels (Navigation Rapide)
if not selected_ticker:
    st.subheader("Tendances par Secteur")
    tabs = st.tabs(["🔥 Tech & IA", "💎 Luxe & Europe", "⚡ Énergie", "₿ Crypto", "💊 Santé"])
    
    sectors_ui = {
        "🔥 Tech & IA": ["NVDA", "PLTR", "MSFT", "GOOGL", "AMD", "TSLA", "SNOW"],
        "💎 Luxe & Europe": ["MC.PA", "RMS.PA", "OR.PA", "AIR.PA", "RACE.MI"],
        "⚡ Énergie": ["TTE.PA", "XOM", "SHELL", "ENPH", "FSLR"],
        "₿ Crypto": ["COIN", "MSTR", "BTC-USD", "ETH-USD", "SOL-USD"],
        "💊 Santé": ["LLY", "NVO", "MRNA", "PFE", "SANOFI"]
    }
    
    for i, (tab_name, tickers) in enumerate(sectors_ui.items()):
        with tabs[i]:
            cols = st.columns(6)
            for j, t in enumerate(tickers):
                if cols[j % 6].button(t, key=f"sect_{t}"):
                    st.session_state['quick_select'] = t
                    st.rerun()

# Gestion de la sélection
if 'quick_select' in st.session_state and not search_input:
    selected_ticker = st.session_state['quick_select']

# --- AFFICHAGE DE L'ACTION SÉLECTIONNÉE ---
if selected_ticker:
    info, hist, stock_obj = get_data(selected_ticker)
    
    if info:
        # Header
        col_h1, col_h2 = st.columns([3, 1])
        name = info.get('shortName', selected_ticker)
        price = info.get('currentPrice', info.get('regularMarketPreviousClose'))
        currency = info.get('currency', 'USD')
        
        with col_h1:
            st.header(f"{name} ({selected_ticker})")
            st.caption(f"{info.get('sector', 'Secteur Inconnu')} | {info.get('country', 'Monde')}")
        with col_h2:
            st.metric("Prix", f"{price} {currency}" if price else "N/A")

        # Onglets
        t_chart, t_fund, t_pro, t_news, t_ai = st.tabs(["📈 Graphique", "💰 Financier", "🏦 Analystes", "📰 News", "🤖 Bot FHi"])

        # 1. GRAPHIQUE
        with t_chart:
            if not hist.empty:
                fig = go.Figure(data=[go.Candlestick(x=hist.index,
                                open=hist['Open'], high=hist['High'],
                                low=hist['Low'], close=hist['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Graphique indisponible.")

        # 2. FINANCIER
        with t_fund:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Capitalisation", safe_format(info.get('marketCap'), "{:,.0f}"))
            c2.metric("PER", safe_format(info.get('trailingPE'), "{:.2f}"))
            c3.metric("Bénéfice/Action", safe_format(info.get('trailingEps'), "{:.2f}"))
            c4.metric("Dividende", safe_format(info.get('dividendYield'), "{:.2%}"))
            st.write("---")
            st.write(info.get('longBusinessSummary', ''))

        # 3. ANALYSTES
        with t_pro:
            if IS_PREMIUM:
                col_p1, col_p2 = st.columns(2)
                target = info.get('targetMeanPrice')
                
                with col_p1:
                    st.metric("Objectif Moyen", f"{target} {currency}" if target else "N/A")
                    if target and price:
                        pot = ((target - price) / price) * 100
                        color = "green" if pot > 0 else "red"
                        st.markdown(f"Potentiel : :{color}[**{pot:+.2f}%**]")
                
                with col_p2:
                    st.metric("Avis Consensus", info.get('recommendationKey', 'Inconnu').upper().replace("_", " "))
                
                st.markdown("---")
                st.caption("Sources externes pour vérification :")
                c_s1, c_s2, c_s3 = st.columns(3)
                c_s1.link_button("Yahoo Finance", f"https://finance.yahoo.com/quote/{selected_ticker}")
                c_s2.link_button("MarketWatch", f"https://www.marketwatch.com/investing/stock/{selected_ticker}")
                c_s3.link_button("Google Finance", f"https://www.google.com/finance/quote/{selected_ticker}:NASDAQ")
            else:
                st.warning("🔒 Section réservée aux membres PRO (Objectifs de prix & Consensus).")

        # 4. NEWS
        with t_news:
            st.subheader(f"Actualités : {name}")
            try:
                news = stock_obj.news[:5]
                if news:
                    for n in news:
                        st.markdown(f"**[{n.get('title')}]({n.get('link')})**")
                        st.caption(f"{n.get('publisher')} - {datetime.fromtimestamp(n.get('providerPublishTime', 0)).strftime('%d/%m/%Y')}")
                        st.write("---")
                else:
                    st.info("Pas d'actualités récentes via l'API.")
            except:
                st.error("Erreur chargement news.")

        # 5. BOT IA
        with t_ai:
            st.markdown(f"### 🤖 Assistant FHi : {name}")
            
            # Initialisation historique
            if "messages" not in st.session_state:
                st.session_state.messages = [{"role": "assistant", "content": "Bonjour. Je peux analyser l'histoire, les concurrents ou le potentiel de cette action."}]
            
            # Affichage historique
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])
            
            # Input Utilisateur
            if user_input := st.chat_input("Posez une question sur l'action..."):
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.chat_message("user").write(user_input)
                
                # Génération réponse
                with st.spinner("Analyse en cours..."):
                    if IS_PREMIUM:
                        response = local_ai_logic(user_input, info, selected_ticker)
                    else:
                        response = "🔒 L'IA avancée (Comparaison Concurrents & Avis) est réservée aux membres PRO."
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.chat_message("assistant").write(response)

    else:
        st.error(f"Action '{selected_ticker}' introuvable. Essayez le symbole exact (ex: MC.PA pour LVMH).")
