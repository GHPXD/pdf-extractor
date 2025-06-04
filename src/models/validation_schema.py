from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class FieldSchema:
    """Esquema para validação de um campo individual"""
    type: str  # string, number, integer, date, boolean, email, cpf, cnpj, enum
    required: bool = False
    severity: str = "error"  # error ou warning
    options: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

@dataclass
class ValidationSchema:
    """Esquema completo para validação de documentos"""
    name: str
    description: str
    version: str
    fields: Dict[str, FieldSchema]
    strict: bool = False  # Se True, campos não definidos no esquema geram avisos
    custom_validations: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Converte dicionários de campos para objetos FieldSchema"""
        converted_fields = {}
        for field_name, field_data in self.fields.items():
            if isinstance(field_data, dict):
                converted_fields[field_name] = FieldSchema(**field_data)
            else:
                converted_fields[field_name] = field_data
        self.fields = converted_fields