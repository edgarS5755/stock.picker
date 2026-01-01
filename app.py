import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURATION DU SITE ---
st.set_page_config(page_title="FHi - Smart Stock Picker", layout="wide", page_icon="📈")

# --- CSS AVANCÉ ---
st.markdown("""
<style>
    /* Navigation */
    button[data-baseweb="tab"] {
        background-color: #ffffff !important;
        color: #31333F !important;
        font-weight: 600 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 5px !important;
        margin-right: 5px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #000000 !important; /* Noir FHi */
        color: white !important;
        border: 1px solid #000000 !important;
    }
    
    /* Zone Premium Grise */
    .premium-box {
        background-color: #e9ecef; /* Gris */
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #000000;
        color: #333;
    }
    
    /* Boutons de sélection d'actifs */
    .stButton>button {width: 100%; border-radius: 5px; border: 1px solid #ddd;}
    
    /* Logo Sidebar */
    [data-testid="stSidebar"] img {
        opacity: 0.9;
        margin-bottom: 20px;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
</style>
""", unsafe_allow_html=True)

# --- DONNÉES ET CATÉGORIES (SELECTION ÉLARGIE) ---
MARKET_DATA = {
    "🚀 Pépites US (Growth)": {
        "Palantir (AI)": "PLTR", "SoFi Technologies": "SOFI", "Unity Software": "U", 
        "DraftKings": "DKNG", "UiPath (Auto)": "PATH", "Coinbase": "COIN",
        "Rocket Lab (Espace)": "RKLB", "Crispr (Genomics)": "CRSP"
    },
    "🇪🇺 Europe Croissance": {
        "Dassault Systèmes": "DSY.PA", "Schneider Electric": "SU.PA", "Adyen (Paiement)": "ADYEN.AS", 
        "ASML (Semiconducteurs)": "ASML.AS", "Ferrari": "RACE.MI", "Airbus": "AIR.PA",
        "Thales": "HO.PA", "Capgemini": "CAP.PA"
    },
    "💉 BioTech & Pharma (Risqué)": {
        "Moderna": "MRNA", "BioNTech": "BNTX", "Valneva": "VLA.PA", 
        "Sartorius": "DIM.PA", "Eurofins": "ERF.PA"
    },
    "🏢 Blue Chips (Sécurité)": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Berkshire Hathaway": "BRK-B", 
        "LVMH": "MC.PA", "TotalEnergies": "TTE.PA", "Air Liquide": "AI.PA"
    },
    "🌍 Indices & ETFs": {
        "S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "CAC 40": "^FCHI", 
        "ETF World (CW8)": "CW8.PA", "ETF Emerging": "PAEEM.PA"
    }
}

# --- GESTION DE L'ÉTAT ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "PLTR" 
if 'selected_name' not in st.session_state:
    st.session_state.selected_name = "Palantir"

def set_ticker(name, ticker):
    st.session_state.selected_ticker = ticker
    st.session_state.selected_name = name

# --- FONCTIONS ---
@st.cache_data(ttl=3600)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    return info, hist

def generate_ai_prompt(risk, horizon, capital):
    """Génère un prompt intelligent"""
    return f"""Agis comme un analyste financier expert (type Warren Buffett croisé avec un Capital Risqueur).
Mon profil : Investisseur avec un risque '{risk}', pour un horizon de '{horizon}', capital de départ '{capital}'.
Analyse l'action [INSÉRER NOM ACTION ICI] en te basant sur ses derniers chiffres.
1. Cette entreprise a-t-elle un avantage concurrentiel durable (Moat) ?
2. Quels sont les 3 risques majeurs qui pourraient faire chuter le cours de 50% ?
3. Estime si le prix actuel est une opportunité ou une bulle.
Réponds avec un ton direct, sans jargon inutile."""

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("image_2.png", width=140)
    except:
        st.header("FHi")
    
    st.markdown("### 🧭 Explorateur")
    category = st.radio("Sélection FHi", list(MARKET_DATA.keys()))
    
    st.markdown("---")
    st.markdown("### 🛠 Recherche Manuelle")
    st.caption("Cherchez n'importe quelle action (US ou EU)")
    manual_search = st.text_input("Symbole (ex: TSLA, OR.PA)", "")
    if st.button("Chercher"):
        if manual_search:
            set_ticker(manual_search.upper(), manual_search.upper())

    st.markdown("---")
    st.markdown("### 🔐 FHi Premium")
    pwd = st.text_input("Clé d'activation", type="password")
    IS_PREMIUM = pwd == "PRO2026"
    
    if IS_PREMIUM:
        st.success("Licence ACTIVE")
    else:
        st.info("🔒 Mode Standard")
        st.caption("Débloquez le consensus bancaire.")

# --- PAGE PRINCIPALE ---

# 1. TABLEAU DE BORD DE SÉLECTION
st.title(f"Marché : {category}")

cols = st.columns(4)
assets_list = list(MARKET_DATA[category].items())

for i, (name, ticker_sym) in enumerate(assets_list):
    col = cols[i % 4]
    if col.button(f"🔎 {name}", key=f"btn_{ticker_sym}"):
        set_ticker(name, ticker_sym)

st.markdown("---")

# 2. ZONE D'ANALYSE
current_ticker = st.session_state.selected_ticker
current_name = st.session_state.selected_name

if current_ticker:
    try:
        info, hist = get_data(current_ticker)
        curr_price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        currency = info.get('currency', 'USD')
        
        # En-tête
        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.header(f"{current_name} ({current_ticker})")
            st.caption(f"Secteur: {info.get('sector', 'N/A')} | Industrie: {info.get('industry', 'N/A')}")
        with col_h2:
            st.metric("Prix", f"{curr_price} {currency}")

        # ONGLETS
        tab_ia, tab_view, tab_financials, tab_pro = st.tabs(["🤖 Assistant IA", "📈 Graphique", "💰 Données (Gratuit)", "🏦 Banques (PREMIUM)"])

        # --- ONGLET 1 : ASSISTANT IA (NOUVEAU) ---
        with tab_ia:
            st.subheader("Assistant de Stratégie FHi")
            col_ia1, col_ia2 = st.columns([1, 2])
            
            with col_ia1:
                st.write("Profil de l'investisseur :")
                risk_level = st.select_slider("Votre tolérance au risque", options=["Faible (Bon père de famille)", "Moyen (Équilibré)", "Élevé (Aggressif/Crypto)"])
                horizon = st.selectbox("Horizon de placement", ["Court terme (Semaines)", "Moyen terme (1-3 ans)", "Long terme (Retraite)"])
                capital = st.selectbox("Capital", ["< 1 000€", "1 000€ - 10 000€", "> 10 000€"])
                
                if st.button("Générer ma stratégie"):
                    st.success("Profil analysé.")
            
            with col_ia2:
                st.info(f"💡 **Conseil FHi pour le profil {risk_level} :**")
                
                if "Élevé" in risk_level:
                    st.write("Vous cherchez de la performance. Concentrez-vous sur les 'Pépites US' et la 'BioTech'. Acceptez une volatilité de -30%.")
                elif "Moyen" in risk_level:
                    st.write("Visez la croissance stable. Le secteur 'Europe Croissance' ou les GAFAM ('Blue Chips') sont idéaux.")
                else:
                    st.write("Priorité sécurité. Regardez les ETFs et les actions à dividendes (TotalEnergies, Air Liquide).")
                
                st.markdown("### 🧠 Votre Super-Prompt")
                st.write("Copiez ce texte et collez-le dans ChatGPT/Claude pour une analyse sur-mesure de cette action :")
                prompt_text = generate_ai_prompt(risk_level, horizon, capital)
                st.code(prompt_text.replace("[INSÉRER NOM ACTION ICI]", current_ticker), language="text")

        # --- ONGLET 2 : GRAPHIQUE ---
        with tab_view:
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'], high=hist['High'],
                            low=hist['Low'], close=hist['Close'])])
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)

        # --- ONGLET 3 : FINANCIER (DÉBLOQUÉ) ---
        with tab_financials:
            st.write("Données fondamentales accessibles à tous les membres.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Capitalisation", f"{info.get('marketCap', 0)/1e9:.1f} Mrd")
            c2.metric("Revenus (TTM)", f"{info.get('totalRevenue', 0)/1e9:.1f} Mrd")
            c3.metric("Marge Bénéficiaire", f"{info.get('profitMargins', 0)*100:.1f}%")
            c4.metric("Dette/Equity", f"{info.get('debtToEquity', 'N/A')}")
            
            st.markdown("#### Description")
            st.write(info.get('longBusinessSummary', 'Pas de description.'))

        # --- ONGLET 4 : PRO / BANQUES (PREMIUM GRIS) ---
        with tab_pro:
            if IS_PREMIUM:
                # CONTENU PAYANT EN GRIS
                st.markdown('<div class="premium-box">', unsafe_allow_html=True)
                
                st.subheader("🔒 Consensus des Banques & Analystes")
                
                target = info.get('targetMeanPrice')
                recommendation = info.get('recommendationKey', 'inconnu').upper().replace("_", " ")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.metric("🎯 Objectif de Prix Moyen", f"{target} {currency}")
                    if target and curr_price:
                        pot = ((target - curr_price) / curr_price) * 100
                        st.write(f"Potentiel : **{pot:+.1f}%**")
                with col_p2:
                    st.metric("📢 Avis Majoritaire", recommendation)

                st.markdown("---")
                st.markdown("**🔍 Vérification des sources :**")
                search_q = f"{current_name} stock analyst ratings bloomberg reuters"
                st.link_button("Lancer une recherche de sources fiables", f"https://www.google.com/search?q={search_q}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            else:
                # LOCK SCREEN
                st.warning("⚠️ Zone Réservée aux Membres Premium")
                st.markdown("""
                <div style="filter: blur(4px); opacity: 0.5;">
                    <h3>Consensus des Banques</h3>
                    <p>Objectif de prix : <b>154.30 $</b></p>
                    <p>Recommandation : <b>STRONG BUY</b></p>
                    <p>Potentiel : <b>+24%</b></p>
                </div>
                """, unsafe_allow_html=True)
                st.error("🔒 Les signaux d'achat et objectifs de cours sont floutés.")
                st.write("Passez Premium pour voir ce que les banques pensent vraiment de cette action.")

    except Exception as e:
        st.error(f"Action non trouvée. Essayez le symbole exact (ex: AAPL, AIR.PA). Erreur : {e}")
