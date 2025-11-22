"""
Página Dashboard - Visão geral do sistema
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.data_manager import DataManager
from src.ui import theme


def render(data_manager: DataManager):
    """Renderizar página do dashboard"""
    
    st.title("🏠 Dashboard")
    st.markdown("Visão geral do inventário e estatísticas em tempo real")
    
    # Carregar dados
    with st.spinner("A carregar dados..."):
        stats = data_manager.get_statistics()
        items_df = data_manager.get_items()
        movements_df = data_manager.get_movements()
    
    # === MÉTRICAS PRINCIPAIS ===
    st.subheader("📊 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total de Itens",
            value=stats["total_items"],
            delta=None
        )
    
    with col2:
        st.metric(
            label="🔄 Movimentos",
            value=stats["total_movements"],
            delta=None
        )
    
    with col3:
        st.metric(
            label="📍 Locais",
            value=stats["total_locations"],
            delta=None
        )
    
    with col4:
        st.metric(
            label="👥 Secções",
            value=stats["total_sections"],
            delta=None
        )
    
    st.divider()
    
    # === GRÁFICOS ===
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📊 Itens por Categoria")
        
        if not items_df.empty and "Categoria" in items_df.columns:
            category_counts = items_df["Categoria"].value_counts().reset_index()
            category_counts.columns = ["Categoria", "Quantidade"]
            
            fig_categories = px.bar(
                category_counts,
                x="Categoria",
                y="Quantidade",
                text="Quantidade",
                color="Quantidade",
                color_continuous_scale="Blues"
            )
            fig_categories.update_layout(
                showlegend=False,
                height=350,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            fig_categories.update_traces(textposition="outside")
            st.plotly_chart(fig_categories, use_container_width=True)
        else:
            theme.show_info("Sem dados de categorias disponíveis")
    
    with col_right:
        st.subheader("📈 Estado dos Itens")
        
        if not items_df.empty and "Estado" in items_df.columns:
            state_counts = items_df["Estado"].value_counts().reset_index()
            state_counts.columns = ["Estado", "Quantidade"]
            
            fig_states = px.pie(
                state_counts,
                values="Quantidade",
                names="Estado",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_states.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_states, use_container_width=True)
        else:
            theme.show_info("Sem dados de estado disponíveis")
    
    st.divider()
    
    # === MOVIMENTOS RECENTES ===
    st.subheader("🔄 Movimentos Recentes")
    
    if not movements_df.empty:
        # Ordenar por data (mais recentes primeiro)
        if "Data" in movements_df.columns:
            movements_df["Data"] = pd.to_datetime(movements_df["Data"], errors="coerce")
            recent_movements = movements_df.sort_values("Data", ascending=False).head(10)
            
            # Mostrar tabela
            display_columns = []
            for col in ["Movimento", "Item", "Quantidade", "Data", "Motivo", "Secção"]:
                if col in recent_movements.columns:
                    display_columns.append(col)
            
            if display_columns:
                st.dataframe(
                    recent_movements[display_columns],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(recent_movements, use_container_width=True, hide_index=True)
        else:
            st.dataframe(movements_df.head(10), use_container_width=True, hide_index=True)
    else:
        theme.show_info("Ainda não existem movimentos registados")
    
    st.divider()
    
    # === GRÁFICO DE MOVIMENTOS POR MÊS ===
    st.subheader("📅 Movimentos por Mês")
    
    if not movements_df.empty and "Data" in movements_df.columns:
        movements_df["Data"] = pd.to_datetime(movements_df["Data"], errors="coerce")
        movements_df = movements_df.dropna(subset=["Data"])
        
        if not movements_df.empty:
            movements_df["Mês"] = movements_df["Data"].dt.to_period("M").astype(str)
            monthly_counts = movements_df.groupby("Mês").size().reset_index(name="Movimentos")
            
            fig_timeline = px.line(
                monthly_counts,
                x="Mês",
                y="Movimentos",
                markers=True,
                line_shape="spline"
            )
            fig_timeline.update_traces(
                line=dict(color="#667eea", width=3),
                marker=dict(size=10, color="#764ba2")
            )
            fig_timeline.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                hovermode="x unified"
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            theme.show_info("Sem dados de datas válidas")
    else:
        theme.show_info("Sem dados de movimentos disponíveis")
    
    # === ITENS COM STOCK BAIXO ===
    st.divider()
    st.subheader("⚠️ Alertas de Stock")
    
    if not items_df.empty and "Quantidade Atual" in items_df.columns:
        try:
            low_stock = items_df[items_df["Quantidade Atual"] < 5].copy()
            
            if not low_stock.empty:
                theme.show_warning(f"Existem {len(low_stock)} itens com stock baixo (< 5 unidades)")
                
                display_cols = []
                for col in ["Material", "Categoria", "Quantidade Atual", "Unidade"]:
                    if col in low_stock.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        low_stock[display_cols].sort_values("Quantidade Atual"),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                theme.show_success("Todos os itens têm stock adequado!")
        except Exception:
            theme.show_info("Não foi possível verificar o stock")
    else:
        theme.show_info("Sem dados de quantidade disponíveis")
