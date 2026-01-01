import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURATION DU SITE ---
st.set_page_config(page_title="FHi", layout="wide", page_icon=None, initial_sidebar_state="collapsed")

# --- 2. CSS "SAFARI DARK" (Design Apple-like) ---
st.markdown("""
<style>
    /* RESET GLOBAL */
    .stApp { background-color: #000000; color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* CACHER LA SIDEBAR ET LE HEADER STREAMLIT */
    [data-testid="stSidebar"] { display: none; }
    header { visibility: hidden; }
    
    /* BARRE DE NAVIGATION (STYLE SAFARI) */
    .nav-container {
        position: fixed; top: 0; left: 0; width: 100%; height: 60px;
        background-color: rgba(28, 28, 30, 0.8); /* Transparence floutée */
        backdrop-filter: blur(20px);
        z-index: 999; border-bottom: 1px solid #333;
        display: flex; align-items: center; justify-content: space-between; padding: 0 20px;
    }
    
    /* INPUT RECHERCHE (STYLE URL BAR) */
    .stTextInput > div > div > input {
        background-color: #1c1c1e; color: #fff; border: none; border-radius: 8px; text-align: center;
        font-size: 14px; height: 35px;
    }
    .stTextInput > div > div > input:focus { box-shadow: 0 0 0 2px #0a84ff; }

    /* BOUTONS NAVIGATION (ONGLETS PROPRES) */
    div.stButton > button {
        background-color: transparent; border: none; color: #86868b; font-weight: 500; font-size: 15px;
        transition: color 0.2s; padding: 0 15px;
    }
    div.stButton > button:hover { color: #ffffff; }
    div.stButton > button:focus { color: #ffffff; border: none; box-shadow: none; }
    
    /* CARTES FLOTTANTES (SANS BORDURES) */
    .stock-card {
        background-color: #1c1c1e; padding: 15px; border-radius: 12px; margin-bottom: 10px;
        cursor: pointer; transition: transform 0.1s, background-color 0.2s;
    }
    .stock-card:hover { background-color: #2c2c2e; }
    
    /* TYPOGRAPHIE */
    h1, h2, h3 { font-weight: 600; letter-spacing: -0.5px; color: #fff; }
    .sub-text { color: #86868b; font-size: 13px; }
    .price-text { font-size: 16px; font-weight: 600; color: #fff; }
    .green { color: #30d158; }
    .red { color: #ff453a; }

    /* ONGLETS INTERNES (Minimalistes) */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #333; gap: 20px; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; color: #86868b; font-size: 14px; }
    .stTabs [aria-selected="true"] { color: #fff !important; font-weight: 600; border-bottom: 2px solid #fff; }
</style>
""", unsafe_allow_html=True)

# --- 3. GESTION DE L'ÉTAT (NAVIGATION) ---
if 'view' not in st.session_state: st.session_state.view = 'accueil'
if 'ticker' not in st.session_state: st.session_state.ticker = None

def go_to_terminal(symbol):
    st.session_state.ticker = symbol
    st.session_state.view = 'terminal'

def go_home():
    st.session_state.view = 'accueil'

# --- 4. DONNÉES ---
SECTORS = {
    "US Tech": ["AAPL", "NVDA", "MSFT", "PLTR", "TSLA"],
    "Europe Luxe & Ind": ["MC.PA", "RMS.PA", "AIR.PA", "TTE.PA"],
    "Crypto Assets": ["BTC-USD", "ETH-USD", "SOL-USD", "COIN"],
    "Pharma": ["LLY", "NVO", "SANOFI"]
}

TICKER_MAP = {
    "LVMH": "MC.PA", "APPLE": "AAPL", "TESLA": "TSLA", "BITCOIN": "BTC-USD"
}

@st.cache_data(ttl=600)
def get_simple_quote(symbol):
    try:
        t = yf.Ticker(symbol)
        # Fast info est plus rapide
        price = t.fast_info.last_price
        prev = t.fast_info.previous_close
        change = ((price - prev)/prev)*100
        return price, change
    except: return 0, 0

@st.cache_data(ttl=1800)
def get_full_data(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.info, t.history(period="1y"), t.news
    except: return None, None, None

# --- 5. BARRE DE NAVIGATION (TOP BAR) ---
# On utilise des colonnes pour simuler la barre Safari
col_logo, col_search, col_nav1, col_nav2 = st.columns([1, 4, 1, 1])

with col_logo:
    if st.button("FHi", key="nav_home"):
        go_home()
        st.rerun()

with col_search:
    search_val = st.text_input("Recherche (ex: LVMH)", label_visibility="collapsed", placeholder="Rechercher ou saisir un site").upper()
    if search_val:
        # Check map
        target = search_val
        for k, v in TICKER_MAP.items():
            if k in search_val: target = v
        go_to_terminal(target)
        st.rerun()

with col_nav1:
    if st.button("Marchés"): 
        go_home()
        st.rerun()

with col_nav2:
    if st.button("Terminal"):
        if st.session_state.ticker: st.session_state.view = 'terminal'
        st.rerun()

st.write("") # Spacer pour ne pas être collé à la barre

# --- 6. VUE : ACCUEIL ---
if st.session_state.view == 'accueil':
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Marchés")
    
    # BANDEAU D'INDICES (Minimaliste)
    cols = st.columns(4)
    indices = {"S&P 500": "^GSPC", "CAC 40": "^FCHI", "BTC": "BTC-USD", "EUR/USD": "EURUSD=X"}
    
    for i, (name, sym) in enumerate(indices.items()):
        p, c = get_simple_quote(sym)
        color = "green" if c >= 0 else "red"
        cols[i].markdown(f"""
        <div style="text-align:center;">
            <div class="sub-text">{name}</div>
            <div class="price-text">{p:,.2f} <span class="{color}">{c:+.2f}%</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    # GRILLE SECTORIELLE INTERACTIVE
    for cat, tickers in SECTORS.items():
        st.subheader(cat)
        
        # On crée une ligne de colonnes
        cols_stock = st.columns(len(tickers))
        
        for idx, t in enumerate(tickers):
            # Récupération data rapide
            p, c = get_simple_quote(t)
            c_color = "green" if c >= 0 else "red"
            
            # Le bouton Streamlit prend toute la largeur de la colonne
            # L'astuce : utiliser le bouton comme carte cliquable
            label = f"{t}\n{p:.2f} ({c:+.1f}%)"
            if cols_stock[idx].button(label, key=f"btn_{t}"):
                go_to_terminal(t)
                st.rerun()

    st.markdown("---")
    st.subheader("Actualités")
    
    # News S&P500 génériques
    _, _, news = get_full_data("^GSPC")
    if news:
        for n in news[:5]:
            with st.container():
                c1, c2 = st.columns([1, 4])
                with c1:
                    # Image
                    img = n.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '')
                    if img: st.image(img, use_container_width=True)
                with c2:
                    st.markdown(f"**[{n['title']}]({n['link']})**")
                    st.caption(f"{n['publisher']} • {datetime.fromtimestamp(n['providerPublishTime']).strftime('%H:%M')}")
            st.divider()

# --- 7. VUE : TERMINAL (FICHE ACTION) ---
elif st.session_state.view == 'terminal':
    st.markdown("<br>", unsafe_allow_html=True)
    
    symbol = st.session_state.ticker
    if not symbol:
        st.warning("Aucune action sélectionnée.")
        st.stop()

    info, hist, news = get_full_data(symbol)
    
    if info:
        # HEADER ACTION
        c1, c2 = st.columns([3, 1])
        with c1:
            st.title(info.get('shortName', symbol))
            st.caption(f"{symbol} • {info.get('sector', '')} • {info.get('country', '')}")
        with c2:
            price = info.get('currentPrice', info.get('regularMarketPreviousClose'))
            curr = info.get('currency', 'USD')
            st.metric("Cours", f"{price} {curr}")

        # ONGLETS SAFARI
        tab_chart, tab_data, tab_ai = st.tabs(["Graphique", "Données", "Assistant"])

        with tab_chart:
            # Graphique épuré
            if hist is not None:
                fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
                fig.update_layout(
                    template="plotly_dark", 
                    height=500, 
                    xaxis_rangeslider_visible=False, 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab_data:
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Cap Market**\n{info.get('marketCap', 0)/1e9:.1f} Mrd")
            c2.write(f"**PER**\n{info.get('trailingPE', '-')}")
            c3.write(f"**Cible Analystes**\n{info.get('targetMeanPrice', '-')}")
            st.markdown("<br>", unsafe_allow_html=True)
            st.write(info.get('longBusinessSummary', ''))

        with tab_ai:
            st.write(f"**Analyse FHi sur {symbol}**")
            # Petit bot intégré
            q = st.text_input("Poser une question...", key="ai_input")
            if q:
                rec = info.get('recommendationKey', 'inconnue').upper().replace('_', ' ')
                st.info(f"Le consensus est {rec}. Basé sur les fondamentaux, {symbol} est une valeur à surveiller.")

    else:
        st.error("Données indisponibles.")
