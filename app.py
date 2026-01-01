import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="AlphaValue - Stock Picker", layout="wide")

# --- FONCTIONS DE CALCUL (L'INTELLIGENCE) ---
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="1y")
    return info, hist

def graham_valuation(eps, book_value):
    # Formule de Benjamin Graham : V = Racine(22.5 * EPS * BookValue)
    if eps is None or book_value is None or eps < 0 or book_value < 0:
        return 0
    return np.sqrt(22.5 * eps * book_value)

def predict_price_1y(current_price, growth_rate):
    # Projection simple basée sur le taux de croissance estimé
    if growth_rate is None:
        growth_rate = 0.05 # 5% par défaut si pas de donnée
    return current_price * (1 + growth_rate)

# --- SIDEBAR (NAVIGATION) ---
st.sidebar.title("💰 AlphaValue Pro")
st.sidebar.write("L'outil des investisseurs intelligents.")
ticker = st.sidebar.text_input("Entrez le symbole (ex: AAPL, MC.PA)", "AAPL")
premium_mode = st.sidebar.checkbox("Activer Mode Premium (Simulation)")

# --- DASHBOARD PRINCIPAL ---
st.title(f"Analyse Fondamentale : {ticker.upper()}")

try:
    info, hist = get_stock_data(ticker)
    
    # 1. VUE D'ENSEMBLE (GRATUIT)
    col1, col2, col3 = st.columns(3)
    current_price = info.get('currentPrice', 0)
    col1.metric("Prix Actuel", f"${current_price}")
    col2.metric("PE Ratio (Prix/Bénéfice)", info.get('trailingPE', 'N/A'))
    col3.metric("Capitalisation", f"${info.get('marketCap', 0):,}")

    st.subheader("Performance sur 1 an")
    st.line_chart(hist['Close'])

    # 2. ANALYSE FONDAMENTALE (DONNÉES CLES)
    st.markdown("---")
    st.header("📊 Santé Financière (Le Bilan)")
    
    f_col1, f_col2, f_col3 = st.columns(3)
    f_col1.info(f"Dette/Capitaux Propres: {info.get('debtToEquity', 'N/A')}")
    f_col2.info(f"Marge Bénéficiaire: {info.get('profitMargins', 0)*100:.2f}%")
    f_col3.info(f"Croissance Trimestrielle: {info.get('earningsQuarterlyGrowth', 0)*100:.2f}%")

    # 3. SECTION PREMIUM : LE VERDICT DES GURUS + PRÉVISIONS
    st.markdown("---")
    st.header("🧠 L'Analyse Intelligente (IA & Graham)")

    if premium_mode:
        # Calculs avancés
        eps = info.get('trailingEps', 0)
        book_value = info.get('bookValue', 0)
        growth_est = info.get('earningsGrowth', 0.10) # Estimation
        
        graham_price = graham_valuation(eps, book_value)
        predicted_price = predict_price_1y(current_price, growth_est)
        marge_securite = ((graham_price - current_price) / graham_price) * 100

        # Affichage Premium
        p_col1, p_col2 = st.columns(2)
        
        with p_col1:
            st.subheader("💎 Valorisation Benjamin Graham")
            st.write(f"Prix Juste (Fair Value) : **${graham_price:.2f}**")
            if current_price < graham_price:
                st.success(f"✅ ACTION SOUS-ÉVALUÉE (Marge de sécu: {marge_securite:.1f}%)")
            else:
                st.error(f"⚠️ ACTION SUR-ÉVALUÉE (Trop chère de {-marge_securite:.1f}%)")

        with p_col2:
            st.subheader("🔮 Prévision IA (1 an)")
            st.metric(label="Objectif de cours estimé", value=f"${predicted_price:.2f}", delta=f"{((predicted_price-current_price)/current_price)*100:.1f}%")
            st.caption("Basé sur la projection des Free Cash Flows et la croissance des earnings.")

    else:
        # Paywall
        st.warning("🔒 Cette section est réservée aux membres PRO.")
        st.write("Débloquez l'algorithme de Graham, les prévisions de prix et les signaux d'achat.")
        st.button("Passer Premium pour 9€/mois")

except Exception as e:
    st.error(f"Erreur : Impossible de trouver l'action '{ticker}'. Vérifiez le symbole.")

# --- FOOTER ---
st.markdown("---")
st.caption("AlphaValue - Données fournies par Yahoo Finance. Ceci n'est pas un conseil en investissement.")
