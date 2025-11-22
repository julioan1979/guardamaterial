"""
Página de Administração
"""
import streamlit as st
import pandas as pd
import bcrypt

from src.data_manager import DataManager
from src.ui import theme
from src.config import USER_ROLES
from src.schema_sync import get_options_with_fallback


def render(data_manager: DataManager):
    """Renderizar página de administração"""
    
    st.title("⚙️ Administração")
    st.markdown("Configurações e gestão de utilizadores do sistema")
    
    # Verificar se utilizador tem permissões de admin
    user = st.session_state.get("user", {})
    user_role = user.get("funcao", "Utilizador")
    
    if user_role != "Administrador":
        theme.show_error("⛔ Acesso negado! Esta página é restrita a administradores.")
        return
    
    # Tabs
    tab_users, tab_options, tab_config, tab_logs = st.tabs([
        "👥 Utilizadores",
        "🏷️ Opções de Campos",
        "⚙️ Configurações",
        "📜 Registos"
    ])
    
    # === TAB: UTILIZADORES ===
    with tab_users:
        st.subheader("👥 Gestão de Utilizadores")
        
        users_df = data_manager.get_users()
        
        # Sub-tabs
        subtab_list, subtab_add = st.tabs([
            "📋 Lista de Utilizadores",
            "➕ Adicionar Utilizador"
        ])
        
        with subtab_list:
            if users_df.empty:
                theme.show_info("Sem utilizadores registados")
            else:
                st.metric("Total de Utilizadores", len(users_df))
                
                # Mostrar tabela
                display_cols = []
                for col in ["Nome do Usuário", "Email", "Função", "Telefone", "Secções associadas"]:
                    if col in users_df.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        users_df[display_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                else:
                    st.dataframe(users_df, use_container_width=True, hide_index=True, height=400)
                
                # Estatísticas por função
                st.markdown("---")
                st.subheader("📊 Utilizadores por Função")
                
                if "Função" in users_df.columns:
                    role_counts = users_df["Função"].value_counts().reset_index()
                    role_counts.columns = ["Função", "Quantidade"]
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.dataframe(
                            role_counts,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        import plotly.express as px
                        fig = px.pie(
                            role_counts,
                            values="Quantidade",
                            names="Função",
                            hole=0.4
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
        
        with subtab_add:
            st.markdown("### ➕ Adicionar Novo Utilizador")
            
            with st.form("form_add_user", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    nome = st.text_input(
                        "📝 Nome Completo *",
                        placeholder="João Silva"
                    )
                    
                    email = st.text_input(
                        "📧 Email *",
                        placeholder="joao.silva@exemplo.com"
                    )
                    
                    telefone = st.text_input(
                        "📞 Telefone",
                        placeholder="+351 912 345 678"
                    )
                
                with col2:
                    funcao_options = get_options_with_fallback("Usuarios", "Função")
                    funcao = st.selectbox(
                        "🎭 Função *",
                        [""] + funcao_options
                    )
                    
                    password = st.text_input(
                        "🔒 Palavra-passe *",
                        type="password",
                        placeholder="Mínimo 6 caracteres"
                    )
                    
                    password_confirm = st.text_input(
                        "🔒 Confirmar Palavra-passe *",
                        type="password"
                    )
                
                observacoes = st.text_area(
                    "📝 Observações",
                    placeholder="Informações adicionais..."
                )
                
                # Selecionar secções (se existirem)
                sections_df = data_manager.get_sections()
                selected_sections = []
                
                if not sections_df.empty:
                    st.markdown("**👥 Secções Associadas**")
                    section_options = {
                        row["id"]: row.get("Nome da Secção", "Sem nome")
                        for _, row in sections_df.iterrows()
                    }
                    
                    selected_sections = st.multiselect(
                        "Selecione as secções:",
                        options=list(section_options.keys()),
                        format_func=lambda x: section_options[x],
                        label_visibility="collapsed"
                    )
                
                st.markdown("---")
                
                submitted = st.form_submit_button(
                    "💾 Criar Utilizador",
                    use_container_width=True,
                    type="primary"
                )
                
                if submitted:
                    # Validações
                    if not nome or not email or not funcao or not password:
                        theme.show_error("Por favor preencha todos os campos obrigatórios!")
                    elif len(password) < 6:
                        theme.show_error("A palavra-passe deve ter no mínimo 6 caracteres!")
                    elif password != password_confirm:
                        theme.show_error("As palavras-passe não coincidem!")
                    else:
                        # Criar hash da password
                        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                        
                        user_data = {
                            "Nome do Usuário": nome,
                            "Email": email,
                            "Função": funcao,
                            "Palavra-passe": password_hash,
                        }
                        
                        if telefone:
                            user_data["Telefone"] = telefone
                        
                        if observacoes:
                            user_data["Observações"] = observacoes
                        
                        if selected_sections:
                            user_data["Secções associadas"] = selected_sections
                        
                        with st.spinner("A criar utilizador..."):
                            result = data_manager.create_user(user_data)
                            
                            if result:
                                theme.show_success(f"Utilizador '{nome}' criado com sucesso!")
                                st.balloons()
                                st.rerun()
                            else:
                                theme.show_error("Erro ao criar utilizador")
    
    # === TAB: OPÇÕES DE CAMPOS ===
    with tab_options:
        st.subheader("🏷️ Gestão de Opções de Campos")
        st.markdown("Visualize e adicione opções aos campos Single Select")
        
        st.info("""
        💡 **Recomendação**: Para adicionar/remover opções de forma mais confiável, use o Airtable diretamente:
        
        1. 📱 Abra: [airtable.com/appIQ3DP7p2EwI4PW](https://airtable.com/appIQ3DP7p2EwI4PW) (Base do Inventário)
        2. 🔍 Clique no nome do campo que deseja editar (ex: "Contenção", "Local")
        3. ⚙️ Selecione "Customize field type"
        4. ➕ Adicione ou remova opções na lista
        5. 💾 As alterações aparecem aqui automaticamente (cache de 1 hora)
        6. 🔄 Para atualização imediata: vá a **Configurações** → **Limpar Cache**
        
        *A funcionalidade via API abaixo é experimental e pode ter limitações.*
        """)
        
        st.markdown("---")
        st.markdown("### 🔍 Opções Disponíveis por Campo")
        
        # Selecionar tabela e campo
        col1, col2 = st.columns(2)
        
        with col1:
            table_options = {
                "Itens": ["Categoria", "Estado", "Unidade"],
                "Movimentos": ["Motivo"],
                "Local": ["Local", "Orientação no Local", "Contencao"],
                "Usuarios": ["Função"]
            }
            
            selected_table = st.selectbox(
                "📊 Selecione a Tabela",
                list(table_options.keys())
            )
        
        with col2:
            available_fields = table_options.get(selected_table, [])
            selected_field = st.selectbox(
                "🏷️ Selecione o Campo",
                available_fields
            )
        
        if selected_table and selected_field:
            st.markdown("---")
            
            # Importar funções adicionais do schema_sync
            from src.schema_sync import add_select_option, remove_select_option
            
            # Obter opções atuais
            current_options = get_options_with_fallback(selected_table, selected_field)
            
            # Mostrar opções atuais
            st.markdown(f"### 📋 Opções Atuais de **{selected_field}**")
            
            if current_options:
                col_metric, col_list = st.columns([1, 3])
                
                with col_metric:
                    st.metric("Total de Opções", len(current_options))
                
                with col_list:
                    for idx, option in enumerate(current_options, 1):
                        st.text(f"{idx}. {option}")
            else:
                theme.show_info("Nenhuma opção definida")
    
    # === TAB: CONFIGURAÇÕES ===
    with tab_config:
        st.subheader("⚙️ Configurações do Sistema")
        
        st.info("🔧 Configurações gerais da aplicação")
        
        # Informações do sistema
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Estatísticas do Sistema")
            stats = data_manager.get_statistics()
            
            st.metric("Total de Itens", stats["total_items"])
            st.metric("Total de Movimentos", stats["total_movements"])
            st.metric("Total de Locais", stats["total_locations"])
            st.metric("Total de Secções", stats["total_sections"])
        
        with col2:
            st.markdown("### 🔐 Perfis de Utilizador")
            
            for role, config in USER_ROLES.items():
                with st.expander(f"👤 {role}"):
                    st.write("**Permissões:**")
                    st.write(", ".join(config["permissions"]))
                    st.write("**Páginas permitidas:**")
                    if "all" in config["pages"]:
                        st.write("Todas as páginas")
                    else:
                        st.write(", ".join(config["pages"]))
        
        st.markdown("---")
        
        # Cache management
        st.markdown("### 🔄 Gestão de Cache")
        st.info("Limpe o cache para forçar o recarregamento de todos os dados")
        
        if st.button("🗑️ Limpar Cache", use_container_width=True):
            st.cache_data.clear()
            data_manager.clear_cache()
            theme.show_success("Cache limpa com sucesso!")
            st.rerun()
    
    # === TAB: REGISTOS ===
    with tab_logs:
        st.subheader("📜 Registos do Sistema")
        
        st.info("📝 Histórico de atividades recentes")
        
        # Mostrar movimentos recentes como log de atividade
        movements_df = data_manager.get_movements()
        
        if not movements_df.empty:
            st.markdown("### 🔄 Últimas Atividades")
            
            if "Data" in movements_df.columns:
                movements_df["Data"] = pd.to_datetime(movements_df["Data"], errors="coerce")
                recent_logs = movements_df.sort_values("Data", ascending=False).head(20)
                
                display_cols = []
                for col in ["ID", "Movimento", "Data", "Responsável", "Secção", "Motivo"]:
                    if col in recent_logs.columns:
                        display_cols.append(col)
                
                if display_cols:
                    st.dataframe(
                        recent_logs[display_cols],
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
            else:
                st.dataframe(movements_df.head(20), use_container_width=True, hide_index=True, height=400)
        else:
            theme.show_info("Sem registos de atividade")
