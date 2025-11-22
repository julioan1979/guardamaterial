"""
Página de Movimentos
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from src.data_manager import DataManager
from src.ui import theme
from src.schema_sync import get_options_with_fallback


def render(data_manager: DataManager):
    """Renderizar página de movimentos"""
    
    st.title("🔄 Movimentos")
    st.markdown("Registar entradas e saídas de materiais")
    
    # Tabs
    tab_list, tab_add = st.tabs([
        "📋 Histórico de Movimentos",
        "➕ Registar Movimento"
    ])
    
    # === TAB: HISTÓRICO ===
    with tab_list:
        st.subheader("📋 Histórico de Movimentos")
        
        movements_df = data_manager.get_movements()
        
        if movements_df.empty:
            theme.show_info("Ainda não existem movimentos registados")
        else:
            # Filtros
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                search = st.text_input("🔍 Pesquisar", placeholder="Item, motivo...")
            
            with col_f2:
                if "Motivo" in movements_df.columns:
                    motivos = ["Todos"] + sorted(movements_df["Motivo"].dropna().unique().tolist())
                    selected_motivo = st.selectbox("🎯 Motivo", motivos)
                else:
                    selected_motivo = "Todos"
            
            with col_f3:
                # Filtro por data
                date_filter = st.selectbox("📅 Período", [
                    "Todos",
                    "Último mês",
                    "Últimos 3 meses",
                    "Último ano"
                ])
            
            # Aplicar filtros
            filtered_df = movements_df.copy()
            
            if search:
                mask = filtered_df.apply(
                    lambda row: search.lower() in str(row).lower(),
                    axis=1
                )
                filtered_df = filtered_df[mask]
            
            if selected_motivo != "Todos" and "Motivo" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Motivo"] == selected_motivo]
            
            if date_filter != "Todos" and "Data" in filtered_df.columns:
                filtered_df["Data"] = pd.to_datetime(filtered_df["Data"], errors="coerce")
                today = pd.Timestamp.now()
                
                if date_filter == "Último mês":
                    filtered_df = filtered_df[filtered_df["Data"] >= (today - pd.DateOffset(months=1))]
                elif date_filter == "Últimos 3 meses":
                    filtered_df = filtered_df[filtered_df["Data"] >= (today - pd.DateOffset(months=3))]
                elif date_filter == "Último ano":
                    filtered_df = filtered_df[filtered_df["Data"] >= (today - pd.DateOffset(years=1))]
            
            # Métricas
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total Movimentos", len(filtered_df))
            with col_m2:
                if "Quantidade" in filtered_df.columns:
                    total_qty = filtered_df["Quantidade"].sum()
                    st.metric("Quantidade Total", f"{total_qty:.0f}")
            with col_m3:
                st.metric("Total Geral", len(movements_df))
            
            st.markdown("---")
            
            # Tabela
            if not filtered_df.empty:
                # Ordenar por data (mais recentes primeiro)
                if "Data" in filtered_df.columns:
                    filtered_df = filtered_df.sort_values("Data", ascending=False)
                
                # Colunas a mostrar
                display_cols = []
                for col in ["ID", "Movimento", "Item", "Quantidade", "Data", "Motivo", "Evento associado", "Responsável", "Secção", "Local"]:
                    if col in filtered_df.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        filtered_df[display_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=500
                    )
                else:
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=500)
                
                # Exportar
                if st.button("📥 Exportar para CSV"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name=f"movimentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                theme.show_warning("Nenhum movimento encontrado com os filtros aplicados")
    
    # === TAB: REGISTAR MOVIMENTO ===
    with tab_add:
        st.subheader("➕ Registar Novo Movimento")
        
        items_df = data_manager.get_items()
        locations_df = data_manager.get_locations()
        sections_df = data_manager.get_sections()
        
        if items_df.empty:
            theme.show_warning("Não existem itens registados. Crie primeiro um item na página 'Gestão de Itens'.")
            return
        
        with st.form("form_add_movement", clear_on_submit=True):
            # Selecionar item
            item_options = {
                row["id"]: f"{row.get('Material', 'Sem nome')} ({row.get('Categoria', 'N/A')})"
                for _, row in items_df.iterrows()
            }
            
            selected_item = st.selectbox(
                "📦 Item *",
                options=list(item_options.keys()),
                format_func=lambda x: item_options[x]
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                quantidade = st.number_input(
                    "📊 Quantidade *",
                    min_value=0.0,
                    value=1.0,
                    step=0.1
                )
                
                motivos = [""] + get_options_with_fallback("Movimentos", "Motivo")
                motivo = st.selectbox(
                    "🎯 Motivo *",
                    motivos
                )
                
                movimento_date = st.date_input(
                    "📅 Data *",
                    value=date.today()
                )
            
            with col2:
                evento = st.text_input(
                    "🎪 Evento Associado",
                    placeholder="Ex: Acampamento de Verão"
                )
                
                # Selecionar secção
                if not sections_df.empty:
                    section_options = {
                        row["id"]: row.get("Nome da Secção", "Sem nome")
                        for _, row in sections_df.iterrows()
                    }
                    section_options = {"": "Nenhuma"} | section_options
                    
                    selected_section = st.selectbox(
                        "👥 Secção",
                        options=list(section_options.keys()),
                        format_func=lambda x: section_options[x]
                    )
                else:
                    selected_section = ""
                
                # Selecionar local
                if not locations_df.empty:
                    location_options = {
                        row["id"]: row.get("Localizacao", row.get("Local", "Sem nome"))
                        for _, row in locations_df.iterrows()
                    }
                    location_options = {"": "Nenhum"} | location_options
                    
                    selected_location = st.selectbox(
                        "📍 Local",
                        options=list(location_options.keys()),
                        format_func=lambda x: location_options[x]
                    )
                else:
                    selected_location = ""
            
            notas = st.text_area(
                "📝 Notas",
                placeholder="Observações adicionais sobre este movimento..."
            )
            
            st.markdown("---")
            
            submitted = st.form_submit_button(
                "💾 Registar Movimento",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validações
                if not selected_item:
                    theme.show_error("Por favor selecione um item!")
                elif quantidade <= 0:
                    theme.show_error("A quantidade deve ser maior que zero!")
                elif not motivo:
                    theme.show_error("Por favor selecione um motivo!")
                else:
                    # Criar movimento
                    movement_data = {
                        "Item": [selected_item],
                        "Quantidade": quantidade,
                        "Motivo": motivo,
                        "Data": movimento_date.isoformat(),
                    }
                    
                    if evento:
                        movement_data["Evento associado"] = evento
                    
                    if selected_section:
                        movement_data["Secção"] = [selected_section]
                    
                    if selected_location:
                        movement_data["Local"] = [selected_location]
                    
                    if notas:
                        movement_data["Notas"] = notas
                    
                    # Adicionar responsável (utilizador autenticado)
                    if "user" in st.session_state:
                        user_id = st.session_state.user.get("id")
                        if user_id:
                            movement_data["Responsável"] = [user_id]
                    
                    with st.spinner("A registar movimento..."):
                        result = data_manager.create_movement(movement_data)
                        
                        if result:
                            theme.show_success("Movimento registado com sucesso!")
                            st.balloons()
                            st.rerun()
                        else:
                            theme.show_error("Erro ao registar movimento")
