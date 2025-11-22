"""
Tema e estilos personalizados
"""
import streamlit as st


def apply_custom_css():
    """Aplicar CSS customizado para melhorar a aparência"""
    st.markdown("""
        <style>
        /* Melhorar aparência geral */
        .main {
            padding-top: 2rem;
        }
        
        /* Botões */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Cards/Métricas */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
        }
        
        /* Forms */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {
            border-radius: 8px;
        }
        
        /* Tabelas */
        .dataframe {
            border-radius: 8px;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            border-radius: 8px;
            background-color: #f8f9fa;
        }
        
        /* Alertas */
        .stAlert {
            border-radius: 8px;
        }
        
        /* Títulos */
        h1, h2, h3 {
            font-weight: 600;
        }
        
        /* Hover effects para cards */
        div[data-testid="column"] > div {
            transition: transform 0.2s;
        }
        
        div[data-testid="column"] > div:hover {
            transform: scale(1.02);
        }
        </style>
    """, unsafe_allow_html=True)


def show_success(message: str):
    """Mostrar mensagem de sucesso com ícone"""
    st.success(f"✅ {message}")


def show_error(message: str):
    """Mostrar mensagem de erro com ícone"""
    st.error(f"❌ {message}")


def show_warning(message: str):
    """Mostrar mensagem de aviso com ícone"""
    st.warning(f"⚠️ {message}")


def show_info(message: str):
    """Mostrar mensagem informativa com ícone"""
    st.info(f"ℹ️ {message}")
