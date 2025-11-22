"""
Sidebar com navegação e informações do utilizador
"""
import streamlit as st
from typing import Dict, Any
from datetime import datetime

from src.config import USER_ROLES
from src.auth import authenticator


def render_sidebar(user: Dict[str, Any]) -> str:
    """Renderizar sidebar com navegação"""
    
    with st.sidebar:
        # Header do utilizador
        st.markdown(f"""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem;'>
                <h2 style='color: white; margin: 0;'>🎯</h2>
                <h3 style='color: white; margin: 0;'>Inventário</h3>
                <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;'>Escuteiros</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Informação do utilizador
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <p style='margin: 0; font-size: 0.85rem; color: #666;'>👤 Utilizador</p>
                <p style='margin: 0; font-weight: 600;'>{user.get('nome', 'N/A')}</p>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; color: #666;'>🎭 Função</p>
                <p style='margin: 0; font-weight: 600;'>{user.get('funcao', 'N/A')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navegação
        st.subheader("📍 Navegação")
        
        # Determinar páginas disponíveis baseado na função
        user_role = user.get("funcao", "Utilizador")
        role_config = USER_ROLES.get(user_role, USER_ROLES["Utilizador"])
        allowed_pages = role_config["pages"]
        
        # Lista completa de páginas
        all_pages = {
            "🏠 Dashboard": "dashboard",
            "📦 Gestão de Itens": "items",
            "🔄 Movimentos": "movements",
            "📍 Locais": "locations",
            "👥 Secções": "sections",
            "📊 Relatórios": "reports",
            "⚙️ Administração": "admin",
        }
        
        # Filtrar páginas permitidas
        if "all" not in allowed_pages:
            available_pages = {
                k: v for k, v in all_pages.items() 
                if v in allowed_pages
            }
        else:
            available_pages = all_pages
        
        # Radio buttons para navegação
        page = st.radio(
            "Selecione uma página:",
            list(available_pages.keys()),
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Botão de atualizar dados
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Atualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("🚪 Sair", use_container_width=True):
                authenticator.logout()
        
        # Footer
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")
        st.caption(f"🕐 {datetime.now().strftime('%H:%M')}")
        
    return page
