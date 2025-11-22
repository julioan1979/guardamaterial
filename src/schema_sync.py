"""
Módulo para sincronizar opções de campos Single Select com Airtable
"""
import requests
import streamlit as st
from typing import Dict, List
from src.config import get_airtable_config


@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_airtable_schema() -> Dict:
    """Obter schema completo das tabelas do Airtable"""
    config = get_airtable_config()
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
    }
    
    try:
        response = requests.get(
            f"https://api.airtable.com/v0/meta/bases/{config['base_id']}/tables",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao obter schema do Airtable: {e}")
        return {"tables": []}


def get_select_options(table_name: str, field_name: str) -> List[str]:
    """
    Obter opções disponíveis para um campo Single Select ou Multiple Select
    
    Args:
        table_name: Nome da tabela no Airtable
        field_name: Nome do campo
        
    Returns:
        Lista de opções disponíveis
    """
    schema = get_airtable_schema()
    
    for table in schema.get('tables', []):
        if table['name'] == table_name:
            for field in table.get('fields', []):
                if field.get('name') == field_name:
                    field_type = field.get('type')
                    
                    if field_type in ['singleSelect', 'multipleSelects']:
                        choices = field.get('options', {}).get('choices', [])
                        return [choice['name'] for choice in choices]
    
    return []


def get_all_table_options(table_name: str) -> Dict[str, List[str]]:
    """
    Obter todas as opções de campos Single/Multiple Select de uma tabela
    
    Args:
        table_name: Nome da tabela no Airtable
        
    Returns:
        Dicionário {campo: [opções]}
    """
    schema = get_airtable_schema()
    options_dict = {}
    
    for table in schema.get('tables', []):
        if table['name'] == table_name:
            for field in table.get('fields', []):
                field_name = field.get('name')
                field_type = field.get('type')
                
                if field_type in ['singleSelect', 'multipleSelects']:
                    choices = field.get('options', {}).get('choices', [])
                    options_dict[field_name] = [choice['name'] for choice in choices]
    
    return options_dict


# Mapeamento de opções por tabela (cache estático como fallback)
FALLBACK_OPTIONS = {
    "Itens": {
        "Categoria": [
            "Cozinha",
            "Serviço", 
            "Limpeza",
            "Cozinha/Serviço (Geral)",
            "Consumíveis – Bebidas",
            "Consumíveis – Alimentos",
            "Outro"
        ],
        "Estado": [
            "Ativo",
            "Perdido",
            "Em uso",
            "Substituído"
        ],
        "Unidade": [
            "lts",
            "und",
            "grs",
            "kg"
        ]
    },
    "Movimentos": {
        "Motivo": [
            "Uso ( baixa no stock )",
            "Outro ( baixa no stock )",
            "Compra ( entrada no stock )",
            "Transferência ( baixa no stock )",
            "Transferência ( entrada no stock )",
            "Doação ( baixa no stock )",
            "Doação ( entrada no stock )",
            "Descarte (baixa no stock )",
            "Empréstimo (baixa no stock )",
            "Retorno ( entrada no stock )",
            "Venda ( baixa no stock )",
            "Ajuste de estoque ( entrada no stock )"
        ]
    },
    "Local": {
        "Local": [
            "Capela da Penha"
        ],
        "Orientação no Local": [
            "Direita do Altar"
        ],
        "Contencao": [
            "Caixa Nº 1"
        ]
    },
    "Usuarios": {
        "Função": [
            "Administrador",
            "Chefe",
            "CCP",
            "Outro"
        ]
    }
}


def get_options_with_fallback(table_name: str, field_name: str) -> List[str]:
    """
    Obter opções com fallback para valores estáticos
    
    Tenta obter do Airtable primeiro, se falhar usa valores de fallback
    """
    try:
        options = get_select_options(table_name, field_name)
        if options:
            return options
    except Exception:
        pass
    
    # Fallback
    return FALLBACK_OPTIONS.get(table_name, {}).get(field_name, [])
