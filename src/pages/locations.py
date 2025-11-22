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
    tab_list, tab_add, tab_edit = st.tabs([
        "📋 Lista de Locais",
        "➕ Adicionar Local",
        "✏️ Editar/Eliminar"
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
    
    # === TAB: EDITAR/ELIMINAR ===
    with tab_edit:
        st.subheader("✏️ Editar ou Eliminar Local")
        
        locations_df = data_manager.get_locations()
        
        if locations_df.empty:
            theme.show_info("Ainda não existem locais para editar")
        else:
            # Criar lista de opções com Localizacao (formula field)
            location_options = []
            for _, row in locations_df.iterrows():
                localizacao = row.get("Localizacao", "Sem localização")
                location_options.append(f"{localizacao}")
            
            selected_location = st.selectbox(
                "Selecione o local a editar:",
                location_options
            )
            
            if selected_location:
                # Encontrar o local selecionado
                selected_idx = location_options.index(selected_location)
                location_row = locations_df.iloc[selected_idx]
                selected_location_id = location_row["id"]
                
                with st.form("form_edit_location"):
                    st.markdown(f"**📍 Editando:** {selected_location}")
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        local_options = get_options_with_fallback("Local", "Local")
                        current_local = location_row.get("Local", "")
                        local_index = local_options.index(current_local) if current_local in local_options else 0
                        local = st.selectbox(
                            "🏢 Local *",
                            local_options,
                            index=local_index
                        )
                        
                        orientacao_options = get_options_with_fallback("Local", "Orientação no Local")
                        current_orientacao = location_row.get("Orientação no Local", "")
                        orientacao_index = orientacao_options.index(current_orientacao) if current_orientacao in orientacao_options else 0
                        orientacao = st.selectbox(
                            "🧭 Orientação no Local",
                            orientacao_options,
                            index=orientacao_index
                        )
                    
                    with col2:
                        contencao_options = get_options_with_fallback("Local", "Contencao")
                        current_contencao = location_row.get("Contencao", "")
                        contencao_index = contencao_options.index(current_contencao) if current_contencao in contencao_options else 0
                        contencao = st.selectbox(
                            "📦 Contenção",
                            contencao_options,
                            index=contencao_index
                        )
                    
                    notas = st.text_area(
                        "📝 Notas",
                        value=location_row.get("Notas", ""),
                        placeholder="Descrição adicional do local..."
                    )
                    
                    st.markdown("---")
                    
                    # Checkbox de confirmação para eliminação
                    confirm_delete = st.checkbox("⚠️ Confirmo que desejo eliminar este local")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        update_btn = st.form_submit_button(
                            "💾 Atualizar Local",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    with col_btn2:
                        delete_btn = st.form_submit_button(
                            "🗑️ Eliminar Local",
                            use_container_width=True,
                            type="secondary"
                        )
                    
                    if update_btn:
                        update_data = {
                            "Local": local,
                            "Orientação no Local": orientacao,
                            "Contencao": contencao,
                        }
                        
                        if notas:
                            update_data["Notas"] = notas
                        
                        with st.spinner("A atualizar..."):
                            result = data_manager.update_location(selected_location_id, update_data)
                            
                            if result:
                                theme.show_success("Local atualizado com sucesso!")
                                st.rerun()
                            else:
                                theme.show_error("Erro ao atualizar local")
                    
                    if delete_btn:
                        if not confirm_delete:
                            theme.show_warning("⚠️ Por favor, confirme a eliminação marcando a caixa acima")
                        else:
                            with st.spinner("A eliminar..."):
                                success = data_manager.delete_location(selected_location_id)
                                
                                if success:
                                    theme.show_success("Local eliminado com sucesso!")
                                    st.rerun()
                                else:
                                    theme.show_error("Erro ao eliminar local")

