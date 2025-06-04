import re
import json
import pandas as pd
from datetime import datetime
from ..utils.logger import get_logger
from ..models.validation_schema import ValidationSchema

logger = get_logger(__name__)

class DataValidator:
    """Valida os dados extraídos de documentos"""
    
    def __init__(self, schema_dir=None):
        self.schema_dir = schema_dir
        self.schemas = {}
        self.load_schemas()
    
    def load_schemas(self):
        """Carrega esquemas de validação do diretório de esquemas"""
        if not self.schema_dir:
            return
        
        import os
        if not os.path.exists(self.schema_dir):
            logger.warning(f"Diretório de esquemas não encontrado: {self.schema_dir}")
            return
        
        try:
            for file in os.listdir(self.schema_dir):
                if file.endswith('.json'):
                    schema_path = os.path.join(self.schema_dir, file)
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema_data = json.load(f)
                        schema_name = os.path.splitext(file)[0]
                        self.schemas[schema_name] = ValidationSchema(**schema_data)
            
            logger.info(f"Carregados {len(self.schemas)} esquemas de validação")
        except Exception as e:
            logger.error(f"Erro ao carregar esquemas de validação: {str(e)}")
    
    def validate_field(self, value, field_type, options=None):
        """Valida um campo individual com base em seu tipo"""
        if value is None:
            return True, None
        
        options = options or {}
        error = None
        
        try:
            if field_type == 'string':
                # Validar string
                if not isinstance(value, str):
                    error = "Valor deve ser uma string"
                elif 'min_length' in options and len(value) < options['min_length']:
                    error = f"String muito curta (mínimo: {options['min_length']})"
                elif 'max_length' in options and len(value) > options['max_length']:
                    error = f"String muito longa (máximo: {options['max_length']})"
                elif 'pattern' in options and not re.match(options['pattern'], value):
                    error = f"String não corresponde ao padrão esperado"
            
            elif field_type == 'number' or field_type == 'decimal':
                # Converter para número se for string
                if isinstance(value, str):
                    value = value.replace(',', '.')
                    try:
                        value = float(value)
                    except ValueError:
                        error = "Não é possível converter para número"
                
                # Validar número
                if not isinstance(value, (int, float)):
                    error = "Valor deve ser um número"
                elif 'min' in options and value < options['min']:
                    error = f"Número muito pequeno (mínimo: {options['min']})"
                elif 'max' in options and value > options['max']:
                    error = f"Número muito grande (máximo: {options['max']})"
            
            elif field_type == 'integer':
                # Converter para inteiro se for string
                if isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError:
                        error = "Não é possível converter para inteiro"
                
                # Validar inteiro
                if not isinstance(value, int):
                    error = "Valor deve ser um inteiro"
                elif 'min' in options and value < options['min']:
                    error = f"Inteiro muito pequeno (mínimo: {options['min']})"
                elif 'max' in options and value > options['max']:
                    error = f"Inteiro muito grande (máximo: {options['max']})"
            
            elif field_type == 'date':
                # Converter para data se for string
                if isinstance(value, str):
                    try:
                        if 'format' in options:
                            value = datetime.strptime(value, options['format'])
                        else:
                            # Tenta formatos comuns
                            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                                try:
                                    value = datetime.strptime(value, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                error = "Formato de data não reconhecido"
                    except ValueError:
                        error = f"Data inválida"
                
                # Validar data
                if not isinstance(value, datetime):
                    error = "Valor deve ser uma data"
                elif 'min_date' in options:
                    min_date = datetime.strptime(options['min_date'], '%Y-%m-%d')
                    if value < min_date:
                        error = f"Data anterior ao mínimo permitido ({options['min_date']})"
                elif 'max_date' in options:
                    max_date = datetime.strptime(options['max_date'], '%Y-%m-%d')
                    if value > max_date:
                        error = f"Data posterior ao máximo permitido ({options['max_date']})"
            
            elif field_type == 'boolean':
                # Converter para booleano se for string
                if isinstance(value, str):
                    value = value.lower()
                    if value in ['true', 'yes', 'sim', '1', 'verdadeiro']:
                        value = True
                    elif value in ['false', 'no', 'não', '0', 'falso']:
                        value = False
                    else:
                        error = "Não é possível converter para booleano"
                
                # Validar booleano
                if not isinstance(value, bool):
                    error = "Valor deve ser um booleano"
            
            elif field_type == 'email':
                # Validar email
                if not isinstance(value, str):
                    error = "Email deve ser uma string"
                elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                    error = "Email inválido"
            
            elif field_type == 'cpf':
                # Validar CPF
                if not isinstance(value, str):
                    error = "CPF deve ser uma string"
                else:
                    # Remove caracteres não numéricos
                    cpf = re.sub(r'\D', '', value)
                    
                    # Verifica se tem 11 dígitos
                    if len(cpf) != 11:
                        error = "CPF deve ter 11 dígitos"
                    # Verifica se todos os dígitos são iguais
                    elif len(set(cpf)) == 1:
                        error = "CPF inválido"
                    else:
                        # Validação do primeiro dígito verificador
                        soma = 0
                        for i in range(9):
                            soma += int(cpf[i]) * (10 - i)
                        resto = soma % 11
                        digito1 = 0 if resto < 2 else 11 - resto
                        
                        if digito1 != int(cpf[9]):
                            error = "CPF inválido"
                        else:
                            # Validação do segundo dígito verificador
                            soma = 0
                            for i in range(10):
                                soma += int(cpf[i]) * (11 - i)
                            resto = soma % 11
                            digito2 = 0 if resto < 2 else 11 - resto
                            
                            if digito2 != int(cpf[10]):
                                error = "CPF inválido"
            
            elif field_type == 'cnpj':
                # Validar CNPJ
                if not isinstance(value, str):
                    error = "CNPJ deve ser uma string"
                else:
                    # Remove caracteres não numéricos
                    cnpj = re.sub(r'\D', '', value)
                    
                    # Verifica se tem 14 dígitos
                    if len(cnpj) != 14:
                        error = "CNPJ deve ter 14 dígitos"
                    # Verifica se todos os dígitos são iguais
                    elif len(set(cnpj)) == 1:
                        error = "CNPJ inválido"
                    else:
                        # Validação do primeiro dígito verificador
                        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
                        soma = 0
                        for i in range(12):
                            soma += int(cnpj[i]) * pesos[i]
                        resto = soma % 11
                        digito1 = 0 if resto < 2 else 11 - resto
                        
                        if digito1 != int(cnpj[12]):
                            error = "CNPJ inválido"
                        else:
                            # Validação do segundo dígito verificador
                            pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
                            soma = 0
                            for i in range(13):
                                soma += int(cnpj[i]) * pesos[i]
                            resto = soma % 11
                            digito2 = 0 if resto < 2 else 11 - resto
                            
                            if digito2 != int(cnpj[13]):
                                error = "CNPJ inválido"
            
            elif field_type == 'enum':
                # Validar enum (valor deve estar em uma lista de opções)
                if 'values' not in options:
                    error = "Opções de enum não definidas"
                elif value not in options['values']:
                    error = f"Valor deve ser um dos seguintes: {', '.join(options['values'])}"
            
            else:
                # Tipo desconhecido
                error = f"Tipo de campo desconhecido: {field_type}"
        
        except Exception as e:
            error = f"Erro na validação: {str(e)}"
        
        return error is None, error
    
    def validate_data(self, data, schema_name=None, schema=None):
        """Valida os dados extraídos contra um esquema"""
        # Determina o esquema a ser usado
        if schema is None:
            if schema_name and schema_name in self.schemas:
                schema = self.schemas[schema_name]
            else:
                logger.error(f"Esquema não encontrado: {schema_name}")
                return False, {"error": f"Esquema não encontrado: {schema_name}"}
        
        if not schema:
            logger.error("Nenhum esquema fornecido para validação")
            return False, {"error": "Nenhum esquema fornecido para validação"}
        
        # Inicializa resultados
        validation_results = {
            "valid": True,
            "errors": {},
            "warnings": {}
        }
        
        # Converte DataFrame para dicionário se necessário
        if isinstance(data, pd.DataFrame):
            # Se for um DataFrame com uma única linha, converte para dict
            if len(data) == 1:
                data = data.iloc[0].to_dict()
            else:
                # Valida cada linha do DataFrame
                all_valid = True
                row_results = []
                
                for i, row in data.iterrows():
                    row_valid, row_result = self.validate_data(row.to_dict(), schema_name, schema)
                    if not row_valid:
                        all_valid = False
                    row_results.append(row_result)
                
                validation_results["valid"] = all_valid
                validation_results["row_results"] = row_results
                return all_valid, validation_results
        
        # Valida campos obrigatórios
        for field_name, field_schema in schema.fields.items():
            if field_schema.required and (field_name not in data or data[field_name] is None or data[field_name] == ""):
                validation_results["valid"] = False
                validation_results["errors"][field_name] = "Campo obrigatório não preenchido"
        
        # Valida tipos e restrições de cada campo
        for field_name, value in data.items():
            # Ignora campos que não estão no esquema
            if field_name not in schema.fields:
                if schema.strict:
                    validation_results["warnings"][field_name] = "Campo não definido no esquema"
                continue
            
            field_schema = schema.fields[field_name]
            
            # Valida o campo
            valid, error = self.validate_field(
                value, 
                field_schema.type, 
                field_schema.options
            )
            
            if not valid:
                # Decide se é erro ou aviso com base na severidade
                if field_schema.required or field_schema.severity == "error":
                    validation_results["valid"] = False
                    validation_results["errors"][field_name] = error
                else:
                    validation_results["warnings"][field_name] = error
        
        # Executa validações personalizadas
        for validation in schema.custom_validations:
            try:
                # Avalia a condição (expressão Python simples)
                # Nota: isso é potencialmente inseguro, mas útil para validações complexas
                condition_result = eval(validation["condition"], {"data": data})
                
                if not condition_result:
                    if validation.get("severity", "error") == "error":
                        validation_results["valid"] = False
                        validation_results["errors"][validation["name"]] = validation["message"]
                    else:
                        validation_results["warnings"][validation["name"]] = validation["message"]
            except Exception as e:
                logger.error(f"Erro ao executar validação personalizada '{validation['name']}': {str(e)}")
                validation_results["warnings"][validation["name"]] = f"Erro na validação: {str(e)}"
        
        return validation_results["valid"], validation_results
