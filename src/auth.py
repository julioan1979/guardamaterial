"""
Sistema de autenticação de utilizadores
"""
from __future__ import annotations

import streamlit as st
import bcrypt
from datetime import datetime
from typing import Optional, Dict, Any

from src.config import get_airtable_config, TABLES
from pyairtable import Table


class Authenticator:
    """Classe para gestão de autenticação"""
    
    def __init__(self):
        self.config = get_airtable_config()
        if not self.config["api_key"] or not self.config["base_id"]:
            st.error("⚠️ Credenciais do Airtable não configuradas!")
            st.stop()
    
    def get_users_table(self) -> Table:
        """Obter tabela de utilizadores do Airtable"""
        return Table(
            self.config["api_key"],
            self.config["base_id"],
            self.config["users_table"]
        )
    
    def verify_credentials(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verificar credenciais do utilizador"""
        if not email or not password:
            return None
        
        try:
            table = self.get_users_table()
            # Buscar utilizador por email (escapar aspas)
            escaped_email = email.replace("'", "\\'")
            formula = f"{{Email}} = '{escaped_email}'"
            records = table.all(formula=formula, max_records=1)
            
            if not records:
                return None
            
            user_record = records[0]
            fields = user_record["fields"]
            
            # Verificar password
            stored_password = fields.get("Palavra-passe", "")
            
            # Tentar verificar com bcrypt primeiro
            try:
                if stored_password.startswith("$2"):  # Hash bcrypt
                    if bcrypt.checkpw(password.encode(), stored_password.encode()):
                        return self._prepare_user_data(user_record)
                else:
                    # Fallback para comparação direta (texto simples)
                    if password == stored_password:
                        return self._prepare_user_data(user_record)
            except Exception:
                # Se falhar, tentar comparação direta
                if password == stored_password:
                    return self._prepare_user_data(user_record)
            
            return None
            
        except Exception as e:
            st.error(f"Erro ao verificar credenciais: {e}")
            return None
    
    def _prepare_user_data(self, record: Dict) -> Dict[str, Any]:
        """Preparar dados do utilizador para sessão"""
        fields = record["fields"]
        return {
            "id": record["id"],
            "nome": fields.get("Nome do Usuário", "Utilizador"),
            "email": fields.get("Email", ""),
            "funcao": fields.get("Função", "Utilizador"),
            "telefone": fields.get("Telefone", ""),
            "seccoes": fields.get("Secções associadas", []),
            "authenticated": True,
            "login_time": datetime.now()
        }
    
    def check_authentication(self) -> bool:
        """Verificar se utilizador está autenticado"""
        return st.session_state.get("user", {}).get("authenticated", False)
    
    def logout(self):
        """Fazer logout do utilizador"""
        if "user" in st.session_state:
            del st.session_state["user"]
        st.rerun()
    
    def show_login_page(self):
        """Renderizar página de login"""
        
        # Centrar o conteúdo
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            # Logo/Título
            st.markdown("""
                <div style='text-align: center;'>
                    <h1>🎯</h1>
                    <h2>Gestão de Inventário</h2>
                    <h3>Escuteiros</h3>
                    <p>Sistema de gestão de stock e materiais</p>
                </div>
                <br>
            """, unsafe_allow_html=True)
            
            # Formulário de login
            with st.form("login_form", clear_on_submit=False):
                st.subheader("Iniciar Sessão")
                
                email = st.text_input(
                    "📧 Email",
                    placeholder="seu.email@exemplo.com",
                    key="login_email"
                )
                
                password = st.text_input(
                    "🔒 Palavra-passe",
                    type="password",
                    placeholder="••••••••",
                    key="login_password"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    login_button = st.form_submit_button(
                        "🚀 Entrar",
                        use_container_width=True,
                        type="primary"
                    )
                with col_b:
                    st.form_submit_button(
                        "❓ Esqueci a password",
                        use_container_width=True,
                        disabled=True
                    )
            
            if login_button:
                if not email or not password:
                    st.error("⚠️ Por favor, preencha todos os campos.")
                else:
                    with st.spinner("A verificar credenciais..."):
                        user = self.verify_credentials(email, password)
                        
                        if user:
                            st.session_state["user"] = user
                            st.success(f"✅ Bem-vindo(a), {user['nome']}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Email ou palavra-passe incorretos.")
            
            # Informação adicional
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.info("💡 **Dica:** Se não tem acesso, contacte o administrador do sistema.")


# Instância global do autenticador
authenticator = Authenticator()
