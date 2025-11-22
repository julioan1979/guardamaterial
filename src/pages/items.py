"""
Página de Gestão de Itens
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.data_manager import DataManager
from src.ui import theme
from src.schema_sync import get_options_with_fallback


def render(data_manager: DataManager):
    """Renderizar página de gestão de itens"""
    
    st.title("📦 Gestão de Itens")
    st.markdown("Adicionar, editar e consultar itens do inventário")
    
    # Tabs para organizar funcionalidades
    tab_list, tab_add, tab_edit = st.tabs([
        "📋 Lista de Itens",
        "➕ Adicionar Novo",
        "✏️ Editar/Eliminar"
    ])
    
    # === TAB: LISTA DE ITENS ===
    with tab_list:
        st.subheader("📋 Todos os Itens")
        
        items_df = data_manager.get_items()
        
        if items_df.empty:
            theme.show_info("Ainda não existem itens registados. Use o separador 'Adicionar Novo' para criar o primeiro item!")
        else:
            # Filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                search_term = st.text_input("🔍 Pesquisar", placeholder="Nome do material...")
            
            with col_f2:
                categories = ["Todas"] + sorted(items_df["Categoria"].dropna().unique().tolist())
                selected_category = st.selectbox("🏷️ Categoria", categories)
            
            with col_f3:
                states = ["Todos"] + sorted(items_df["Estado"].dropna().unique().tolist())
                selected_state = st.selectbox("📊 Estado", states)
            
            # Aplicar filtros
            filtered_df = items_df.copy()
            
            if search_term:
                mask = filtered_df.apply(
                    lambda row: search_term.lower() in str(row).lower(),
                    axis=1
                )
                filtered_df = filtered_df[mask]
            
            if selected_category != "Todas":
                filtered_df = filtered_df[filtered_df["Categoria"] == selected_category]
            
            if selected_state != "Todos":
                filtered_df = filtered_df[filtered_df["Estado"] == selected_state]
            
            # Estatísticas rápidas
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Total Filtrado", len(filtered_df))
            with col_s2:
                if "Quantidade Atual" in filtered_df.columns:
                    try:
                        total_qty = filtered_df["Quantidade Atual"].sum()
                        st.metric("Quantidade Total", f"{total_qty:.0f}")
                    except Exception:
                        st.metric("Quantidade Total", "N/A")
            with col_s3:
                st.metric("Total Geral", len(items_df))
            
            st.markdown("---")
            
            # Mostrar tabela
            if not filtered_df.empty:
                # Selecionar colunas para mostrar
                display_columns = []
                for col in ["Material", "Categoria", "Estado", "Unidade", "Quantidade Atual", "Entradas Totais", "Saídas Totais"]:
                    if col in filtered_df.columns:
                        display_columns.append(col)
                
                if display_columns:
                    st.dataframe(
                        filtered_df[display_columns],
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                else:
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=400)
                
                # Botão de exportar
                if st.button("📥 Exportar para CSV", key="export_items"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name=f"inventario_itens_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                theme.show_warning("Nenhum item encontrado com os filtros aplicados")
    
    # === TAB: ADICIONAR NOVO ===
    with tab_add:
        st.subheader("➕ Adicionar Novo Item")
        
        with st.form("form_add_item", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                material = st.text_input(
                    "📝 Nome do Material *",
                    placeholder="Ex: Corda de escalada"
                )
                
                # Obter opções dinâmicas do Airtable
                categorias = [""] + get_options_with_fallback("Itens", "Categoria")
                categoria = st.selectbox(
                    "🏷️ Categoria *",
                    categorias
                )
                
                estados = [""] + get_options_with_fallback("Itens", "Estado")
                estado = st.selectbox(
                    "📊 Estado *",
                    estados
                )
            
            with col2:
                unidades = [""] + get_options_with_fallback("Itens", "Unidade")
                unidade = st.selectbox(
                    "📏 Unidade *",
                    unidades
                )
                
                st.info("💡 **Nota:** A quantidade será controlada através dos movimentos de entrada/saída")
            
            st.markdown("---")
            
            submitted = st.form_submit_button(
                "💾 Guardar Item",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validações
                if not material:
                    theme.show_error("O nome do material é obrigatório!")
                elif not categoria:
                    theme.show_error("Por favor selecione uma categoria!")
                elif not estado:
                    theme.show_error("Por favor selecione um estado!")
                elif not unidade:
                    theme.show_error("Por favor selecione uma unidade!")
                else:
                    # Criar item
                    item_data = {
                        "Material": material,
                        "Categoria": categoria,
                        "Estado": estado,
                        "Unidade": unidade,
                    }
                    
                    with st.spinner("A guardar item..."):
                        result = data_manager.create_item(item_data)
                        
                        if result:
                            theme.show_success(f"Item '{material}' criado com sucesso!")
                            st.balloons()
                            st.rerun()
                        else:
                            theme.show_error("Erro ao criar item. Tente novamente.")
    
    # === TAB: EDITAR/ELIMINAR ===
    with tab_edit:
        st.subheader("✏️ Editar ou Eliminar Item")
        
        items_df = data_manager.get_items()
        
        if items_df.empty:
            theme.show_info("Não existem itens para editar")
        else:
            # Selecionar item
            item_options = {
                row["id"]: f"{row.get('Material', 'Sem nome')} ({row.get('Categoria', 'N/A')})"
                for _, row in items_df.iterrows()
            }
            
            selected_item_id = st.selectbox(
                "Selecione o item a editar:",
                options=list(item_options.keys()),
                format_func=lambda x: item_options[x]
            )
            
            if selected_item_id:
                item_row = items_df[items_df["id"] == selected_item_id].iloc[0]
                
                st.markdown("---")
                
                # Formulário de edição
                with st.form("form_edit_item"):
                    col1, col2 = st.columns(2)
                    
                    # Obter opções dinâmicas
                    categorias = get_options_with_fallback("Itens", "Categoria")
                    estados = get_options_with_fallback("Itens", "Estado")
                    unidades = get_options_with_fallback("Itens", "Unidade")
                    
                    with col1:
                        material = st.text_input(
                            "📝 Nome do Material",
                            value=item_row.get("Material", "")
                        )
                        
                        current_cat = item_row.get("Categoria", "")
                        cat_index = categorias.index(current_cat) if current_cat in categorias else 0
                        categoria = st.selectbox(
                            "🏷️ Categoria",
                            categorias,
                            index=cat_index
                        )
                    
                    with col2:
                        current_estado = item_row.get("Estado", "")
                        estado_index = estados.index(current_estado) if current_estado in estados else 0
                        estado = st.selectbox(
                            "📊 Estado",
                            estados,
                            index=estado_index
                        )
                        
                        current_unidade = item_row.get("Unidade", "")
                        unidade_index = unidades.index(current_unidade) if current_unidade in unidades else 0
                        unidade = st.selectbox(
                            "📏 Unidade",
                            unidades,
                            index=unidade_index
                        )
                    
                    st.markdown("---")
                    
                    # Checkbox de confirmação para eliminação
                    confirm_delete = st.checkbox("⚠️ Confirmo que desejo eliminar este item")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        update_btn = st.form_submit_button(
                            "💾 Atualizar Item",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    with col_btn2:
                        delete_btn = st.form_submit_button(
                            "🗑️ Eliminar Item",
                            use_container_width=True,
                            type="secondary"
                        )
                    
                    if update_btn:
                        update_data = {
                            "Material": material,
                            "Categoria": categoria,
                            "Estado": estado,
                            "Unidade": unidade,
                        }
                        
                        with st.spinner("A atualizar..."):
                            result = data_manager.update_item(selected_item_id, update_data)
                            
                            if result:
                                theme.show_success("Item atualizado com sucesso!")
                                st.rerun()
                            else:
                                theme.show_error("Erro ao atualizar item")
                    
                    if delete_btn:
                        if not confirm_delete:
                            theme.show_warning("⚠️ Por favor, confirme a eliminação marcando a caixa acima")
                        else:
                            with st.spinner("A eliminar..."):
                                success = data_manager.delete_item(selected_item_id)
                                
                                if success:
                                    theme.show_success("Item eliminado com sucesso!")
                                    st.rerun()
                                else:
                                    theme.show_error("Erro ao eliminar item")
