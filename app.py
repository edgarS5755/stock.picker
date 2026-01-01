import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURATION STABLE ---
st.set_page_config(page_title="FHi - Market", layout="wide", page_icon="🌐")

# --- CSS MINIMALISTE (Juste pour le mode sombre) ---
st.markdown("""
<style>
    /* Force le fond sombre propre */
    .stApp { background-color: #0e1117; color: #fafafa; }
    /* Ajustement des titres */
    h1, h2, h3 { color: #fff; }
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #000000; border-right: 1px solid #333; }
    /* Images */
    img { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- FONCTIONS ROBUSTES ---

@st.cache_data(ttl=600)
def get_market_data_safe(tickers):
    """Récupère les données sans faire planter le site"""
    data = {}
    for name, symbol in tickers.items():
        try:
            # On utilise une méthode plus légère pour éviter le blocage
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                change = ((price - prev) / prev) * 100
                data[name] = {"price": price, "change": change}
            else:
                data[name] = {"price": 0.0, "change": 0.0}
        except:
            data[name] = {"price": 0.0, "change": 0.0}
    return data

@st.cache_data(ttl=1800)
def get_news_safe():
    """Récupère les news avec gestion d'erreur d'image"""
    try:
        # On utilise le SP500 comme source d'info généraliste
        news = yf.Ticker("^GSPC").news
        clean_news = []
        seen_titles = set()
        
        for n in news:
            if n['title'] not in seen_titles:
                # Extraction sécurisée de l'image
                img = None
                if 'thumbnail' in n and 'resolutions' in n['thumbnail']:
                    try: img = n['thumbnail']['resolutions'][0]['url']
                    except: pass
                
                clean_news.append({
                    "title": n['title'],
                    "link": n['link'],
                    "publisher": n['publisher'],
                    "time": n['providerPublishTime'],
                    "img": img
                })
                seen_titles.add(n['title'])
        return clean_news[:10]
    except:
        return []

def get_stock_details(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.info, t.history(period="1y")
    except:
        return None, None

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("image_2.png", width=120)
    except:
        st.header("FHi")
    
    st.markdown("### 🧭 Menu")
    mode = st.radio("Navigation", ["🏠 Accueil Marchés", "🔎 Terminal Pro"], label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("FHi v2.1 Stable")

# ==============================================================================
# PAGE 1 : ACCUEIL (VERSION STABLE)
# ==============================================================================
if mode == "🏠 Accueil Marchés":
    st.title("Marchés en Direct")
    
    # 1. BANDEAU INDICES (Utilisation de st.metric natif = alignement parfait)
    indices = {"S&P 500": "^GSPC", "CAC 40": "^FCHI", "BTC": "BTC-USD", "ETH": "ETH-USD", "Or": "GC=F"}
    data_indices = get_market_data_safe(indices)
    
    cols = st.columns(len(indices))
    for i, (name, d) in enumerate(data_indices.items()):
        cols[i].metric(name, f"{d['price']:,.2f}", f"{d['change']:+.2f}%")
    
    st.markdown("---")
    
    # 2. CONTENU PRINCIPAL
    col_main, col_side = st.columns([2, 1], gap="large")
    
    with col_main:
        st.subheader("📰 Actualités Financières")
        news_items = get_news_safe()
        
        if not news_items:
            st.info("Chargement des actualités...")
        
        for item in news_items:
            # Boite native Streamlit (Border=True crée le cadre proprement)
            with st.container(border=True):
                c_img, c_txt = st.columns([1, 3])
                
                with c_img:
                    if item['img']:
                        st.image(item['img'], use_container_width=True)
                    else:
                        st.image("https://placehold.co/150x100?text=News", use_container_width=True)
                
                with c_txt:
                    st.markdown(f"#### [{item['title']}]({item['link']})")
                    st.caption(f"{item['publisher']} • {datetime.fromtimestamp(item['time']).strftime('%H:%M')}")

    with col_side:
        st.subheader("📊 Tendance Actions")
        # Tableau simple et propre
        top_stocks = {"NVIDIA": "NVDA", "Tesla": "TSLA", "Apple": "AAPL", "LVMH": "MC.PA", "Total": "TTE.PA"}
        data_stocks = get_market_data_safe(top_stocks)
        
        with st.container(border=True):
            for name, d in data_stocks.items():
                col_n, col_p, col_v = st.columns([2, 2, 2])
                col_n.write(f"**{name}**")
                col_p.write(f"{d['price']:.2f}")
                color = "green" if d['change'] >= 0 else "red"
                col_v.markdown(f":{color}[{d['change']:+.2f}%]")
                st.divider()
        
        st.info("💡 Conseil : Le secteur Tech surperforme aujourd'hui.")

# ==============================================================================
# PAGE 2 : TERMINAL (VERSION STABLE)
# ==============================================================================
elif mode == "🔎 Terminal Pro":
    st.title("Terminal d'Analyse FHi")
    
    c_search, c_btn = st.columns([4, 1])
    search = c_search.text_input("Symbole (ex: AAPL, MC.PA, BTC-USD)", value="AAPL").upper()
    
    if search:
        info, hist = get_stock_details(search)
        
        if info and not hist.empty:
            # En-tête propre
            st.markdown(f"## {info.get('shortName', search)}")
            c1, c2, c3 = st.columns(3)
            price = info.get('currentPrice', info.get('regularMarketPreviousClose', 0))
            currency = info.get('currency', 'USD')
            
            c1.metric("Prix", f"{price} {currency}")
            c2.metric("Secteur", info.get('sector', 'N/A'))
            c3.metric("Pays", info.get('country', 'N/A'))
            
            # Onglets natifs
            tab1, tab2, tab3 = st.tabs(["📈 Graphique", "💰 Données", "🤖 Analyse IA"])
            
            with tab1:
                fig = go.Figure(data=[go.Candlestick(x=hist.index, 
                                open=hist['Open'], high=hist['High'], 
                                low=hist['Low'], close=hist['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                c_f1, c_f2 = st.columns(2)
                c_f1.write(f"**Capitalisation:** {info.get('marketCap', 0)/1e9:.1f} Mrd")
                c_f1.write(f"**PER:** {info.get('trailingPE', 'N/A')}")
                c_f2.write(f"**Dividende:** {info.get('dividendYield', 0)*100:.2f}%")
                c_f2.write(f"**Beta:** {info.get('beta', 'N/A')}")
                
                st.write("---")
                st.caption(info.get('longBusinessSummary'))

            with tab3:
                st.write("### Assistant FHi")
                if "messages" not in st.session_state: st.session_state.messages = []
                
                q = st.text_input("Posez une question sur cette action :")
                if q:
                    st.info(f"Analyse IA pour {search} : Le consensus actuel est {info.get('recommendationKey', 'Neutre').upper()}.")
                    
        else:
            st.error("Action introuvable ou erreur de connexion.")
