import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DU SITE (Style Investing.com) ---
st.set_page_config(page_title="Global Finance Pro", layout="wide", page_icon="📈")

# --- CSS PERSONNALISÉ POUR LE LOOK "TRADER" ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center;}
    .stTabs [data-baseweb="tab-list"] {gap: 20px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap; background-color: #ffffff; border-radius: 5px;}
    .stTabs [aria-selected="true"] {background-color: #e6f3ff; color: #0068c9; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- DICTIONNAIRE DE MAPPING (NOM -> TICKER) ---
# Pour simuler la recherche par nom (Top 50 Global + CAC40)
POPULAR_STOCKS = {
    "Apple Inc.": "AAPL", "Microsoft": "MSFT", "NVIDIA": "NVDA", "Amazon": "AMZN", "Google (Alphabet)": "GOOGL",
    "Tesla": "TSLA", "Meta (Facebook)": "META", "Berkshire Hathaway": "BRK-B", "TSMC": "TSM",
    "LVMH (Luxe)": "MC.PA", "TotalEnergies": "TTE.PA", "L'Oréal": "OR.PA", "Hermès": "RMS.PA", "Sanofi": "SAN.PA",
    "Airbus": "AIR.PA", "BNP Paribas": "BNP.PA", "AXA": "CS.PA",
    "Volkswagen": "VOW3.DE", "Siemens": "SIE.DE", "SAP": "SAP.DE",
    "Toyota": "TM", "Sony": "SONY", "Samsung Electronics": "005930.KS",
    "Alibaba": "BABA", "Tencent": "TCEHY"
}

# --- FONCTIONS MATHÉMATIQUES AVANCÉES ---

def calculate_dcf(fcf, growth_rate, discount_rate=0.10, terminal_growth=0.025, years=5):
    """Modèle Discounted Cash Flow simplifie (Méthode Banque d'Affaire)"""
    try:
        future_fcf = []
        for i in range(1, years + 1):
            fcf = fcf * (1 + growth_rate)
            future_fcf.append(fcf)
        
        # Valeur Terminale
        terminal_value = future_fcf[-1] * (1 + terminal_growth) / (discount_rate - terminal_growth)
        
        # Actualisation
        dcf_value = 0
        for i in range(years):
            dcf_value += future_fcf[i] / ((1 + discount_rate) ** (i + 1))
        
        dcf_value += terminal_value / ((1 + discount_rate) ** years)
        return dcf_value
    except:
        return 0

def get_analyst_consensus(info):
    """Récupère les données des analystes pro"""
    target = info.get('targetMeanPrice', 0)
    recommendation = info.get('recommendationKey', 'none').upper()
    return target, recommendation

# --- SIDEBAR & AUTHENTIFICATION ---
st.sidebar.title("🔐 Espace Membre")
user_password = st.sidebar.text_input("Clé d'accès (Licence)", type="password")
# LE MOT DE PASSE EST DÉFINI ICI (Change le si tu veux)
IS_PREMIUM = user_password == "PRO2026"

if not IS_PREMIUM:
    st.sidebar.warning("Mode Gratuit restreint.")
    st.sidebar.info("👉 Entrez votre clé pour débloquer les modèles prédictifs (DCF, Graham) et les signaux d'achat.")
    st.sidebar.markdown("[Acheter une licence (19€)](https://gumroad.com)") # Mets ton lien ici
else:
    st.sidebar.success("✅ Mode PRO Activé")

# --- BANDEAU D'INDICES MONDIAUX ---
st.markdown("### 🌍 Marchés en Direct")
col1, col2, col3, col4, col5 = st.columns(5)
indices = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "CAC 40": "^FCHI", "DAX": "^GDAXI", "Nikkei 225": "^N225"}

# Pour l'affichage rapide des indices (optimisation pour ne pas ralentir)
for name, ticker in indices.items():
    # On utilise une astuce pour ne pas charger trop de données au démarrage
    pass 
    # Dans une version complète, on chargerait les deltas ici. 
    # Pour l'instant on affiche juste les noms pour le look "Investing.com"
    
col1.metric("S&P 500", "Live", "+0.5%") # Fake placeholders pour la rapidité de l'exemple
col2.metric("CAC 40", "Live", "-0.2%")
col3.metric("Bitcoin", "Live", "+1.2%")
col4.metric("Gold", "Live", "+0.1%")
col5.metric("Oil (WTI)", "Live", "-0.5%")
st.markdown("---")

# --- RECHERCHE ET SÉLECTION ---
st.header("🔎 Analyseur d'Actions Intelligent")

search_mode = st.radio("Mode de recherche :", ["Liste Rapide (Top 50)", "Symbole Manuel (Expert)"], horizontal=True)

if search_mode == "Liste Rapide (Top 50)":
    stock_name = st.selectbox("Sélectionnez une entreprise :", list(POPULAR_STOCKS.keys()))
    ticker = POPULAR_STOCKS[stock_name]
else:
    ticker = st.text_input("Entrez le symbole (ex: KO pour Coca-Cola, AIR.PA pour Airbus)", "AAPL")

# --- CHARGEMENT DES DONNÉES ---
if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Récupération historique (1 an)
        hist = stock.history(period="1y")
        
        # Titre et Prix
        current_price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
        currency = info.get('currency', 'USD')
        
        st.title(f"{info.get('longName', ticker)} ({ticker})")
        st.write(f"Secteur : **{info.get('sector', 'N/A')}** | Pays : **{info.get('country', 'N/A')}**")
        
        # --- ONGLETS (DASHBOARD) ---
        tab1, tab2, tab3 = st.tabs(["📈 Vue d'ensemble", "📊 Données Financières", "🧠 Prévisions PRO & IA"])

        # --- TAB 1: OVERVIEW ---
        with tab1:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Prix Actuel", f"{current_price} {currency}")
            m2.metric("Variation (52 sem)", f"{((current_price - info.get('fiftyTwoWeekLow', 0))/info.get('fiftyTwoWeekLow', 1))*100:.1f}%")
            m3.metric("Volume Moyen", f"{info.get('averageVolume', 0)/1000000:.1f}M")
            m4.metric("Capitalisation", f"{info.get('marketCap', 0)/1e9:.1f} Mrd")
            
            # Graphique Bougies (Candlestick) avec Plotly (plus pro que line_chart)
            fig = go.Figure(data=[go.Candlestick(x=hist.index,
                            open=hist['Open'], high=hist['High'],
                            low=hist['Low'], close=hist['Close'])])
            fig.update_layout(title="Graphique Interactif", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        # --- TAB 2: FINANCIER ---
        with tab2:
            st.subheader("Les chiffres clés (Bilan)")
            c1, c2, c3 = st.columns(3)
            c1.info(f"PER (Prix/Bénéfice) : **{info.get('trailingPE', 'N/A')}**")
            c2.info(f"Dividende (Rendement) : **{info.get('dividendYield', 0)*100:.2f}%**")
            c3.info(f"Bénéfice par action (EPS) : **{info.get('trailingEps', 'N/A')}**")
            
            st.write("Description de l'entreprise :")
            st.caption(info.get('longBusinessSummary', 'Pas de description disponible.'))

        # --- TAB 3: PRO / GURU / PREVISIONS (PAYWALL) ---
        with tab3:
            st.header("💎 Analyse Expert & Prévisions")
            
            if IS_PREMIUM:
                # DONNÉES AVANCÉES
                st.success("Accès Autorisé : Algorithmes débloqués.")
                
                # 1. ANALYSTE CONSENSUS
                target_price, recom = get_analyst_consensus(info)
                
                # 2. CALCUL GRAHAM
                eps = info.get('trailingEps', 0)
                bv = info.get('bookValue', 0)
                graham_val = np.sqrt(22.5 * eps * bv) if (eps > 0 and bv > 0) else 0
                
                # 3. CALCUL DCF SIMPLIFIÉ
                fcf = info.get('freeCashflow', 0)
                shares = info.get('sharesOutstanding', 1)
                if fcf and shares:
                    fcf_per_share = fcf / shares
                    dcf_val = calculate_dcf(fcf_per_share, 0.08) # Hypothèse 8% croissance
                else:
                    dcf_val = 0

                # --- AFFICHAGE DASHBOARD PRO ---
                col_pro1, col_pro2, col_pro3 = st.columns(3)
                
                with col_pro1:
                    st.markdown("### 🏦 Banques & Analystes")
                    st.metric("Objectif Moyen (1 an)", f"{target_price} {currency}")
                    st.write(f"Conseil : **{recom}**")
                    if target_price > current_price:
                        upside = ((target_price - current_price) / current_price) * 100
                        st.write(f"Potentiel : :green[**+{upside:.1f}%**]")
                    else:
                        st.write("Potentiel : :red[Négatif]")

                with col_pro2:
                    st.markdown("### 👴 Méthode Graham")
                    st.metric("Juste Valeur (Graham)", f"{graham_val:.2f} {currency}")
                    if current_price < graham_val:
                        st.write("Verdict : :green[**SOUS-ÉVALUÉ**]")
                    else:
                        st.write("Verdict : :red[**SUR-ÉVALUÉ**]")

                with col_pro3:
                    st.markdown("### 🧮 Modèle DCF (Cash Flow)")
                    st.metric("Valeur Intrinsèque", f"{dcf_val:.2f} {currency}")
                    st.caption("Basé sur l'actualisation des flux de trésorerie futurs.")

                st.markdown("---")
                st.subheader("🔮 Prévision Algorithmique (Synthèse)")
                
                # Logique de synthèse simple
                signals = 0
                if target_price > current_price * 1.05: signals += 1
                if graham_val > current_price: signals += 1
                if dcf_val > current_price: signals += 1
                
                if signals == 3:
                    st.success("STRONG BUY (ACHAT FORT) : Tous les indicateurs sont au vert. 🚀")
                elif signals == 2:
                    st.info("BUY (ACHAT) : La majorité des modèles sont positifs. 📈")
                elif signals == 1:
                    st.warning("HOLD (CONSERVER) : Signaux contradictoires. 🤔")
                else:
                    st.error("SELL (VENDRE) : L'action semble survalorisée. 📉")
                    
            else:
                # ÉCRAN DE VENTE (SI PAS CONNECTÉ)
                st.error("🔒 ANALYSE PRO BLOQUÉE")
                
                col_lock1, col_lock2 = st.columns([2, 1])
                with col_lock1:
                    st.write("""
                    **Les investisseurs amateurs regardent le prix. Les Pros regardent la valeur.**
                    
                    En débloquant la version PRO, vous obtenez instantanément :
                    * 🎯 **L'objectif de cours** des plus grandes banques (Goldman Sachs, JP Morgan...).
                    * ⚖️ **La Juste Valeur** selon Benjamin Graham (Mentor de Warren Buffett).
                    * 💰 **Le Modèle DCF** : Combien l'entreprise vaut réellement selon son cash.
                    * 🚦 **La synthèse Achat/Vente** claire et nette.
                    """)
                with col_lock2:
                    st.markdown("### Seulement 19€ / mois")
                    st.button("🔓 DÉBLOQUER MAINTENANT") # Ici tu mettras ton lien Stripe
                    st.caption("Entrez votre code licence dans le menu à gauche.")

    except Exception as e:
        st.error(f"Action non trouvée ou erreur de données : {e}")
