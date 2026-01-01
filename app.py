import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DU SITE (Style FHi) ---
st.set_page_config(page_title="FHi - Financial Health Index", layout="wide", page_icon="📈")

# --- CSS PERSONNALISÉ POUR LE LOOK "TRADER" ET LOGO ---
st.markdown("""
<style>
    /* Style des cartes de métriques */
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center;}
    /* Style des onglets */
    .stTabs [data-baseweb="tab-list"] {gap: 20px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #ffffff; border-radius: 5px;}
    .stTabs [aria-selected="true"] {background-color: #e6f3ff; color: #0068c9; font-weight: bold;}
    /* Style des news */
    .news-item {padding: 10px; border-bottom: 1px solid #eee;}
    .news-title {font-weight: bold; color: #0068c9; text-decoration: none;}
    .news-source {font-size: 0.8em; color: #666;}
    /* Style du Logo en Sidebar (Fondu et taille) */
    [data-testid="stSidebar"] img {
        opacity: 0.8; /* Effet de transparence pour le fondu */
        margin-bottom: -20px; /* Remonte le logo vers le titre */
    }
</style>
""", unsafe_allow_html=True)

# --- DICTIONNAIRE DE MAPPING (NOM -> TICKER) ---
POPULAR_STOCKS = {
    "Apple Inc.": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "Amazon": "AMZN", "Google (Alphabet)": "GOOGL",
    "Tesla": "TSLA", "Meta (Facebook)": "META", "Berkshire Hathaway": "BRK-B", "TSMC": "TSM",
    "LVMH (Luxe)": "MC.PA", "TotalEnergies": "TTE.PA", "L'Oréal": "OR.PA", "Hermès": "RMS.PA", "Sanofi": "SAN.PA",
    "Airbus": "AIR.PA", "BNP Paribas": "BNP.PA", "AXA": "CS.PA",
    "Volkswagen": "VOW3.DE", "Siemens": "SIE.DE", "SAP": "SAP.DE",
    "Toyota": "TM", "Sony": "SONY", "Samsung Electronics": "005930.KS",
    "Alibaba": "BABA", "Tencent": "TCEHY"
}

# --- FONCTIONS AVEC MISE EN CACHE (ANTI RATE-LIMIT) ---

# On garde les données principales en mémoire pendant 2 heures (7200 secondes)
@st.cache_data(ttl=7200, show_spinner=False)
def get_stock_data_cached(ticker_symbol):
    """Récupère infos et historique avec cache"""
    stock = yf.Ticker(ticker_symbol)
    # On force le téléchargement des données essentielles pour éviter les bugs de yfinance
    info = stock.fast_info 
    # On complète avec le 'info' standard si besoin, mais fast_info est plus stable
    full_info = stock.info 
    hist = stock.history(period="1y")
    return full_info, hist

# On garde les news en mémoire pendant 3 heures
@st.cache_data(ttl=10800, show_spinner=False)
def get_company_news_cached(ticker_symbol):
    """Récupère les dernières actualités financières avec cache"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        return news[:5]
    except Exception:
        return []

def get_analyst_consensus(info):
    """Récupère les données des analystes pro"""
    target = info.get('targetMeanPrice', 0)
    recommendation = info.get('recommendationKey', 'none').upper()
    return target, recommendation


# --- SIDEBAR & LOGO ---
with st.sidebar:
    try:
        # Logo en petit (width=100) et en haut
        st.image("image_2.png", width=120) 
    except:
        st.write("FHi")

    st.title("🔐 Espace Membre")
    user_password = st.text_input("Clé d'accès (Licence)", type="password")
    # LE MOT DE PASSE EST DÉFINI ICI
    IS_PREMIUM = user_password == "PRO2026"

    if not IS_PREMIUM:
        st.warning("Mode Gratuit.")
        st.info("👉 Entrez votre clé pour débloquer l'analyse des banques.")
        st.markdown("[Acheter une licence (19€)](https://gumroad.com)")
    else:
        st.success("✅ Mode PRO Activé")

# --- PAGE PRINCIPALE ---

# --- BANDEAU D'INDICES MONDIAUX ---
st.markdown("### 🌍 Marchés en Direct")
col1, col2, col3, col4, col5 = st.columns(5)
# Valeurs statiques pour éviter de surcharger l'API au démarrage
col1.metric("S&P 500", "Top US", "---") 
col2.metric("CAC 40", "France", "---")
col3.metric("Bitcoin", "Crypto", "---")
col4.metric("Gold", "Matières", "---")
col5.metric("Oil (WTI)", "Énergie", "---")
st.markdown("---")

# --- RECHERCHE ET SÉLECTION ---
st.header("🔎 Analyseur d'Actions FHi")

search_mode = st.radio("Mode de recherche :", ["Liste Rapide (Top 50)", "Symbole Manuel (Expert)"], horizontal=True)

if search_mode == "Liste Rapide (Top 50)":
    stock_name = st.selectbox("Sélectionnez une entreprise :", list(POPULAR_STOCKS.keys()))
    ticker = POPULAR_STOCKS[stock_name]
else:
    ticker = st.text_input("Entrez le symbole (ex: KO pour Coca-Cola, AIR.PA pour Airbus)", "AAPL")

# --- CHARGEMENT DES DONNÉES CENTRALISÉ ---
if ticker:
    try:
        # Utilisation de la fonction en CACHE
        with st.spinner('Analyse FHi en cours...'):
            info, hist = get_stock_data_cached(ticker)
        
        # Titre et Prix
        current_price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        currency = info.get('currency', 'USD')
        long_name = info.get('longName', ticker)
        
        st.subheader(f"{long_name} ({ticker})")
        st.write(f"Secteur : **{info.get('sector', 'N/A')}** | Pays : **{info.get('country', 'N/A')}**")
        
        # --- ONGLETS (DASHBOARD) ---
        tab1, tab2, tab3 = st.tabs(["📈 Vue d'ensemble", "📊 Données Financières", "💎 Analyse Banques (PRO)"])

        # --- TAB 1: OVERVIEW ---
        with tab1:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Prix Actuel", f"{current_price} {currency}")
            
            low_52 = info.get('fiftyTwoWeekLow', 1)
            if low_52 and current_price:
                 var_52 = ((current_price - low_52)/low_52)*100
                 m2.metric("Variation (52 sem)", f"{var_52:.1f}%")
            else:
                 m2.metric("Variation (52 sem)", "N/A")

            m3.metric("Volume Moyen", f"{info.get('averageVolume', 0)/1000000:.1f}M")
            m4.metric("Capitalisation", f"{info.get('marketCap', 0)/1e9:.1f} Mrd")
            
            # Graphique Bougies (Candlestick) avec Plotly
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'], high=hist['High'],
                            low=hist['Low'], close=hist['Close'])])
            fig.update_layout(title="Graphique Interactif (1 An)", xaxis_rangeslider_visible=False, height=500)
            st.plotly_chart(fig, use_container_width=True)

        # --- TAB 2: FINANCIER ---
        with tab2:
            st.subheader("Les chiffres clés (Bilan)")
            c1, c2, c3 = st.columns(3)
            c1.info(f"PER (Prix/Bénéfice) : **{info.get('trailingPE', 'N/A')}**")
            
            div_yield = info.get('dividendYield')
            if div_yield:
                 c2.info(f"Dividende (Rendement) : **{div_yield*100:.2f}%**")
            else:
                 c2.info("Dividende : Aucun")

            c3.info(f"Bénéfice par action (EPS) : **{info.get('trailingEps', 'N/A')}**")
            
            st.write("Description de l'entreprise :")
            st.caption(info.get('longBusinessSummary', 'Pas de description disponible.'))

        # --- TAB 3: PRO / BANQUES (PAYWALL) ---
        with tab3:
            st.header("💎 Consensus des Analystes")
            
            if IS_PREMIUM:
                # DONNÉES AVANCÉES
                st.success("Accès Autorisé : Données bancaires débloquées.")
                
                # 1. ANALYSTE CONSENSUS
                target_price, recom = get_analyst_consensus(info)
                
                # --- AFFICHAGE DASHBOARD PRO ---
                st.markdown("### 🏦 Banques & Institutions")
                col_pro1, col_pro2 = st.columns(2)

                with col_pro1:
                    if target_price and current_price:
                        st.metric("Objectif de Cours Moyen (1 an)", f"{target_price} {currency}")
                        if target_price > current_price:
                            upside = ((target_price - current_price) / current_price) * 100
                            st.write(f"Potentiel estimé : :green[**+{upside:.1f}%**]")
                        else:
                            st.write("Potentiel estimé : :red[Négatif]")
                    else:
                         st.write("Données d'objectif de cours indisponibles.")
                
                with col_pro2:
                    st.write(f"Recommandation Majoritaire :")
                    st.header(f"**{recom.replace('_', ' ')}**")

                st.markdown("---")
                st.subheader("Synthèse FHi")
                
                # Logique de synthèse simple basée sur les analystes
                if target_price and current_price:
                    if "BUY" in recom and target_price > current_price * 1.10:
                        st.success("STRONG BUY (ACHAT FORT) : Les banques sont très optimistes. 🚀")
                    elif "BUY" in recom or target_price > current_price:
                        st.info("BUY (ACHAT) : Le consensus est positif. 📈")
                    elif "HOLD" in recom:
                        st.warning("HOLD (CONSERVER) : Les avis sont neutres. 🤔")
                    else:
                        st.error("SELL (VENDRE) : Les analystes recommandent la prudence ou la vente. 📉")
                else:
                     st.warning("Synthèse impossible : données insuffisantes.")
                    
            else:
                # ÉCRAN DE VENTE (SI PAS CONNECTÉ)
                st.error("🔒 ANALYSE PRO BLOQUÉE")
                
                col_lock1, col_lock2 = st.columns([2, 1])
                with col_lock1:
                    st.write("""
                    **Ne tradez plus seul. Suivez l'argent intelligent.**
                    
                    En débloquant la version PRO de FHi, vous voyez instantanément :
                    * 🎯 **L'objectif de cours** précis des plus grandes banques d'affaires (Goldman Sachs, JP Morgan...).
                    * ⚖️ **La Recommandation Officielle** du consensus (Achat, Vente, Conserver).
                    * 🚦 **La synthèse FHi** claire et nette pour prendre votre décision.
                    """)
                with col_lock2:
                    st.markdown("### Seulement 19€ / mois")
                    st.button("🔓 DÉBLOQUER MAINTENANT") 
                    st.caption("Entrez votre code licence dans le menu à gauche.")
        
        # --- SECTION ACTUALITÉS (EN DESSOUS DES ONGLETS) ---
        st.markdown("---")
        st.header("📰 Actualités Financières Récentes")
        
        # Utilisation de la fonction NEWS en CACHE
        news_items = get_company_news_cached(ticker)
        
        if news_items:
            st.write(f"Dernières nouvelles concernant **{long_name}**.")
            for item in news_items:
                # Convertir le timestamp en date lisible
                pub_date = datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%d/%m/%Y %H:%M')
                publisher = item.get('publisher', 'Source Inconnue')
                title = item.get('title', 'Pas de titre')
                link = item.get('link', '#')
                
                st.markdown(f"""
                <div class="news-item">
                    <a href="{link}" target="_blank" class="news-title">{title}</a>
                    <br>
                    <span class="news-source">Source : {publisher} | Date : {pub_date}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("Aucune actualité récente disponible ou erreur de chargement.")

    except Exception as e:
        st.warning(f"Erreur lors de la récupération des données. Si le problème persiste, Yahoo Finance limite peut-être les requêtes temporairement. Erreur : {e}")

# Assure-toi que image_2.png est bien uploadé sur GitHub
