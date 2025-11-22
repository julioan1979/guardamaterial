"""
Página de Relatórios
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.data_manager import DataManager
from src.ui import theme


def render(data_manager: DataManager):
    """Renderizar página de relatórios"""
    
    st.title("📊 Relatórios")
    st.markdown("Análises e relatórios detalhados do inventário")
    
    # Tabs
    tab_overview, tab_items, tab_movements, tab_export = st.tabs([
        "📈 Visão Geral",
        "📦 Análise de Itens",
        "🔄 Análise de Movimentos",
        "📥 Exportações"
    ])
    
    # Carregar dados
    items_df = data_manager.get_items()
    movements_df = data_manager.get_movements()
    locations_df = data_manager.get_locations()
    sections_df = data_manager.get_sections()
    
    # === TAB: VISÃO GERAL ===
    with tab_overview:
        st.subheader("📈 Resumo Executivo")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Itens", len(items_df))
        with col2:
            st.metric("🔄 Movimentos", len(movements_df))
        with col3:
            st.metric("📍 Locais", len(locations_df))
        with col4:
            st.metric("👥 Secções", len(sections_df))
        
        st.markdown("---")
        
        # Gráficos lado a lado
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Distribuição por Categoria")
            
            if not items_df.empty and "Categoria" in items_df.columns:
                category_data = items_df["Categoria"].value_counts().reset_index()
                category_data.columns = ["Categoria", "Quantidade"]
                
                fig = px.pie(
                    category_data,
                    values="Quantidade",
                    names="Categoria",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                theme.show_info("Sem dados disponíveis")
        
        with col_right:
            st.subheader("📈 Estado dos Materiais")
            
            if not items_df.empty and "Estado" in items_df.columns:
                state_data = items_df["Estado"].value_counts().reset_index()
                state_data.columns = ["Estado", "Quantidade"]
                
                fig = px.bar(
                    state_data,
                    x="Estado",
                    y="Quantidade",
                    text="Quantidade",
                    color="Quantidade",
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(height=350, showlegend=False)
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)
            else:
                theme.show_info("Sem dados disponíveis")
    
    # === TAB: ANÁLISE DE ITENS ===
    with tab_items:
        st.subheader("📦 Análise Detalhada de Itens")
        
        if items_df.empty:
            theme.show_info("Sem itens para analisar")
        else:
            # Filtros
            col_f1, col_f2 = st.columns(2)
            
            with col_f1:
                if "Categoria" in items_df.columns:
                    categories = ["Todas"] + sorted(items_df["Categoria"].dropna().unique().tolist())
                    filter_cat = st.selectbox("Filtrar por Categoria", categories)
                else:
                    filter_cat = "Todas"
            
            with col_f2:
                if "Estado" in items_df.columns:
                    states = ["Todos"] + sorted(items_df["Estado"].dropna().unique().tolist())
                    filter_state = st.selectbox("Filtrar por Estado", states)
                else:
                    filter_state = "Todos"
            
            # Aplicar filtros
            filtered_items = items_df.copy()
            
            if filter_cat != "Todas" and "Categoria" in filtered_items.columns:
                filtered_items = filtered_items[filtered_items["Categoria"] == filter_cat]
            
            if filter_state != "Todos" and "Estado" in filtered_items.columns:
                filtered_items = filtered_items[filtered_items["Estado"] == filter_state]
            
            st.markdown("---")
            
            # Tabela de top itens
            st.subheader("🔝 Itens com Maior Movimento")
            
            if "Entradas Totais" in filtered_items.columns:
                top_items = filtered_items.nlargest(10, "Entradas Totais")
                
                display_cols = []
                for col in ["Material", "Categoria", "Entradas Totais", "Saídas Totais", "Quantidade Atual"]:
                    if col in top_items.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        top_items[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                theme.show_info("Dados de movimentação não disponíveis")
            
            st.markdown("---")
            
            # Gráfico de quantidades
            st.subheader("📊 Quantidades por Item")
            
            if "Quantidade Atual" in filtered_items.columns and "Material" in filtered_items.columns:
                try:
                    qty_data = filtered_items[["Material", "Quantidade Atual"]].copy()
                    qty_data = qty_data.nlargest(15, "Quantidade Atual")
                    
                    fig = px.bar(
                        qty_data,
                        x="Material",
                        y="Quantidade Atual",
                        text="Quantidade Atual",
                        color="Quantidade Atual",
                        color_continuous_scale="Blues"
                    )
                    fig.update_layout(height=400, showlegend=False)
                    fig.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    theme.show_info("Não foi possível gerar o gráfico")
    
    # === TAB: ANÁLISE DE MOVIMENTOS ===
    with tab_movements:
        st.subheader("🔄 Análise de Movimentos")
        
        if movements_df.empty:
            theme.show_info("Sem movimentos para analisar")
        else:
            # Timeline de movimentos
            st.subheader("📅 Evolução de Movimentos ao Longo do Tempo")
            
            if "Data" in movements_df.columns:
                movements_df["Data"] = pd.to_datetime(movements_df["Data"], errors="coerce")
                movements_timeline = movements_df.dropna(subset=["Data"])
                
                if not movements_timeline.empty:
                    movements_timeline["Mês"] = movements_timeline["Data"].dt.to_period("M").astype(str)
                    monthly_data = movements_timeline.groupby("Mês").size().reset_index(name="Movimentos")
                    
                    fig = px.line(
                        monthly_data,
                        x="Mês",
                        y="Movimentos",
                        markers=True,
                        line_shape="spline"
                    )
                    fig.update_traces(line=dict(width=3))
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Análise por motivo
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Movimentos por Motivo")
                
                if "Motivo" in movements_df.columns:
                    motivo_data = movements_df["Motivo"].value_counts().reset_index()
                    motivo_data.columns = ["Motivo", "Quantidade"]
                    
                    fig = px.pie(
                        motivo_data,
                        values="Quantidade",
                        names="Motivo",
                        hole=0.3
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("👥 Movimentos por Secção")
                
                if "Secção" in movements_df.columns:
                    # Contar movimentos por secção
                    section_counts = {}
                    for _, mov in movements_df.iterrows():
                        seccoes = mov.get("Secção", [])
                        if isinstance(seccoes, list):
                            for sec_id in seccoes:
                                # Buscar nome da secção
                                sec_name = "Desconhecida"
                                if not sections_df.empty:
                                    sec_row = sections_df[sections_df["id"] == sec_id]
                                    if not sec_row.empty:
                                        sec_name = sec_row.iloc[0].get("Nome da Secção", "Desconhecida")
                                
                                section_counts[sec_name] = section_counts.get(sec_name, 0) + 1
                    
                    if section_counts:
                        sec_data = pd.DataFrame(list(section_counts.items()), columns=["Secção", "Movimentos"])
                        
                        fig = px.bar(
                            sec_data,
                            x="Secção",
                            y="Movimentos",
                            text="Movimentos",
                            color="Movimentos",
                            color_continuous_scale="Reds"
                        )
                        fig.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
    
    # === TAB: EXPORTAÇÕES ===
    with tab_export:
        st.subheader("📥 Exportar Dados")
        
        st.info("💡 Exporte os dados para análise externa em formato CSV")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📦 Itens")
            if not items_df.empty:
                csv_items = items_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Itens (CSV)",
                    data=csv_items,
                    file_name=f"inventario_itens_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.caption("Sem dados disponíveis")
            
            st.markdown("### 📍 Locais")
            if not locations_df.empty:
                csv_locations = locations_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Locais (CSV)",
                    data=csv_locations,
                    file_name=f"inventario_locais_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.caption("Sem dados disponíveis")
        
        with col2:
            st.markdown("### 🔄 Movimentos")
            if not movements_df.empty:
                csv_movements = movements_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Movimentos (CSV)",
                    data=csv_movements,
                    file_name=f"inventario_movimentos_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.caption("Sem dados disponíveis")
            
            st.markdown("### 👥 Secções")
            if not sections_df.empty:
                csv_sections = sections_df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Download Secções (CSV)",
                    data=csv_sections,
                    file_name=f"inventario_seccoes_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.caption("Sem dados disponíveis")
        
        st.markdown("---")
        
        # Exportação completa
        st.markdown("### 📦 Exportação Completa")
        st.markdown("Exporte todos os dados num único ficheiro ZIP")
        
        if st.button("📥 Gerar Exportação Completa", use_container_width=True):
            import io
            import zipfile
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                if not items_df.empty:
                    zip_file.writestr("itens.csv", items_df.to_csv(index=False))
                if not movements_df.empty:
                    zip_file.writestr("movimentos.csv", movements_df.to_csv(index=False))
                if not locations_df.empty:
                    zip_file.writestr("locais.csv", locations_df.to_csv(index=False))
                if not sections_df.empty:
                    zip_file.writestr("seccoes.csv", sections_df.to_csv(index=False))
            
            st.download_button(
                label="⬇️ Download ZIP Completo",
                data=zip_buffer.getvalue(),
                file_name=f"inventario_completo_{datetime.now().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                use_container_width=True
            )
