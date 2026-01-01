import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DU SITE ---
st.set_page_config(page_title="FHi - Terminal", layout="wide", page_icon="📈")

# --- CSS AVANCÉ (Navigation & Lisibilité) ---
st.markdown("""
<style>
    /* Correction de la lisibilité des ONGLETS (Tabs) */
    button[data-baseweb="tab"] {
        background-color: #f0f2f6 !important;
        color: #31333F !important; /* Texte Noir */
        font-weight: 600 !important;
        border-radius: 5px !important;
        margin-right: 5px !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0068c9 !important; /* Bleu FHi */
        color: white !important;
    }
    
    /* Style des cartes et boutons */
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center;}
    .stButton>button {width: 100%; border-radius: 5px;}
    
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

# --- DONNÉES ET CATÉGORIES ---
# On structure les données pour la navigation verticale
MARKET_DATA = {
    "🌍 Indices Mondiaux": {
        "S&P 500": "^GSPC", "Nasdaq 100": "^IXIC", "CAC 40": "^FCHI", 
        "DAX (Allemagne)": "^GDAXI", "Nikkei 225 (Japon)": "^N225", "VIX (Peur)": "^VIX"
    },
    "🏢 Grandes Actions": {
        "Apple": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "Tesla": "TSLA",
        "LVMH": "MC.PA", "TotalEnergies": "TTE.PA", "Airbus": "AIR.PA", "Sanofi": "SAN.PA"
    },
    "₿ Cryptomonnaies": {
        "Bitcoin USD": "BTC-USD", "Ethereum USD": "ETH-USD", "Solana": "SOL-USD", 
        "XRP": "XRP-USD", "Binance Coin": "BNB-USD"
    },
    "💱 Forex (Devises)": {
        "Euro / Dollar": "EURUSD=X", "Dollar / Yen": "JPY=X", "Livres / Dollar": "GBPUSD=X",
        "Euro / Suisse": "EURCHF=X"
    },
    "🛢️ Matières Premières": {
        "Or (Gold)": "GC=F", "Pétrole (WTI)": "CL=F", "Argent (Silver)": "SI=F", 
        "Gaz Naturel": "NG=F", "Cuivre": "HG=F"
    },
    "📊 ETFs Populaires": {
        "S&P 500 ETF (VOO)": "VOO", "Nasdaq ETF (QQQ)": "QQQ", 
        "World ETF (VT)": "VT", "Gold ETF (GLD)": "GLD"
    }
}

# --- GESTION DE L'ÉTAT (POUR LA NAVIGATION FLUIDE) ---
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = "AAPL" # Par défaut
if 'selected_name' not in st.session_state:
    st.session_state.selected_name = "Apple"

def set_ticker(name, ticker):
    """Fonction déclenchée au clic sur un actif"""
    st.session_state.selected_ticker = ticker
    st.session_state.selected_name = name

# --- FONCTIONS CACHÉES (PERFORMANCE) ---
@st.cache_data(ttl=3600)
def get_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    return info, hist

@st.cache_data(ttl=3600)
def get_news(ticker):
    stock = yf.Ticker(ticker)
    return stock.news[:4]

# --- SIDEBAR (NAVIGATION VERTICALE) ---
with st.sidebar:
    try:
        st.image("image_2.png", width=140)
    except:
        st.header("FHi")
    
    st.markdown("### 🧭 Navigation Marchés")
    
    # Menu principal
    category = st.radio("Classe d'actifs", list(MARKET_DATA.keys()))
    
    st.markdown("---")
    st.markdown("### 🔐 Compte Pro")
    pwd = st.text_input("Code Licence", type="password")
    IS_PREMIUM = pwd == "PRO2026"
    
    if IS_PREMIUM:
        st.success("Mode TRADER Actif")
    else:
        st.info("🔒 Mode Standard")
        st.caption("Entrez le code pour voir les objectifs de prix des banques.")

# --- PAGE PRINCIPALE ---

# 1. ZONE DE SÉLECTION RAPIDE (DASHBOARD CATEGORIE)
st.title(f"Marché : {category}")

# Affichage des actifs de la catégorie choisie sous forme de grille
cols = st.columns(4)
assets_list = list(MARKET_DATA[category].items())

for i, (name, ticker_sym) in enumerate(assets_list):
    # On distribue les boutons dans les colonnes
    col = cols[i % 4]
    if col.button(f"🔎 {name}", key=f"btn_{ticker_sym}"):
        set_ticker(name, ticker_sym)

st.markdown("---")

# 2. ZONE DE DÉTAIL (L'ACTIF SÉLECTIONNÉ)
current_ticker = st.session_state.selected_ticker
current_name = st.session_state.selected_name

if current_ticker:
    try:
        info, hist = get_data(current_ticker)
        curr_price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        currency = info.get('currency', 'USD')
        
        # En-tête du produit
        h1, h2 = st.columns([3, 1])
        with h1:
            st.header(f"{current_name} ({current_ticker})")
            st.caption(f"Secteur: {info.get('sector', 'N/A')} | Pays: {info.get('country', 'N/A')}")
        with h2:
            st.metric("Prix Actuel", f"{curr_price} {currency}")

        # --- LES ONGLETS PRINCIPAUX ---
        tab_view, tab_financials, tab_pro = st.tabs(["📈 Graphique & Vue", "💰 Données Financières", "🏦 Consensus Banques (PRO)"])

        # ONGLET 1 : GRAPHIQUE
        with tab_view:
            # Graphique interactif
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'], high=hist['High'],
                            low=hist['Low'], close=hist['Close'])])
            fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
            # Mini Stats
            c1, c2, c3 = st.columns(3)
            c1.info(f"Plus Haut (52s): {info.get('fiftyTwoWeekHigh', 'N/A')}")
            c2.info(f"Plus Bas (52s): {info.get('fiftyTwoWeekLow', 'N/A')}")
            c3.info(f"Volume Moyen: {info.get('averageVolume', 0)/1e6:.1f} M")

        # ONGLET 2 : FINANCIER
        with tab_financials:
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.subheader("Bilan")
                st.write(f"**Capitalisation :** {info.get('marketCap', 0)/1e9:.2f} Mrd {currency}")
                st.write(f"**Revenus (TTM) :** {info.get('totalRevenue', 0)/1e9:.2f} Mrd {currency}")
                st.write(f"**Bénéfice (Profit) :** {info.get('grossProfits', 0)/1e9:.2f} Mrd {currency}")
            with col_f2:
                st.subheader("Ratios")
                st.write(f"**PER (Price/Earnings) :** {info.get('trailingPE', 'N/A')}")
                st.write(f"**P/B (Price/Book) :** {info.get('priceToBook', 'N/A')}")
                st.write(f"**Dividende :** {info.get('dividendYield', 0)*100:.2f}%")

        # ONGLET 3 : PRO / BANQUES
        with tab_pro:
            st.subheader("🕵️‍♂️ Analyse des Institutionnels")
            
            if IS_PREMIUM:
                # Récupération données analystes
                target = info.get('targetMeanPrice')
                recommendation = info.get('recommendationKey', 'inconnu').upper().replace("_", " ")
                num_analysts = info.get('numberOfAnalystOpinions', 0)
                
                # Jauge de Consensus
                c_pro1, c_pro2 = st.columns(2)
                with c_pro1:
                    st.metric("Objectif de Prix Moyen (Consensus)", f"{target} {currency}")
                    if target and curr_price:
                        upside = ((target - curr_price) / curr_price) * 100
                        color = "green" if upside > 0 else "red"
                        st.markdown(f"Potentiel : :{color}[**{upside:+.2f}%**]")
                    
                with c_pro2:
                    st.metric("Recommandation", recommendation)
                    st.caption(f"Basé sur {num_analysts} analystes professionnels.")

                st.markdown("---")
                st.markdown("#### 🔗 Sources & Rapports Externes")
                st.write("Les données ci-dessus sont agrégées (Moyenne des notes Goldman Sachs, JP Morgan, Morgan Stanley...).")
                
                # Liens dynamiques pour la fiabilité
                col_link1, col_link2 = st.columns(2)
                with col_link1:
                    # Lien vers Google News recherche spécifique
                    search_query = f"{current_name} stock analyst rating"
                    st.link_button("📰 Lire les articles récents (Presse)", f"https://www.google.com/search?q={search_query}&tbm=nws")
                with col_link2:
                    # Lien vers Yahoo Analysis
                    st.link_button("📊 Détails Consensus (Yahoo Finance)", f"https://finance.yahoo.com/quote/{current_ticker}/analysis")

            else:
                st.error("🔒 Section Réservée aux membres FHi PRO")
                st.write("Accédez aux objectifs de prix des banques et aux liens vers les rapports d'analystes.")

        # --- ACTUALITÉS EN BAS DE PAGE ---
        st.markdown("---")
        st.subheader(f"Dernières Infos : {current_name}")
        news = get_news(current_ticker)
        if news:
            for n in news:
                title = n.get('title')
                link = n.get('link')
                publisher = n.get('publisher')
                st.markdown(f"- **[{title}]({link})** _(Source: {publisher})_")
        else:
            st.caption("Pas d'actualités récentes disponibles.")

    except Exception as e:
        st.error(f"Erreur de chargement pour {current_ticker}. Essayez un autre actif. ({e})")
