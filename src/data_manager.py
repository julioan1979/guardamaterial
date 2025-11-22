"""
Gestor de dados e integração com Airtable
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
from pyairtable import Table
from datetime import datetime

from src.config import get_airtable_config, TABLES, CACHE_TTL


class DataManager:
    """Classe para gerir dados do Airtable com cache"""
    
    def __init__(self):
        self.config = get_airtable_config()
        self._tables_cache = {}
    
    def get_table(self, table_name: str) -> Table:
        """Obter instância da tabela do Airtable com cache"""
        if table_name not in self._tables_cache:
            self._tables_cache[table_name] = Table(
                self.config["api_key"],
                self.config["base_id"],
                table_name
            )
        return self._tables_cache[table_name]
    
    @st.cache_data(ttl=CACHE_TTL, show_spinner=False)
    def load_table_data(_self, table_name: str) -> pd.DataFrame:
        """Carregar dados de uma tabela com cache"""
        try:
            table = _self.get_table(table_name)
            records = table.all()
            return _self._records_to_dataframe(records)
        except Exception as e:
            st.error(f"Erro ao carregar {table_name}: {e}")
            return pd.DataFrame()
    
    def _records_to_dataframe(self, records: List[Dict]) -> pd.DataFrame:
        """Converter registos Airtable para DataFrame"""
        if not records:
            return pd.DataFrame()
        
        rows = []
        for record in records:
            row = {"id": record["id"]}
            row.update(record.get("fields", {}))
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def clear_cache(self):
        """Limpar cache de dados"""
        self.load_table_data.clear()
    
    # === ITENS ===
    
    def get_items(self, reload: bool = False) -> pd.DataFrame:
        """Obter todos os itens"""
        if reload:
            self.clear_cache()
        return self.load_table_data(TABLES["ITEMS"])
    
    def create_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar novo item"""
        try:
            table = self.get_table(TABLES["ITEMS"])
            result = table.create(data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao criar item: {e}")
            return {}
    
    def update_item(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar item existente"""
        try:
            table = self.get_table(TABLES["ITEMS"])
            result = table.update(record_id, data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao atualizar item: {e}")
            return {}
    
    def delete_item(self, record_id: str) -> bool:
        """Eliminar item"""
        try:
            table = self.get_table(TABLES["ITEMS"])
            table.delete(record_id)
            self.clear_cache()
            return True
        except Exception as e:
            st.error(f"Erro ao eliminar item: {e}")
            return False
    
    # === MOVIMENTOS ===
    
    def get_movements(self, reload: bool = False) -> pd.DataFrame:
        """Obter todos os movimentos"""
        if reload:
            self.clear_cache()
        return self.load_table_data(TABLES["MOVEMENTS"])
    
    def create_movement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar novo movimento"""
        try:
            table = self.get_table(TABLES["MOVEMENTS"])
            result = table.create(data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao criar movimento: {e}")
            return {}
    
    # === LOCAIS ===
    
    def get_locations(self, reload: bool = False) -> pd.DataFrame:
        """Obter todos os locais"""
        if reload:
            self.clear_cache()
        return self.load_table_data(TABLES["LOCATIONS"])
    
    def create_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar novo local"""
        try:
            table = self.get_table(TABLES["LOCATIONS"])
            result = table.create(data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao criar local: {e}")
            return {}
    
    def update_location(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualizar local"""
        try:
            table = self.get_table(TABLES["LOCATIONS"])
            result = table.update(record_id, data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao atualizar local: {e}")
            return {}
    
    def delete_location(self, record_id: str) -> bool:
        """Eliminar local"""
        try:
            table = self.get_table(TABLES["LOCATIONS"])
            table.delete(record_id)
            self.clear_cache()
            return True
        except Exception as e:
            st.error(f"Erro ao eliminar local: {e}")
            return False
    
    # === SECÇÕES ===
    
    def get_sections(self, reload: bool = False) -> pd.DataFrame:
        """Obter todas as secções"""
        if reload:
            self.clear_cache()
        return self.load_table_data(TABLES["SECTIONS"])
    
    def create_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar nova secção"""
        try:
            table = self.get_table(TABLES["SECTIONS"])
            result = table.create(data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao criar secção: {e}")
            return {}
    
    # === UTILIZADORES ===
    
    def get_users(self, reload: bool = False) -> pd.DataFrame:
        """Obter todos os utilizadores"""
        if reload:
            self.clear_cache()
        df = self.load_table_data(TABLES["USERS"])
        # Remover campo de password por segurança
        if "Palavra-passe" in df.columns:
            df = df.drop(columns=["Palavra-passe"])
        return df
    
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Criar novo utilizador"""
        try:
            table = self.get_table(TABLES["USERS"])
            result = table.create(data)
            self.clear_cache()
            return result
        except Exception as e:
            st.error(f"Erro ao criar utilizador: {e}")
            return {}
    
    # === ESTATÍSTICAS ===
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obter estatísticas gerais do sistema"""
        items_df = self.get_items()
        movements_df = self.get_movements()
        locations_df = self.get_locations()
        sections_df = self.get_sections()
        
        stats = {
            "total_items": len(items_df),
            "total_movements": len(movements_df),
            "total_locations": len(locations_df),
            "total_sections": len(sections_df),
            "total_quantity": 0,
            "low_stock_items": 0,
            "categories": []
        }
        
        if not items_df.empty:
            # Quantidade total
            if "Quantidade Atual" in items_df.columns:
                try:
                    stats["total_quantity"] = items_df["Quantidade Atual"].sum()
                except Exception:
                    pass
            
            # Categorias
            if "Categoria" in items_df.columns:
                stats["categories"] = items_df["Categoria"].value_counts().to_dict()
        
        return stats
