"""
Sistema de Gestão de Inventário - Escuteiros
Aplicação principal com autenticação e navegação
"""
from __future__ import annotations

import streamlit as st
from datetime import datetime

# Importar módulos locais
from src.config import PAGE_CONFIG, APP_CONFIG
from src.auth import authenticator
from src.data_manager import DataManager
from src.ui import sidebar, theme

# Configurar página
st.set_page_config(**PAGE_CONFIG)

# Aplicar tema customizado
theme.apply_custom_css()


def main():
    """Função principal da aplicação"""
    
    # Verificar autenticação
    if not authenticator.check_authentication():
        authenticator.show_login_page()
        return
    
    # Inicializar gestor de dados
    data_manager = DataManager()
    
    # Renderizar sidebar com navegação
    page = sidebar.render_sidebar(st.session_state.user)
    
    # Renderizar página selecionada
    if page == "🏠 Dashboard":
        from src.pages import dashboard
        dashboard.render(data_manager)
    
    elif page == "📦 Gestão de Itens":
        from src.pages import items
        items.render(data_manager)
    
    elif page == "🔄 Movimentos":
        from src.pages import movements
        movements.render(data_manager)
    
    elif page == "📍 Locais":
        from src.pages import locations
        locations.render(data_manager)
    
    elif page == "👥 Secções":
        from src.pages import sections
        sections.render(data_manager)
    
    elif page == "📊 Relatórios":
        from src.pages import reports
        reports.render(data_manager)
    
    elif page == "⚙️ Administração":
        from src.pages import admin
        admin.render(data_manager)
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.caption(f"© {datetime.now().year} Escuteiros")


if __name__ == "__main__":
    main()
