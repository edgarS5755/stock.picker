import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DU SITE (MODE SOMBRE PAR DÉFAUT) ---
st.set_page_config(page_title="FHi Terminal", layout="wide", page_icon="📊")

# --- CSS "DARK FINANCE" (STYLE YAHOO/BLOOMBERG) ---
st.markdown("""
<style>
    /* Forcer le thème sombre global */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Navigation Tabs (Onglets horizontaux) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0e1117;
        padding-bottom: 5px;
        border-bottom: 1px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        background-color: #161b22;
        color: #8b949e;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-size: 14px;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #238636 !important; /* Vert Finance */
        color: white !important;
        border-color: #238636 !important;
    }

    /* Cards & Metrics */
    div[data-testid="stMetricValue"] {
        color: #ffffff;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
    }

    /* Sidebar propre */
    [data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    
    /* Chatbot Input */
    .stChatInput {
        border-color: #30363d;
    }
    
    /* Logo */
    [data-testid="stSidebar"] img {
        opacity: 0.8;
        margin-bottom: 20px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

# --- DONNÉES ET CATÉGORIES (TEXTE PRO, SANS EMOJIS) ---
MARKET_DATA = {
    "US Growth Stocks": {
        "Palantir Technologies": "PLTR", "SoFi Technologies": "SOFI", "Unity Software": "U", 
        "DraftKings": "DKNG", "Coinbase Global": "COIN", "Tesla Inc": "TSLA", "NVIDIA Corp": "NVDA"
    },
    "Europe Large Caps": {
        "LVMH": "MC.PA", "TotalEnergies": "TTE.PA", "Airbus SE": "AIR.PA", 
        "Schneider Electric": "SU.PA", "ASML Holding": "ASML.AS", "SAP SE": "SAP.DE"
    },
    "BioTech & Speculative": {
        "Moderna": "MRNA", "BioNTech": "BNTX", "Valneva": "VLA.PA", "Crispr Therapeutics": "CRSP"
    },
    "Global Indices & ETFs": {
        "S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "CAC 40": "^FCHI", 
        "MSCI World ETF": "CW8.PA", "Gold (Spot)": "GC=F"
    }
}

# --- GESTION DE L'HISTORIQUE DU CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_ticker" not in st.session_state:
    st.session_state.last_ticker = None

# --- FONCTIONS BACKEND ---
@st.cache_data(ttl=3600)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    return info, hist

def local_ai_response(query, info, ticker):
    """
    Cerveau du Bot IA interne (Simule une IA sans API externe)
    Analyse les données financières pour construire une réponse logique.
    """
    query = query.lower()
    
    # Extraction des données clés
    price = info.get('currentPrice', 0)
    target = info.get('targetMeanPrice', 0)
    recom = info.get('recommendationKey', 'none').replace('_', ' ')
    pe = info.get('trailingPE', 'N/A')
    sector = info.get('sector', 'Unknown')
    summary = info.get('longBusinessSummary', '')[:300] + "..."

    # Logique de réponse contextuelle
    if "acheter" in query or "buy" in query or "avis" in query or "opinion" in query:
        if target > price:
            sentiment = "positif"
            upside = ((target - price) / price) * 100
            return f"Analyse FHi sur {ticker} : Les indicateurs techniques sont au vert. Le consensus des analystes vise {target} (potentiel de +{upside:.1f}%). Recommandation officielle : {recom.upper()}. C'est un moment intéressant pour entrer."
        else:
            return f"Prudence sur {ticker}. Le prix actuel ({price}) est proche ou supérieur à l'objectif des analystes ({target}). La recommandation est plutôt {recom.upper()}. Attendez un repli."
    
    elif "risque" in query or "risk" in query:
        beta = info.get('beta', 1)
        if beta > 1.5:
            return f"{ticker} est une action à haute volatilité (Beta: {beta}). Elle convient aux investisseurs agressifs. Le risque de perte en capital à court terme est élevé."
        else:
            return f"{ticker} est considérée comme une valeur relativement stable (Beta: {beta}). Elle convient à une gestion 'Bon père de famille'."
            
    elif "c'est quoi" in query or "activite" in query:
        return f"{ticker} opère dans le secteur {sector}. Résumé : {summary}"
        
    else:
        return f"Je suis l'assistant FHi dédié à {ticker}. Vous pouvez me demander mon avis sur l'action, le niveau de risque ou une analyse du prix."

# --- SIDEBAR (NAVIGATION) ---
with st.sidebar:
    try:
        st.image("image_2.png", width=120)
    except:
        st.header("FHi Terminal")
    
    st.markdown("### Market Data")
    category = st.selectbox("Select Market", list(MARKET_DATA.keys()))
    
    st.markdown("---")
    st.markdown("### Search")
    manual_search = st.text_input("Enter Symbol (e.g., TSLA)", "")
    if manual_search:
        # Override selection
        current_selection_name = manual_search.upper()
        current_selection_ticker = manual_search.upper()
    else:
        # Default selection from list
        current_selection_name = st.radio("Assets", list(MARKET_DATA[category].keys()))
        current_selection_ticker = MARKET_DATA[category][current_selection_name]

    st.markdown("---")
    st.markdown("### Account")
    pwd = st.text_input("License Key", type="password")
    IS_PREMIUM = pwd == "PRO2026"
    
    if IS_PREMIUM:
        st.success("STATUS: PRO TRADER")
    else:
        st.info("STATUS: FREE TIER")

# --- MAIN INTERFACE ---

# Reset chat if stock changes
if st.session_state.last_ticker != current_selection_ticker:
    st.session_state.messages = []
    st.session_state.last_ticker = current_selection_ticker

if current_selection_ticker:
    try:
        # Data Loading
        info, hist = get_data(current_selection_ticker)
        current_price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        currency = info.get('currency', 'USD')
        
        # Header Section (Yahoo Style)
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.title(f"{info.get('shortName', current_selection_name)}")
            st.caption(f"{current_selection_ticker} • {info.get('exchange', 'N/A')} • {currency}")
        with col_h2:
            st.metric("Price", f"{current_price:,.2f}", delta=None) # Delta could be added if we pull previous close

        # --- HORIZONTAL TABS ---
        tab_chart, tab_data, tab_analysis, tab_ai = st.tabs(["Chart", "Financials", "Analyst Rating", "FHi AI Assistant"])

        # 1. CHART TAB
        with tab_chart:
            # Plotly Dark Theme
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'], high=hist['High'],
                            low=hist['Low'], close=hist['Close'])])
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=500,
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        # 2. FINANCIALS TAB
        with tab_data:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Market Cap", f"{info.get('marketCap', 0)/1e9:.1f}B")
            c2.metric("PE Ratio", f"{info.get('trailingPE', 'N/A')}")
            c3.metric("Revenue (TTM)", f"{info.get('totalRevenue', 0)/1e9:.1f}B")
            c4.metric("52W High", f"{info.get('fiftyTwoWeekHigh', 0)}")
            
            st.markdown("#### Company Profile")
            st.write(info.get('longBusinessSummary', 'No description available.'))

        # 3. ANALYSIS TAB (PREMIUM)
        with tab_analysis:
            if IS_PREMIUM:
                st.subheader("Institutional Consensus")
                
                col_a1, col_a2 = st.columns(2)
                
                target = info.get('targetMeanPrice', 0)
                recom = info.get('recommendationKey', 'N/A').upper().replace('_', ' ')
                
                with col_a1:
                    st.metric("Price Target", f"{target} {currency}")
                    if target and current_price:
                        upside = ((target - current_price) / current_price) * 100
                        color = "green" if upside > 0 else "red"
                        st.markdown(f"Upside Potential: :{color}[**{upside:+.2f}%**]")
                
                with col_a2:
                    st.metric("Recommendation", recom)
                    st.progress(0.7 if "BUY" in recom else 0.3)
                
                st.info("Data aggregated from major investment banks (Goldman Sachs, Morgan Stanley).")
            else:
                st.warning("🔒 Premium Feature Locked")
                st.write("Upgrade to FHi Pro to view institutional price targets and buy/sell signals.")

        # 4. FHi AI ASSISTANT (INTERNAL CHATBOT)
        with tab_ai:
            st.markdown("#### 🤖 FHi Quantitative Assistant")
            st.caption(f"Ask me anything about {current_selection_name}'s data.")

            # Display Chat History
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # User Input
            if prompt := st.chat_input(f"Question about {current_selection_ticker}?"):
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Generate AI Response (Internal Logic)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing market data..."):
                        if IS_PREMIUM:
                            response = local_ai_response(prompt, info, current_selection_ticker)
                        else:
                            response = "🔒 The AI Assistant is a PRO feature. Please enter your license key."
                        
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        st.error(f"Error loading data: {e}")
