"""
Página de Gestão de Locais
"""
import streamlit as st
import pandas as pd

from src.data_manager import DataManager
from src.ui import theme
from src.schema_sync import get_options_with_fallback


def render(data_manager: DataManager):
    """Renderizar página de locais"""
    
    st.title("📍 Gestão de Locais")
    st.markdown("Gerir locais de armazenamento de materiais")
    
    # Tabs
    tab_list, tab_add = st.tabs([
        "📋 Lista de Locais",
        "➕ Adicionar Local"
    ])
    
    # === TAB: LISTA ===
    with tab_list:
        st.subheader("📋 Todos os Locais")
        
        locations_df = data_manager.get_locations()
        
        if locations_df.empty:
            theme.show_info("Ainda não existem locais registados")
        else:
            # Pesquisa
            search = st.text_input("🔍 Pesquisar", placeholder="Nome do local...")
            
            filtered_df = locations_df.copy()
            
            if search:
                mask = filtered_df.apply(
                    lambda row: search.lower() in str(row).lower(),
                    axis=1
                )
                filtered_df = filtered_df[mask]
            
            # Métricas
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Locais Filtrados", len(filtered_df))
            with col2:
                st.metric("Total de Locais", len(locations_df))
            
            st.markdown("---")
            
            # Tabela
            if not filtered_df.empty:
                display_cols = []
                for col in ["Localizacao", "Local", "Orientação no Local", "Contencao", "Notas", "Itens"]:
                    if col in filtered_df.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        filtered_df[display_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                else:
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=400)
            else:
                theme.show_warning("Nenhum local encontrado")
    
    # === TAB: ADICIONAR ===
    with tab_add:
        st.subheader("➕ Adicionar Novo Local")
        
        with st.form("form_add_location", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                local_options = get_options_with_fallback("Local", "Local")
                local = st.selectbox(
                    "🏢 Local *",
                    [""] + local_options
                )
                
                orientacao_options = get_options_with_fallback("Local", "Orientação no Local")
                orientacao = st.selectbox(
                    "🧭 Orientação no Local",
                    [""] + orientacao_options
                )
            
            with col2:
                contencao_options = get_options_with_fallback("Local", "Contencao")
                contencao = st.selectbox(
                    "📦 Contenção",
                    [""] + contencao_options
                )
            
            notas = st.text_area(
                "📝 Notas",
                placeholder="Descrição adicional do local..."
            )
            
            st.markdown("---")
            
            submitted = st.form_submit_button(
                "💾 Guardar Local",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not local:
                    theme.show_error("Por favor selecione um local!")
                else:
                    location_data = {
                        "Local": local,
                    }
                    
                    if orientacao:
                        location_data["Orientação no Local"] = orientacao
                    
                    if contencao:
                        location_data["Contencao"] = contencao
                    
                    if notas:
                        location_data["Notas"] = notas
                    
                    with st.spinner("A guardar local..."):
                        result = data_manager.create_location(location_data)
                        
                        if result:
                            theme.show_success("Local criado com sucesso!")
                            st.rerun()
                        else:
                            theme.show_error("Erro ao criar local")
