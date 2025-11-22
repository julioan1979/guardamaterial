"""
Configurações da aplicação
"""
import os
import streamlit as st

# Configuração da página Streamlit
PAGE_CONFIG = {
    "page_title": "Gestão de Inventário - Escuteiros",
    "page_icon": "🎯",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        "Get Help": None,
        "Report a bug": None,
        "About": "Sistema de Gestão de Inventário para Escuteiros"
    }
}

# Configurações da aplicação
APP_CONFIG = {
    "name": "Gestão de Inventário - Escuteiros",
    "version": "2.0.0",
    "description": "Sistema completo de gestão de stock e inventário",
}

# Configurações do Airtable
def get_airtable_config():
    """Obter configurações do Airtable de secrets ou variáveis de ambiente"""
    try:
        return {
            "api_key": st.secrets.get("AIRTABLE_API_KEY") or os.getenv("AIRTABLE_API_KEY"),
            "base_id": st.secrets.get("AIRTABLE_BASE_ID") or os.getenv("AIRTABLE_BASE_ID"),
            "users_table": st.secrets.get("AIRTABLE_USERS_TABLE", "Usuarios") or os.getenv("AIRTABLE_USERS_TABLE", "Usuarios"),
        }
    except Exception:
        return {
            "api_key": os.getenv("AIRTABLE_API_KEY"),
            "base_id": os.getenv("AIRTABLE_BASE_ID"),
            "users_table": os.getenv("AIRTABLE_USERS_TABLE", "Usuarios"),
        }

# Nomes das tabelas no Airtable
TABLES = {
    "USERS": "Usuarios",
    "SECTIONS": "Seccoes",
    "LOCATIONS": "Local",
    "ITEMS": "Itens",
    "MOVEMENTS": "Movimentos",
}

# Configurações de cache
CACHE_TTL = 300  # 5 minutos

# Perfis de utilizador
USER_ROLES = {
    "Administrador": {
        "permissions": ["read", "write", "delete", "admin"],
        "pages": ["all"]
    },
    "Gestor": {
        "permissions": ["read", "write"],
        "pages": ["dashboard", "items", "movements", "locations", "sections", "reports"]
    },
    "Utilizador": {
        "permissions": ["read"],
        "pages": ["dashboard", "items", "movements", "reports"]
    }
}
