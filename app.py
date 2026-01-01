import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="FHi Stock Picker", layout="wide", page_icon="📈", initial_sidebar_state="collapsed")

# --- 2. CSS "DARK PICKER" (Cartes & Couleurs) ---
st.markdown("""
<style>
    /* RESET */
    .stApp { background-color: #050505; color: #e0e0e0; font-family: 'Helvetica Neue', sans-serif; }
    
    /* NAVIGATION BAR */
    .nav-bar {
        position: fixed; top: 0; left: 0; width: 100%; height: 60px;
        background: rgba(20, 20, 20, 0.9); backdrop-filter: blur(10px);
        border-bottom: 1px solid #333; z-index: 999;
        display: flex; align-items: center; padding: 0 20px;
    }
    
    /* CARTES ACTIONS (STOCK PICKING) */
    .stock-card {
        background-color: #111; border: 1px solid #222; border-radius: 10px;
        padding: 15px; text-align: center; margin-bottom: 10px;
        transition: transform 0.2s, border-color 0.2s;
    }
    .stock-card:hover { border-color: #2962ff; transform: translateY(-2px); }
    
    /* COULEURS PRIX */
    .price-big { font-size: 1.2rem; font-weight: bold; color: #fff; margin: 5px 0; }
    .var-green { color: #00e676; font-weight: 600; font-size: 0.9rem; }
    .var-red { color: #ff1744; font-weight: 600; font-size: 0.9rem; }
    .ticker-name { color: #888; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    
    /* BOUTONS STREAMLIT CUSTOM */
    div.stButton > button {
        width: 100%; border-radius: 6px; background-color: #1e1e1e; color: #fff; border: 1px solid #333;
    }
    div.stButton > button:hover { border-color: #fff; color: #fff; }

    /* ONGLETS */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #333; gap: 15px; }
    .stTabs [aria-selected="true"] { color: #2962ff !important; border-bottom-color: #2962ff !important; }
    
    /* HIDE SIDEBAR */
    [data-testid="stSidebar"] { display: none; }
    
    /* NEWS */
    .news-item { padding: 10px 0; border-bottom: 1px solid #222; }
    .news-title { color: #fff; text-decoration: none; font-weight: 600; }
    .news-source { color: #666; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE MANAGEMENT ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'ticker' not in st.session_state: st.session_state.ticker = None

def navigate(to, symbol=None):
    st.session_state.view = to
    if symbol: st.session_state.ticker = symbol

# --- 4. DONNÉES DE STOCK PICKING (NICHES) ---
NICHES = {
    "🧠 IA & Data": ["PLTR", "NVDA", "SNOW", "DDOG", "AMD"],
    "🛡️ Cybersecurité": ["PANW", "CRWD", "FTNT", "NET"],
    "☢️ Énergie & Uranium": ["CCJ", "URA", "NEE", "ENPH", "FSLR"],
    "💎 Luxe & Rareté": ["MC.PA", "RMS.PA", "RACE.MI", "CDI.PA"],
    "💊 BioTech (Risqué)": ["CRSP", "MRNA", "BNTX", "VLA.PA"]
}

# --- 5. FONCTIONS DATA (ROBUSTES) ---
@st.cache_data(ttl=300)
def get_quote_safe(symbol):
    """Récupère prix et variation sans planter"""
    try:
        t = yf.Ticker(symbol)
        # Fast info est plus rapide et stable
        price = t.fast_info.last_price
        prev = t.fast_info.previous_close
        if price and prev:
            change = ((price - prev) / prev) * 100
            return price, change
        return 0.0, 0.0
    except:
        return 0.0, 0.0

@st.cache_data(ttl=1800)
def get_full_details(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.info, t.history(period="1y"), t.news
    except: return None, None, None

def bot_brain(query, info, symbol):
    """
    Le Cerveau du Bot: Analyse les vrais chiffres pour répondre.
    """
    q = query.lower()
    name = info.get('shortName', symbol)
    summary = info.get('longBusinessSummary', '')
    
    # 1. ANALYSE FONDAMENTALE (SI DEMANDÉ AVIS)
    if any(x in q for x in ["avis", "acheter", "bon coup", "investir", "analyse"]):
        # Récupération des ratios clés
        target = info.get('targetMeanPrice')
        current = info.get('currentPrice')
        peg = info.get('pegRatio') # Price/Earnings-to-Growth (Top indicateur)
        margins = info.get('profitMargins', 0)
        
        analysis = f"**Analyse FHi pour {name} :**\n\n"
        
        # Logique Valorisation
        if target and current:
            upside = ((target - current) / current) * 100
            analysis += f"🎯 **Potentiel :** Les analystes visent {target} ({upside:+.1f}%).\n"
        
        # Logique Rentabilité
        if margins > 0.20:
            analysis += f"✅ **Rentabilité :** Excellente marge nette de {margins*100:.1f}% (Cash Machine).\n"
        elif margins < 0:
            analysis += f"⚠️ **Attention :** L'entreprise n'est pas encore rentable (Marge {margins*100:.1f}%).\n"
            
        # Logique Prix (PEG)
        if peg and peg < 1:
            analysis += f"💎 **Valorisation :** L'action est sous-évaluée par rapport à sa croissance (PEG < 1).\n"
        elif peg and peg > 3:
            analysis += f"🔥 **Valorisation :** L'action est chère (PEG élevé), le marché attend beaucoup.\n"
            
        return analysis + "\n*Ceci est une aide à la décision, pas un conseil financier.*"

    # 2. HISTOIRE & ACTIVITÉ
    if any(x in q for x in ["histoire", "fait quoi", "activite", "business"]):
        return f"**Activité de {name} :**\n\n{summary[:600]}... (Traduit de Yahoo Finance)"

    # 3. RISQUE
    if "risque" in q:
        beta = info.get('beta', 1)
        debt = info.get('debtToEquity', 0)
        
        risk_msg = f"**Profil de Risque :**\n\n"
        if beta > 1.5: risk_msg += f"🌊 **Volatilité :** Très élevée (Beta {beta}). Ça bouge fort !\n"
        else: risk_msg += f"🛡️ **Volatilité :** Faible/Moyenne (Beta {beta}). Plutôt stable.\n"
        
        if debt > 200: risk_msg += f"⚠️ **Dette :** Attention, niveau d'endettement élevé ({debt}%).\n"
        
        return risk_msg

    return f"Je suis l'assistant FHi spécialisé sur {name}. Demandez-moi une **analyse**, son **histoire** ou son **niveau de risque**."

# --- 6. NAVIGATION BAR (SIMULÉE) ---
c1, c2, c3 = st.columns([1, 4, 1])
with c1:
    if st.button("🏠 FHi Accueil"): navigate('home')
with c2:
    # Barre de recherche globale
    search = st.text_input("Recherche (Symbole)", label_visibility="collapsed", placeholder="Ex: TSLA, LVMH...").upper()
    if search:
        # Mapping manuel rapide pour les noms courants
        map_fix = {"LVMH": "MC.PA", "TOTAL": "TTE.PA", "APPLE": "AAPL"}
        target = map_fix.get(search, search)
        navigate('terminal', target)
        st.rerun()
with c3:
    if st.session_state.ticker:
        if st.button(f"📊 {st.session_state.ticker}"): navigate('terminal')

st.markdown("---")

# --- 7. VUE ACCUEIL (STOCK PICKING) ---
if st.session_state.view == 'home':
    st.title("Sélection de Pépites par Secteur")
    st.caption("FHi Stock Picker : Identifiez les opportunités de marché.")

    # Onglets des Niches
    tabs = st.tabs(list(NICHES.keys()))
    
    for i, (niche_name, tickers) in enumerate(NICHES.items()):
        with tabs[i]:
            # Grille de 4 colonnes
            cols = st.columns(4)
            for j, t in enumerate(tickers):
                col = cols[j % 4]
                
                # Récupération Data Rapide
                p, var = get_quote_safe(t)
                
                # Définition Couleur et Signe
                color_class = "var-green" if var >= 0 else "var-red"
                sign = "+" if var >= 0 else ""
                
                # Affichage Carte dans la Colonne
                with col:
                    with st.container(border=True): # Cadre visuel
                        st.markdown(f"<div class='ticker-name'>{t}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='price-big'>{p:,.2f}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='{color_class}'>{sign}{var:.2f}%</div>", unsafe_allow_html=True)
                        
                        # Bouton d'action
                        if st.button("Analyser 🔎", key=f"btn_{t}"):
                            navigate('terminal', t)
                            st.rerun()

    # Section Actualités (Correction du bug)
    st.markdown("---")
    st.subheader("Dernières Actualités Générales")
    
    # On prend le SP500 comme proxy pour les news globales
    _, _, news_items = get_full_details("^GSPC")
    
    if news_items:
        # On affiche 3 colonnes de news
        news_cols = st.columns(3)
        count = 0
        for item in news_items:
            # Sécurité : on vérifie que le titre et le lien existent
            title = item.get('title')
            link = item.get('link')
            pub = item.get('publisher', 'Presse')
            
            # Gestion Image sécurisée
            img_url = "https://via.placeholder.com/300x150?text=FHi+News"
            try:
                if 'thumbnail' in item and 'resolutions' in item['thumbnail']:
                    img_url = item['thumbnail']['resolutions'][0]['url']
            except: pass

            if title and link:
                with news_cols[count % 3]:
                    st.image(img_url, use_container_width=True)
                    st.markdown(f"**[{title}]({link})**")
                    st.caption(f"Source : {pub}")
                    st.markdown("---")
                count += 1
                if count >= 6: break # Max 6 news

# --- 8. VUE TERMINAL (FICHE ACTION) ---
elif st.session_state.view == 'terminal':
    sym = st.session_state.ticker
    
    if not sym:
        st.warning("Veuillez sélectionner une action.")
        st.stop()

    info, hist, news = get_full_details(sym)
    
    if info:
        # En-tête Action
        c1, c2 = st.columns([3, 1])
        with c1:
            st.title(f"{info.get('shortName', sym)}")
            st.caption(f"Secteur : {info.get('sector', 'N/A')} | Pays : {info.get('country', 'N/A')}")
        with c2:
            p = info.get('currentPrice', info.get('regularMarketPreviousClose'))
            curr = info.get('currency', 'USD')
            st.metric("Cours", f"{p} {curr}")

        # Onglets
        t_chart, t_fund, t_bot = st.tabs(["Graphique", "Fondamentaux", "🤖 Analyse IA"])

        with t_chart:
            if hist is not None:
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

        with t_fund:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Capitalisation", f"{info.get('marketCap', 0)/1e9:.1f} Mrd")
            c2.metric("PER (Price/Earnings)", f"{info.get('trailingPE', '-')}")
            c3.metric("Croissance Revenus", f"{info.get('revenueGrowth', 0)*100:.1f}%")
            c4.metric("Dette/Equity", f"{info.get('debtToEquity', '-')}")
            
            st.write("---")
            st.subheader("Description")
            st.write(info.get('longBusinessSummary', 'Pas de description.'))

        with t_bot:
            st.subheader(f"🤖 L'Analyste Virtuel FHi sur {sym}")
            st.info("Posez une question pour déclencher l'analyse de nos algorithmes.")
            
            # Chatbot simple
            if "messages" not in st.session_state: st.session_state.messages = []
            
            # Reset historique si changement d'action
            if 'last_sym' not in st.session_state or st.session_state['last_sym'] != sym:
                st.session_state.messages = []
                st.session_state['last_sym'] = sym

            # Affichage
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.write(m["content"])

            # Input
            q = st.chat_input("Ex: Est-ce risqué ? Quel est ton avis ?")
            if q:
                st.chat_message("user").write(q)
                st.session_state.messages.append({"role": "user", "content": q})
                
                with st.spinner("Analyse des ratios financiers..."):
                    resp = bot_brain(q, info, sym)
                    st.chat_message("assistant").write(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})

    else:
        st.error("Impossible de récupérer les données. Vérifiez le symbole.")
