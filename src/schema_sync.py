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


def get_field_id(table_name: str, field_name: str) -> str:
    """
    Obter ID de um campo específico
    
    Args:
        table_name: Nome da tabela
        field_name: Nome do campo
        
    Returns:
        ID do campo ou string vazia se não encontrado
    """
    schema = get_airtable_schema()
    
    for table in schema.get('tables', []):
        if table['name'] == table_name:
            for field in table.get('fields', []):
                if field.get('name') == field_name:
                    return field.get('id', '')
    
    return ''


def add_select_option(table_name: str, field_name: str, new_option: str) -> bool:
    """
    Adicionar nova opção a um campo Single Select
    
    Args:
        table_name: Nome da tabela
        field_name: Nome do campo
        new_option: Nova opção a adicionar
        
    Returns:
        True se sucesso, False caso contrário
    """
    config = get_airtable_config()
    
    # Limpar cache antes de buscar schema para garantir dados atuais
    get_airtable_schema.clear()
    schema = get_airtable_schema()
    
    # Encontrar table_id e field_id
    table_id = None
    field_id = None
    current_choices = []
    
    for table in schema.get('tables', []):
        if table['name'] == table_name:
            table_id = table.get('id')
            for field in table.get('fields', []):
                if field.get('name') == field_name:
                    field_id = field.get('id')
                    current_choices = field.get('options', {}).get('choices', [])
                    break
            break
    
    if not table_id or not field_id:
        st.error(f"Campo {field_name} não encontrado na tabela {table_name}")
        return False
    
    # Verificar se opção já existe
    existing_names = [choice['name'] for choice in current_choices]
    if new_option in existing_names:
        st.warning(f"Opção '{new_option}' já existe!")
        return False
    
    # Preservar estrutura completa das choices existentes (com IDs e cores)
    # e adicionar nova opção com cor padrão (Airtable gera o ID automaticamente)
    new_choices = current_choices.copy()
    
    # Determinar cor padrão baseado nas opções existentes
    default_color = "blueLight2"  # Cor padrão do Airtable
    if current_choices and 'color' in current_choices[0]:
        # Usar a mesma cor da primeira opção existente
        default_color = current_choices[0].get('color', 'blueLight2')
    
    new_choices.append({
        "name": new_option,
        "color": default_color
    })
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "options": {
            "choices": new_choices
        }
    }
    
    # Debug: mostrar o que será enviado
    import json
    st.info(f"🔍 Debug - Enviando {len(new_choices)} opções para o Airtable")
    with st.expander("Ver payload completo"):
        st.json(payload)
    
    try:
        response = requests.patch(
            f"https://api.airtable.com/v0/meta/bases/{config['base_id']}/tables/{table_id}/fields/{field_id}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        # Limpar cache para forçar reload
        get_airtable_schema.clear()
        
        return True
    except requests.exceptions.HTTPError as e:
        error_msg = f"Erro HTTP {e.response.status_code}: {e.response.text}"
        st.error(f"Erro ao adicionar opção: {error_msg}")
        return False
    except Exception as e:
        st.error(f"Erro ao adicionar opção: {e}")
        return False


def remove_select_option(table_name: str, field_name: str, option_to_remove: str) -> bool:
    """
    Remover opção de um campo Single Select
    
    Args:
        table_name: Nome da tabela
        field_name: Nome do campo
        option_to_remove: Opção a remover
        
    Returns:
        True se sucesso, False caso contrário
    """
    config = get_airtable_config()
    
    # Limpar cache antes de buscar schema para garantir dados atuais
    get_airtable_schema.clear()
    schema = get_airtable_schema()
    
    # Encontrar table_id e field_id
    table_id = None
    field_id = None
    current_choices = []
    
    for table in schema.get('tables', []):
        if table['name'] == table_name:
            table_id = table.get('id')
            for field in table.get('fields', []):
                if field.get('name') == field_name:
                    field_id = field.get('id')
                    current_choices = field.get('options', {}).get('choices', [])
                    break
            break
    
    if not table_id or not field_id:
        st.error(f"Campo {field_name} não encontrado na tabela {table_name}")
        return False
    
    # Remover opção da lista
    new_choices = [choice for choice in current_choices if choice['name'] != option_to_remove]
    
    if len(new_choices) == len(current_choices):
        st.warning(f"Opção '{option_to_remove}' não encontrada!")
        return False
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "options": {
            "choices": new_choices
        }
    }
    
    try:
        response = requests.patch(
            f"https://api.airtable.com/v0/meta/bases/{config['base_id']}/tables/{table_id}/fields/{field_id}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        # Limpar cache para forçar reload
        get_airtable_schema.clear()
        
        return True
    except requests.exceptions.HTTPError as e:
        error_msg = f"Erro HTTP {e.response.status_code}: {e.response.text}"
        st.error(f"Erro ao remover opção: {error_msg}")
        return False
    except Exception as e:
        st.error(f"Erro ao remover opção: {e}")
        return False
