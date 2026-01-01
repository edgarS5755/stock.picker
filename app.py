import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION DU SITE ---
st.set_page_config(page_title="FHi - Financial Health Index", layout="wide", page_icon="🌐")

# --- CSS "DARK INVESTING" (DESIGN) ---
st.markdown("""
<style>
    /* Fond Global */
    .stApp { background-color: #0b0e11; color: #e1e3e6; }
    
    /* Navigation Sidebar */
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333; }
    
    /* Styles des Cartes Actualités (Home) */
    .news-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 0;
        margin-bottom: 20px;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .news-card:hover { transform: translateY(-3px); border-color: #2962ff; }
    .news-img { width: 100%; height: 180px; object-fit: cover; }
    .news-content { padding: 15px; }
    .news-title { font-size: 1.1rem; font-weight: bold; color: #fff; text-decoration: none; margin-bottom: 8px; display: block;}
    .news-meta { font-size: 0.8rem; color: #8b949e; }
    
    /* Bandeau Indices (Ticker Tape) */
    .ticker-tape {
        display: flex; gap: 15px; overflow-x: auto; padding: 10px 0; border-bottom: 1px solid #333; margin-bottom: 20px;
    }
    .ticker-item {
        background: #161b22; padding: 8px 15px; border-radius: 4px; min-width: 140px; text-align: center; border: 1px solid #333;
    }
    .price-up { color: #00e676; font-weight: bold; }
    .price-down { color: #ff1744; font-weight: bold; }
    
    /* Tableaux de Marché (Home Right) */
    .market-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #222; font-size: 0.9rem; }
    .market-symbol { font-weight: 600; color: #fff; }
    
    /* Onglets */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #333; }
    .stTabs [aria-selected="true"] { background-color: #2962ff !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- DONNÉES DE DÉPART ---
HOME_INDICES = {"S&P 500": "^GSPC", "CAC 40": "^FCHI", "Nasdaq": "^IXIC", "Bitcoin": "BTC-USD", "Gold": "GC=F", "Euro/USD": "EURUSD=X"}

HOME_MARKETS = {
    "🌍 Indices": ["^GSPC", "^FCHI", "^GDAXI", "^N225", "^IXIC"],
    "🏢 Actions Top": ["AAPL", "NVDA", "MC.PA", "TSLA", "MSFT"],
    "₿ Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"],
    "🛢️ Matières": ["GC=F", "CL=F", "SI=F", "NG=F"]
}

# --- FONCTIONS ---

@st.cache_data(ttl=600)
def get_market_snapshot(tickers_dict):
    """Récupère prix et variation pour le bandeau d'accueil"""
    data = {}
    for name, symbol in tickers_dict.items():
        try:
            ticker = yf.Ticker(symbol)
            # Utilisation de fast_info pour rapidité
            price = ticker.fast_info.last_price
            prev = ticker.fast_info.previous_close
            change = ((price - prev) / prev) * 100
            data[name] = {"price": price, "change": change}
        except:
            data[name] = {"price": 0, "change": 0}
    return data

@st.cache_data(ttl=1800)
def get_home_news():
    """Récupère les news générales du marché (via S&P 500 et EURUSD)"""
    news_list = []
    for symbol in ["^GSPC", "EURUSD=X", "^FCHI"]: # Mix pour avoir des news variées
        try:
            t = yf.Ticker(symbol)
            news_list.extend(t.news)
        except:
            pass
    # Trier par date et supprimer doublons
    unique_news = {n['uuid']: n for n in news_list}.values()
    sorted_news = sorted(list(unique_news), key=lambda x: x.get('providerPublishTime', 0), reverse=True)
    return sorted_news[:12] # Top 12 articles

def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist, stock
    except:
        return None, None, None

def safe_format(value, format_str="{}", fallback="—"):
    if value is None or value == "None" or value == "N/A": return fallback
    try: return format_str.format(value)
    except: return fallback

# --- NAVIGATION SIDEBAR ---
with st.sidebar:
    try:
        st.image("image_2.png", width=140)
    except:
        st.header("FHi")
    
    st.markdown("### 🧭 Navigation")
    page = st.radio("Aller à", ["🏠 Accueil (Marchés)", "🔎 Terminal de Recherche"], index=0)
    
    st.markdown("---")
    
    if page == "🔎 Terminal de Recherche":
        st.markdown("### ⚡ Recherche Rapide")
        quick_search = st.text_input("Symbole (ex: AAPL)", "").upper()
    else:
        quick_search = None

    st.markdown("---")
    st.caption("FHi Market Intelligence v2.0")

# ==============================================================================
# PAGE 1 : ACCUEIL (STYLE INVESTING.COM)
# ==============================================================================
if page == "🏠 Accueil (Marchés)":
    
    # 1. BANDEAU HAUT (TICKER TAPE)
    snapshot = get_market_snapshot(HOME_INDICES)
    
    # Construction HTML du ticker tape
    tape_html = '<div class="ticker-tape">'
    for name, data in snapshot.items():
        color_class = "price-up" if data['change'] >= 0 else "price-down"
        sign = "+" if data['change'] >= 0 else ""
        tape_html += f"""
        <div class="ticker-item">
            <div style="font-size:0.8rem; color:#8b949e;">{name}</div>
            <div style="font-size:1.1rem; font-weight:bold;">{data['price']:,.2f}</div>
            <div class="{color_class}">{sign}{data['change']:.2f}%</div>
        </div>
        """
    tape_html += '</div>'
    st.markdown(tape_html, unsafe_allow_html=True)
    
    # 2. STRUCTURE PRINCIPALE (2 COLONNES : NEWS | MARCHÉS)
    col_news, col_sidebar = st.columns([2.5, 1])
    
    # --- COLONNE GAUCHE : ACTUALITÉS VISUELLES ---
    with col_news:
        st.subheader("📰 À la Une des Marchés")
        
        news_data = get_home_news()
        
        # On affiche en grille (2 par ligne)
        for i in range(0, len(news_data), 2):
            row_cols = st.columns(2)
            for j in range(2):
                if i + j < len(news_data):
                    article = news_data[i+j]
                    with row_cols[j]:
                        # Gestion Image
                        img_url = ""
                        if 'thumbnail' in article and 'resolutions' in article['thumbnail']:
                            # On essaie de prendre une bonne résolution
                            try: img_url = article['thumbnail']['resolutions'][0]['url']
                            except: pass
                        
                        # Affichage Carte
                        with st.container():
                            st.markdown(f"""
                            <div class="news-card">
                                {'<img src="' + img_url + '" class="news-img">' if img_url else ''}
                                <div class="news-content">
                                    <a href="{article.get('link')}" target="_blank" class="news-title">{article.get('title')}</a>
                                    <div class="news-meta">
                                        {article.get('publisher')} • {datetime.fromtimestamp(article.get('providerPublishTime', 0)).strftime('%H:%M')}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

    # --- COLONNE DROITE : TABLEAUX DE MARCHÉ ---
    with col_sidebar:
        st.subheader("📊 Tendance")
        
        market_tabs = st.tabs(["Indices", "Actions", "Crypto", "Matières"])
        
        # Fonction pour générer les mini-tableaux
        def render_mini_table(ticker_list):
            snap = get_market_snapshot({t:t for t in ticker_list})
            for sym, d in snap.items():
                c_color = "#00e676" if d['change'] >= 0 else "#ff1744"
                s_sign = "+" if d['change'] >= 0 else ""
                st.markdown(f"""
                <div class="market-row">
                    <span class="market-symbol">{sym}</span>
                    <span style="color:#fff;">{d['price']:,.2f}</span>
                    <span style="color:{c_color};">{s_sign}{d['change']:.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

        with market_tabs[0]: render_mini_table(HOME_MARKETS["🌍 Indices"])
        with market_tabs[1]: render_mini_table(HOME_MARKETS["🏢 Actions Top"])
        with market_tabs[2]: render_mini_table(HOME_MARKETS["₿ Crypto"])
        with market_tabs[3]: render_mini_table(HOME_MARKETS["🛢️ Matières"])
        
        st.markdown("---")
        st.info("💡 Conseil FHi : L'or et le Bitcoin montrent une forte corrélation inverse au Dollar cette semaine.")


# ==============================================================================
# PAGE 2 : TERMINAL DE RECHERCHE (ANCIENNE VERSION AMÉLIORÉE)
# ==============================================================================
elif page == "🔎 Terminal de Recherche":
    
    st.title("FHi Terminal")
    
    # Mapping simple
    TICKER_MAP = {"LVMH": "MC.PA", "APPLE": "AAPL", "TESLA": "TSLA", "BITCOIN": "BTC-USD"}

    # Gestion de la recherche (Input Sidebar OU Input page précédente)
    if quick_search:
        selected_ticker = quick_search
        # Check map
        for k, v in TICKER_MAP.items():
            if k in selected_ticker: selected_ticker = v
    else:
        # Recherche centrale si rien dans sidebar
        col_s1, col_s2 = st.columns([3, 1])
        with col_s1:
            search_center = st.text_input("Rechercher un actif (Nom ou Symbole)", placeholder="Ex: Nvidia, CAC 40...").upper()
        with col_s2:
            st.write("") # Spacer
            st.write("")
            if st.button("Analyser"): pass
        
        selected_ticker = search_center
        # Mapping Map
        for k, v in TICKER_MAP.items():
            if k in selected_ticker: selected_ticker = v

    # --- AFFICHAGE SECTORIEL (SI PAS DE RECHERCHE) ---
    if not selected_ticker:
        st.subheader("Explorer par Secteur")
        st.info("👈 Utilisez la barre de recherche à gauche ou ci-dessus pour une analyse précise.")
        
        tabs_sec = st.tabs(["Tech & IA", "Luxe", "Énergie"])
        with tabs_sec[0]:
            c1, c2, c3 = st.columns(3)
            c1.button("NVIDIA (NVDA)", on_click=lambda: st.write("Copiez NVDA dans la recherche"))
            c2.button("Palantir (PLTR)")
            c3.button("Microsoft (MSFT)")
            
    # --- AFFICHAGE ANALYSE (SI RECHERCHE) ---
    if selected_ticker:
        info, hist, stock_obj = get_data(selected_ticker)
        
        if info:
            # En-tête Terminal
            name = info.get('shortName', selected_ticker)
            price = info.get('currentPrice', info.get('regularMarketPreviousClose'))
            currency = info.get('currency', 'USD')
            
            st.markdown("---")
            c_h1, c_h2 = st.columns([3, 1])
            with c_h1:
                st.header(f"{name} ({selected_ticker})")
                st.caption(f"{info.get('sector')} | {info.get('industry')}")
            with c_h2:
                st.metric("Cours Actuel", f"{price} {currency}")

            # Onglets Détails
            t_chart, t_fund, t_pro, t_ai = st.tabs(["📈 Graphique", "💰 Données", "🏦 Analystes", "🤖 Bot FHi"])
            
            with t_chart:
                if not hist.empty:
                    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            
            with t_fund:
                c1, c2, c3 = st.columns(3)
                c1.metric("Cap. Boursière", safe_format(info.get('marketCap'), "{:,.0f}"))
                c2.metric("PER", safe_format(info.get('trailingPE'), "{:.2f}"))
                c3.metric("Beta", safe_format(info.get('beta'), "{:.2f}"))
                st.write(info.get('longBusinessSummary'))

            with t_pro:
                st.subheader("Consensus")
                target = info.get('targetMeanPrice')
                if target:
                    pot = ((target - price)/price)*100
                    st.metric("Objectif Moyen", f"{target} {currency}", f"{pot:.2f}%")
                    st.progress(0.7 if pot > 0 else 0.3)
                else:
                    st.warning("Pas de données analystes.")
            
            with t_ai:
                st.write(f"🤖 **Assistant FHi** : Posez une question sur {name}...")
                q = st.text_input("Votre question :")
                if q:
                    st.success(f"Réponse FHi sur {q} : L'analyse fondamentale de {name} suggère une position solide avec un PER de {info.get('trailingPE')}.")

        else:
            st.error("Action introuvable.")
