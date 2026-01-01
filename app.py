import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURATION & CSS (LOOK "PRO DARK") ---
st.set_page_config(page_title="FHi - Financial Health Index", layout="wide", page_icon="📈")

st.markdown("""
<style>
    /* FOND GLOBAL & TYPO */
    .stApp { background-color: #000000; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
    
    /* BANDEAU DEFILANT (TICKER TAPE CSS) */
    .ticker-wrap {
        width: 100%; overflow: hidden; background-color: #111; border-bottom: 1px solid #333; padding: 10px 0; white-space: nowrap;
    }
    .ticker { display: inline-block; animation: marquee 30s linear infinite; }
    @keyframes marquee { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-item {
        display: inline-block; padding: 0 2rem; font-size: 1rem; color: #fff; font-weight: bold;
    }
    .up { color: #00e676; }
    .down { color: #ff1744; }

    /* CARTE NEWS (STYLE INVESTING.COM) */
    .news-container {
        background-color: #161b22; border: 1px solid #333; border-radius: 8px; margin-bottom: 15px; overflow: hidden;
        transition: transform 0.2s;
    }
    .news-container:hover { border-color: #2962ff; transform: translateY(-2px); }
    .news-img { width: 100%; height: 160px; object-fit: cover; opacity: 0.9; }
    .news-body { padding: 12px; }
    .news-title { font-size: 1.05rem; font-weight: 600; color: #fff; text-decoration: none; display: block; margin-bottom: 5px; line-height: 1.4; }
    .news-meta { font-size: 0.8rem; color: #888; }

    /* ONGLETS NAVIGATION */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #333; }
    .stTabs [data-baseweb="tab"] { background-color: #111; border: 1px solid #333; color: #888; border-radius: 6px 6px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #2962ff !important; color: white !important; border-bottom: none; }

    /* INPUT RECHERCHE (LOUPE) */
    .stTextInput input { background-color: #222; color: white; border: 1px solid #444; border-radius: 20px; }

    /* SIDEBAR */
    [data-testid="stSidebar"] { background-color: #050505; border-right: 1px solid #222; }
</style>
""", unsafe_allow_html=True)

# --- 2. DONNÉES & MAPPING ---
# Base de reconnaissance étendue pour la loupe
TICKER_MAP = {
    "LVMH": "MC.PA", "TOTAL": "TTE.PA", "AIRBUS": "AIR.PA", "SANOFI": "SAN.PA", "BNP": "BNP.PA", "AXA": "CS.PA",
    "APPLE": "AAPL", "MICROSOFT": "MSFT", "TESLA": "TSLA", "NVIDIA": "NVDA", "AMAZON": "AMZN", "GOOGLE": "GOOGL",
    "BITCOIN": "BTC-USD", "ETHEREUM": "ETH-USD", "SOLANA": "SOL-USD",
    "OR": "GC=F", "PETROLE": "CL=F"
}

SECTORS_DATA = {
    "🔥 Pépites Croissance": ["PLTR", "SOFI", "NVDA", "AMD", "TSLA", "SNOW", "U"],
    "💎 Luxe & Europe": ["MC.PA", "RMS.PA", "OR.PA", "KER.PA", "RACE.MI", "AIR.PA"],
    "⚡ Énergie & Industrie": ["TTE.PA", "XOM", "SHELL", "SU.PA", "ENPH"],
    "₿ Crypto & Blockchain": ["BTC-USD", "ETH-USD", "COIN", "MSTR", "SOL-USD"],
    "💊 BioTech & Pharma": ["LLY", "NVO", "MRNA", "PFE", "SANOFI"]
}

INDICES_TICKER = {"S&P500": "^GSPC", "CAC40": "^FCHI", "NASDAQ": "^IXIC", "BTC": "BTC-USD", "VIX": "^VIX"}

# --- 3. FONCTIONS INTELLIGENTES (CACHE) ---

def safe_fmt(val, fmt="{:.2f}", fallback="-"):
    if val is None or val == "None": return fallback
    try: return fmt.format(val)
    except: return fallback

@st.cache_data(ttl=600)
def get_ticker_tape_data():
    """Récupère les données légères pour le bandeau"""
    html_parts = []
    for name, sym in INDICES_TICKER.items():
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="2d")
            if len(hist) > 1:
                close = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                chg = ((close - prev)/prev)*100
                cls = "up" if chg >= 0 else "down"
                sign = "+" if chg >= 0 else ""
                html_parts.append(f'<span class="ticker-item">{name} <span class="{cls}">{sign}{chg:.2f}%</span></span>')
        except: pass
    return "".join(html_parts) * 5  # Répéter pour l'effet de boucle

@st.cache_data(ttl=1800)
def get_stock_full(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.info, t.history(period="1y"), t.news
    except: return None, None, None

def ai_bot_logic(query, info, symbol):
    """Logique du Bot FHi sans API externe"""
    q = query.lower()
    name = info.get('shortName', symbol)
    
    # Concurrents basiques par secteur (Logique hardcodée pour vitesse)
    sector = info.get('sector', '')
    peers = "ses concurrents"
    if "Technology" in sector: peers = "Microsoft, Apple ou Nvidia"
    if "Auto" in sector: peers = "Toyota, VW ou Ford"
    if "Luxury" in sector: peers = "Hermès ou Kering"

    if any(x in q for x in ["histoire", "activite", "fait quoi"]):
        return f"**À propos de {name} :**\n\n{info.get('longBusinessSummary', 'Pas de description.')[:600]}..."
    
    if any(x in q for x in ["avis", "acheter", "vendre", "potentiel"]):
        tgt = info.get('targetMeanPrice')
        px = info.get('currentPrice')
        rec = info.get('recommendationKey', 'inconnue').upper().replace('_', ' ')
        if tgt and px:
            pot = ((tgt - px)/px)*100
            return f"**Analyse FHi :**\n\nLe consensus analystes est **{rec}**.\nObjectif de cours : {tgt} (Potentiel: {pot:+.2f}%).\nMon conseil : {'Surveiller pour achat' if pot > 10 else 'Attendre un repli'}."
        return "Données analystes insuffisantes pour un conseil ferme."

    if any(x in q for x in ["concurrent", "rival", "comparaison"]):
        pe = info.get('trailingPE', 'N/A')
        return f"{name} évolue dans le secteur {sector}. On la compare souvent à **{peers}**. Son PER actuel est de {pe}, ce qui permet de juger sa cherté relative."

    return f"Je suis l'IA experte sur {name}. Demandez-moi son histoire, ses concurrents ou mon avis d'investissement."

# --- 4. INTERFACE : SIDEBAR ---
with st.sidebar:
    try:
        st.image("image_2.png", width=140)
    except:
        st.header("FHi")

    st.markdown("### 🔍 Recherche Rapide")
    # La Loupe qui contrôle tout
    search_query = st.text_input("Symbole ou Nom (ex: LVMH)", placeholder="Chercher une action...").upper()
    
    st.markdown("---")
    st.markdown("### 🧭 Menu")
    nav = st.radio("Navigation", ["🏠 Accueil & News", "📊 Terminal Pro"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### 🔐 Compte Pro")
    pwd = st.text_input("Clé Licence", type="password")
    IS_PRO = pwd == "PRO2026"
    if IS_PRO: st.success("Mode TRADER : ACTIF")

# --- LOGIQUE DE ROUTAGE ---
# Si une recherche est faite dans la loupe, on force l'affichage du Terminal
active_ticker = None
if search_query:
    nav = "📊 Terminal Pro" # Force switch
    # Mapping Nom -> Symbole
    found = False
    for k, v in TICKER_MAP.items():
        if k in search_query:
            active_ticker = v
            found = True
            break
    if not found: active_ticker = search_query

# --- 5. PAGE : ACCUEIL (MEDIA & PEPITES) ---
if nav == "🏠 Accueil & News":
    
    # A. Ticker Tape (HTML CSS Animation)
    tape_content = get_ticker_tape_data()
    st.markdown(f'<div class="ticker-wrap"><div class="ticker">{tape_content}</div></div>', unsafe_allow_html=True)
    
    st.title("FHi Market Intelligence")
    
    # B. Compartiments Sectoriels (Pépites)
    st.subheader("🔥 Les Pépites du Marché")
    tabs_sec = st.tabs(list(SECTORS_DATA.keys()))
    
    for i, (sec_name, tickers) in enumerate(SECTORS_DATA.items()):
        with tabs_sec[i]:
            # Grille de boutons
            cols = st.columns(6)
            for j, t in enumerate(tickers):
                if cols[j % 6].button(f"{t}", key=f"btn_{t}"):
                    # Astuce: On stocke dans la session pour basculer vers le terminal
                    st.session_state['force_ticker'] = t
                    st.rerun() # Recharge pour appliquer le changement

    # C. Actualités Visuelles (Mise en page Magazine)
    st.markdown("---")
    st.subheader("📰 À la Une")
    
    # On récupère des news générales (Tech + Finance)
    _, _, news_items = get_stock_full("^GSPC") # S&P 500 pour news globales
    
    if news_items:
        # Grille 3 colonnes pour les news
        rows = [news_items[i:i+3] for i in range(0, min(len(news_items), 9), 3)]
        for row in rows:
            cols = st.columns(3)
            for idx, article in enumerate(row):
                with cols[idx]:
                    # Gestion Image (Try/Except pour éviter crash)
                    img_url = "https://via.placeholder.com/300x160?text=FHi+News"
                    if 'thumbnail' in article and 'resolutions' in article['thumbnail']:
                        try: img_url = article['thumbnail']['resolutions'][0]['url']
                        except: pass
                    
                    # HTML Card
                    st.markdown(f"""
                    <div class="news-container">
                        <a href="{article['link']}" target="_blank">
                            <img src="{img_url}" class="news-img">
                        </a>
                        <div class="news-body">
                            <a href="{article['link']}" target="_blank" class="news-title">{article['title']}</a>
                            <div class="news-meta">{article['publisher']} • {datetime.fromtimestamp(article['providerPublishTime']).strftime('%H:%M')}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# --- 6. PAGE : TERMINAL COMPLET ---
if nav == "📊 Terminal Pro":
    # Récupération du ticker (soit via Loupe, soit via Clic Accueil)
    if 'force_ticker' in st.session_state and not search_query:
        active_ticker = st.session_state['force_ticker']
    if not active_ticker: active_ticker = "AAPL" # Défaut

    # Chargement Data
    info, hist, news = get_stock_full(active_ticker)
    
    if info:
        # Header Pro
        c1, c2 = st.columns([3, 1])
        with c1:
            st.title(f"{info.get('shortName', active_ticker)} ({active_ticker})")
            st.caption(f"{info.get('sector', 'N/A')} | {info.get('country', 'Monde')}")
        with c2:
            price = info.get('currentPrice', info.get('regularMarketPreviousClose'))
            curr = info.get('currency', 'USD')
            st.metric("Cours Actuel", f"{price} {curr}")

        # Onglets Détails
        t_chart, t_data, t_pro, t_ai = st.tabs(["📈 Graphique", "💰 Financier", "🏦 Banques (PRO)", "🤖 Assistant FHi"])

        with t_chart:
            if hist is not None and not hist.empty:
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else: st.warning("Graphique indisponible.")

        with t_data:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Cap. Boursière", safe_fmt(info.get('marketCap')/1e9 if info.get('marketCap') else 0, "{:.1f} Mrd"))
            c2.metric("Chiffre d'Affaires", safe_fmt(info.get('totalRevenue')/1e9 if info.get('totalRevenue') else 0, "{:.1f} Mrd"))
            c3.metric("PER (Ratio)", safe_fmt(info.get('trailingPE')))
            c4.metric("Dividende", safe_fmt(info.get('dividendYield'), "{:.2%}"))
            st.markdown("#### Profil")
            st.write(info.get('longBusinessSummary', ''))

        with t_pro:
            if IS_PRO:
                tgt = info.get('targetMeanPrice')
                rec = info.get('recommendationKey', 'N/A').upper().replace('_', ' ')
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.metric("Objectif Moyen", safe_fmt(tgt, f"{{}} {curr}"))
                    if tgt and price:
                        pot = ((tgt - price)/price)*100
                        color = "green" if pot > 0 else "red"
                        st.markdown(f"Potentiel : :{color}[**{pot:+.2f}%**]")
                with col_p2:
                    st.metric("Consensus", rec)
                    st.progress(0.8 if "BUY" in rec else 0.4)
                
                st.info("Données agrégées des analystes majeurs (Goldman, JP Morgan...).")
                c_lk1, c_lk2 = st.columns(2)
                c_lk1.link_button("Vérifier sur Yahoo Finance", f"https://finance.yahoo.com/quote/{active_ticker}")
                c_lk2.link_button("Vérifier sur MarketWatch", f"https://www.marketwatch.com/investing/stock/{active_ticker}")
            else:
                st.warning("🔒 Section PRO verrouillée. Entrez votre clé licence dans le menu.")

        with t_ai:
            st.markdown(f"### 🤖 Discussion avec l'Analyste FHi")
            # Chatbot UI
            if "messages" not in st.session_state: st.session_state.messages = []
            
            # Afficher historique (clean up si on change d'action)
            if 'last_ticker' not in st.session_state or st.session_state['last_ticker'] != active_ticker:
                st.session_state.messages = []
                st.session_state['last_ticker'] = active_ticker

            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

            if prompt := st.chat_input(f"Posez une question sur {active_ticker}..."):
                st.chat_message("user").write(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                with st.spinner("Analyse en cours..."):
                    if IS_PRO:
                        resp = ai_bot_logic(prompt, info, active_ticker)
                    else:
                        resp = "🔒 Je ne peux pas analyser les concurrents en version gratuite."
                    
                    st.chat_message("assistant").write(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})

    else:
        st.error(f"Impossible de charger '{active_ticker}'. Vérifiez le symbole.")
