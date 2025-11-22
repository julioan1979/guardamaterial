"""
Página de Gestão de Secções
"""
import streamlit as st
import pandas as pd

from src.data_manager import DataManager
from src.ui import theme


def render(data_manager: DataManager):
    """Renderizar página de secções"""
    
    st.title("👥 Gestão de Secções")
    st.markdown("Gerir secções do agrupamento de escuteiros")
    
    # Tabs
    tab_list, tab_add = st.tabs([
        "📋 Lista de Secções",
        "➕ Adicionar Secção"
    ])
    
    # === TAB: LISTA ===
    with tab_list:
        st.subheader("📋 Todas as Secções")
        
        sections_df = data_manager.get_sections()
        
        if sections_df.empty:
            theme.show_info("Ainda não existem secções registadas")
        else:
            st.metric("Total de Secções", len(sections_df))
            
            st.markdown("---")
            
            # Mostrar tabela
            display_cols = []
            for col in ["Nome da Secção", "Usuários", "Observações", "Movimentos"]:
                if col in sections_df.columns:
                    display_cols.append(col)
            
            if display_cols:
                st.dataframe(
                    sections_df[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
            else:
                st.dataframe(sections_df, use_container_width=True, hide_index=True, height=400)
            
            # Estatísticas por secção
            st.markdown("---")
            st.subheader("📊 Estatísticas por Secção")
            
            movements_df = data_manager.get_movements()
            
            if not movements_df.empty and "Secção" in movements_df.columns:
                # Contar movimentos por secção
                section_counts = {}
                for _, mov in movements_df.iterrows():
                    seccoes = mov.get("Secção", [])
                    if isinstance(seccoes, list):
                        for sec_id in seccoes:
                            section_counts[sec_id] = section_counts.get(sec_id, 0) + 1
                
                # Criar dataframe com estatísticas
                stats_data = []
                for _, sec in sections_df.iterrows():
                    sec_id = sec["id"]
                    sec_name = sec.get("Nome da Secção", "Sem nome")
                    mov_count = section_counts.get(sec_id, 0)
                    
                    stats_data.append({
                        "Secção": sec_name,
                        "Movimentos": mov_count
                    })
                
                if stats_data:
                    stats_df = pd.DataFrame(stats_data)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.dataframe(
                            stats_df.sort_values("Movimentos", ascending=False),
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        import plotly.express as px
                        fig = px.bar(
                            stats_df,
                            x="Secção",
                            y="Movimentos",
                            text="Movimentos"
                        )
                        fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig, use_container_width=True)
    
    # === TAB: ADICIONAR ===
    with tab_add:
        st.subheader("➕ Adicionar Nova Secção")
        
        with st.form("form_add_section", clear_on_submit=True):
            nome = st.text_input(
                "📝 Nome da Secção *",
                placeholder="Ex: Lobitos, Exploradores, Pioneiros..."
            )
            
            observacoes = st.text_area(
                "📝 Observações",
                placeholder="Informações adicionais sobre a secção..."
            )
            
            st.markdown("---")
            
            submitted = st.form_submit_button(
                "💾 Guardar Secção",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not nome:
                    theme.show_error("O nome da secção é obrigatório!")
                else:
                    section_data = {
                        "Nome da Secção": nome,
                    }
                    
                    if observacoes:
                        section_data["Observações"] = observacoes
                    
                    with st.spinner("A guardar secção..."):
                        result = data_manager.create_section(section_data)
                        
                        if result:
                            theme.show_success(f"Secção '{nome}' criada com sucesso!")
                            st.rerun()
                        else:
                            theme.show_error("Erro ao criar secção")
