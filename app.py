import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="FHi Pro - Gemini Powered", layout="wide", page_icon="🧠", initial_sidebar_state="collapsed")

# --- 2. CSS "DARK PREMIUM" ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; font-family: 'Roboto', sans-serif; }
    
    /* Input API Key */
    .stTextInput input[type="password"] { background-color: #1a1a1a; color: #00e676; border: 1px solid #333; }

    /* Cartes Actions */
    .stock-card {
        background-color: #111; border: 1px solid #333; border-radius: 8px; padding: 15px; text-align: center;
        transition: transform 0.2s;
    }
    .stock-card:hover { border-color: #007bff; transform: translateY(-3px); }
    .big-price { font-size: 1.5rem; font-weight: 700; color: #fff; }
    .pos { color: #00e676; } .neg { color: #ff1744; }

    /* Onglets */
    .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #333; }
    .stTabs [aria-selected="true"] { color: #007bff !important; border-bottom-color: #007bff !important; }
    
    /* Chatbot */
    .stChatMessage { background-color: #111; border-radius: 10px; border: 1px solid #222; }
</style>
""", unsafe_allow_html=True)

# --- 3. STATE MANAGEMENT ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'ticker' not in st.session_state: st.session_state.ticker = None
if 'api_key' not in st.session_state: st.session_state.api_key = ""

def navigate(to, symbol=None):
    st.session_state.view = to
    if symbol: 
        st.session_state.ticker = symbol
        st.session_state.messages = [] # Reset chat

# --- 4. DATA FUNCTIONS ---
@st.cache_data(ttl=60)
def get_live_quote(symbol):
    try:
        t = yf.Ticker(symbol)
        price = t.fast_info.last_price
        prev = t.fast_info.previous_close
        return price, ((price - prev)/prev)*100
    except: return 0.0, 0.0

@st.cache_data(ttl=900)
def get_details(symbol):
    try:
        t = yf.Ticker(symbol)
        return t.info, t.history(period="1y")
    except: return None, None

@st.cache_data(ttl=300)
def get_chart_data(symbol, period):
    try:
        t = yf.Ticker(symbol)
        # Ajustement intervalle
        interval = "1d"
        if period in ["1mo", "3mo"]: interval = "1d"
        elif period in ["5d"]: interval = "15m"
        else: interval = "1wk"
        return t.history(period=period, interval=interval)
    except: return pd.DataFrame()

# --- 5. INTELLIGENCE GEMINI (VRAIE IA) ---
def ask_gemini_real(api_key, query, info, symbol, hist_data):
    """Envoie les données financières brutes à Gemini pour analyse"""
    if not api_key:
        return "⚠️ Veuillez entrer votre Clé API Gemini dans le menu (Barre latérale ou haut de page) pour activer l'intelligence."
    
    try:
        # Configuration
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Préparation du contexte financier pour l'IA
        context = f"""
        Tu es FHi Bot, un analyste financier expert de Wall Street.
        Analyse l'action : {info.get('shortName')} ({symbol}).
        
        DONNÉES FINANCIÈRES EN TEMPS RÉEL :
        - Prix actuel : {info.get('currentPrice')} {info.get('currency')}
        - Secteur : {info.get('sector')}
        - PER (Price Earnings) : {info.get('trailingPE')}
        - Objectif Analystes : {info.get('targetMeanPrice')}
        - Recommandation Consensus : {info.get('recommendationKey')}
        - Marge Nette : {info.get('profitMargins')}
        - Dette/Equity : {info.get('debtToEquity')}
        - Cash Flow Libre : {info.get('freeCashflow')}
        
        QUESTION DE L'UTILISATEUR : "{query}"
        
        CONSIGNES :
        1. Sois direct, professionnel et utilise les chiffres fournis.
        2. Si l'utilisateur demande un avis, base-toi sur le consensus et les ratios (PER, Marges).
        3. Fais des phrases courtes et impactantes. Utilise des emojis financiers.
        4. Ne dis jamais "Je suis une IA", dis "L'analyse FHi indique...".
        """
        
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        return f"Erreur de connexion à Gemini : {e}. Vérifiez votre clé API."

# --- 6. BARRE DE NAVIGATION ---
c1, c2, c3, c4 = st.columns([1, 2, 4, 1])
with c1:
    if st.button("🏠 ACCUEIL"): navigate('home')
with c2:
    # Champ pour la clé API (Mot de passe)
    api_k = st.text_input("🔑 Clé Gemini API", type="password", placeholder="Collez votre clé ici...", key="input_key")
    if api_k: st.session_state.api_key = api_k
with c3:
    search = st.text_input("Recherche", placeholder="Ex: Nvidia, LVMH...", label_visibility="collapsed").upper()
    if search:
        # Mapping rapide
        mapping = {"TOTAL": "TTE.PA", "LVMH": "MC.PA", "APPLE": "AAPL"}
        target = mapping.get(search, search)
        navigate('terminal', target)
        st.rerun()
with c4:
    if st.session_state.ticker:
        if st.button(f"📊 {st.session_state.ticker}"): navigate('terminal')

st.markdown("---")

# --- 7. VUE ACCUEIL ---
if st.session_state.view == 'home':
    st.title("Market Opportunities")
    
    NICHES = {
        "🚀 AI & Chips": ["NVDA", "AMD", "TSM", "PLTR", "AVGO"],
        "🛡️ Cyber & Cloud": ["CRWD", "PANW", "SNOW", "MSFT", "GOOGL"],
        "🏰 Luxe & Retail": ["MC.PA", "RMS.PA", "KER.PA", "NKE", "COST"],
        "₿ Crypto Assets": ["BTC-USD", "ETH-USD", "COIN", "MSTR", "SOL-USD"]
    }
    
    tabs = st.tabs(list(NICHES.keys()))
    
    for i, (name, tickers) in enumerate(NICHES.items()):
        with tabs[i]:
            cols = st.columns(5)
            for j, t in enumerate(tickers):
                p, chg = get_live_quote(t)
                color = "pos" if chg >= 0 else "neg"
                sign = "+" if chg >= 0 else ""
                
                with cols[j % 5]:
                    with st.container():
                        st.markdown(f"""
                        <div class="stock-card">
                            <div style="color:#888;">{t}</div>
                            <div class="big-price">{p:,.2f}</div>
                            <div class="{color}">{sign}{chg:.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Analyser", key=f"btn_{t}"):
                            navigate('terminal', t)
                            st.rerun()

# --- 8. VUE TERMINAL ---
elif st.session_state.view == 'terminal':
    sym = st.session_state.ticker
    info, hist_1y = get_details(sym)
    
    if info:
        # HEADER
        c1, c2 = st.columns([3, 1])
        with c1:
            st.title(f"{info.get('shortName', sym)}")
            st.caption(f"{info.get('sector')} • {info.get('industry')}")
        with c2:
            st.markdown(f"<div class='big-price' style='text-align:right'>{info.get('currentPrice')} {info.get('currency')}</div>", unsafe_allow_html=True)

        # ONGLETS
        t1, t2, t3 = st.tabs(["Graphique", "Données", "🧠 Assistant Gemini"])

        # GRAPH
        with t1:
            periods = ["1d", "5d", "1mo", "6mo", "1y", "5y"]
            sel_p = st.select_slider("Période", options=periods, value="1y")
            df = get_chart_data(sym, sel_p)
            
            if not df.empty:
                # Perf calcul
                start = df['Close'].iloc[0]
                end = df['Close'].iloc[-1]
                perf = ((end-start)/start)*100
                col_perf = "green" if perf >= 0 else "red"
                st.markdown(f"Performance : <span style='color:{col_perf}; font-weight:bold'>{perf:+.2f}%</span>", unsafe_allow_html=True)
                
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)

        # DATA
        with t2:
            st.subheader("Indicateurs Clés")
            k1, k2, k3, k4 = st.columns(4)
            
            def fmt(v, is_percent=False):
                if v is None: return "-"
                if is_percent: return f"{v*100:.2f}%"
                return f"{v:,.2f}"

            k1.metric("Capitalisation", f"{info.get('marketCap', 0)/1e9:.2f} Mrd")
            k2.metric("PER (Price/Earnings)", fmt(info.get('trailingPE')))
            k3.metric("Marge Nette", fmt(info.get('profitMargins'), True))
            k4.metric("Dette/Equity", fmt(info.get('debtToEquity')))
            
            st.divider()
            st.write(info.get('longBusinessSummary'))

        # GEMINI CHAT
        with t3:
            st.markdown("### 🤖 Analyse par Google Gemini")
            if not st.session_state.api_key:
                st.warning("👈 Entrez votre clé API Gemini dans la barre du haut pour activer l'IA.")
            else:
                st.success("Gemini connecté & prêt à analyser.")

            # Historique
            if "messages" not in st.session_state: st.session_state.messages = []
            for m in st.session_state.messages:
                with st.chat_message(m["role"]): st.write(m["content"])

            # Input
            if prompt := st.chat_input(f"Posez une question sur {sym} à Gemini..."):
                st.chat_message("user").write(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                with st.spinner("Gemini analyse les rapports financiers..."):
                    # APPEL À LA VRAIE IA
                    response = ask_gemini_real(st.session_state.api_key, prompt, info, sym, hist_1y)
                    
                    st.chat_message("assistant").write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

    else:
        st.error("Données indisponibles.")
