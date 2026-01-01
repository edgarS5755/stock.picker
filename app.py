import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="FHi - Stock Picker", layout="wide")

# --- FONCTIONS ---
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # On force le téléchargement des données pour vérifier si l'action existe
        hist = stock.history(period="1y")
        if hist.empty:
            return None, None
        
        # On essaie de récupérer les infos, sinon on met des valeurs par défaut
        info = stock.info
        return info, hist
    except:
        return None, None

def graham_valuation(eps, book_value):
    try:
        if eps is None or book_value is None or eps <= 0 or book_value <= 0:
            return 0
        return np.sqrt(22.5 * eps * book_value)
    except:
        return 0

# --- SIDEBAR ---
st.sidebar.title("💰 AlphaValue Pro")
ticker = st.sidebar.text_input("Symbole (ex: AAPL, MSFT, ^CAC40)", "AAPL")
premium_mode = st.sidebar.checkbox("Mode Premium (Simulation)")

# --- MAIN ---
st.title(f"Analyse : {ticker.upper()}")

info, hist = get_stock_data(ticker)

if info is None or hist is None:
    st.error(f"Erreur : Impossible de récupérer les données pour '{ticker}'. Vérifiez le symbole (ex: pour LVMH, essayez 'MC.PA').")
else:
    # Récupération sécurisée des prix
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
    
    # 1. KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("Prix Actuel", f"${current_price:.2f}")
    col2.metric("PE Ratio", f"{info.get('trailingPE', 'N/A')}")
    mk_cap = info.get('marketCap', 0)
    col3.metric("Capitalisation", f"${mk_cap:,.0f}" if mk_cap else "N/A")

    # 2. GRAPHIQUE
    st.line_chart(hist['Close'])

    # 3. ANALYSE
    st.markdown("---")
    if premium_mode:
        st.header("💎 Analyse Graham & Prévisions")
        
        eps = info.get('trailingEps', 0)
        bv = info.get('bookValue', 0)
        graham = graham_valuation(eps, bv)
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Prix Juste (Graham)")
            if graham > 0:
                st.metric("Valeur Intrinsèque", f"${graham:.2f}")
                if current_price < graham:
                    st.success("✅ ACTION SOUS-ÉVALUÉE (Bonne affaire)")
                else:
                    st.error("⚠️ ACTION SUR-ÉVALUÉE (Trop cher)")
            else:
                st.warning("Données insuffisantes pour le calcul Graham (EPS négatif).")
        
        with c2:
            st.subheader("Prévision IA (1 an)")
            st.info("L'algorithme de prévision est réservé aux abonnés payants.")
            
    else:
        st.info("🔒 Activez le mode Premium pour voir la valorisation de Benjamin Graham.")

st.markdown("---")
st.caption("AlphaValue - Données Yahoo Finance.")
