# Configuração do PDF Data Extractor

Este documento descreve o processo de instalação e configuração do PDF Data Extractor.

## Requisitos do Sistema

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Tesseract OCR (para extração de texto via OCR)
- Java Runtime Environment (para tabula-py)
- Acesso à internet para download de dependências

### Requisitos de Hardware Recomendados

- Processador: Intel Core i5 ou equivalente (ou superior)
- RAM: Mínimo de 8GB (16GB recomendado para processamento em lote)
- Espaço em disco: 500MB para a aplicação + espaço para armazenar PDFs e dados extraídos

## Instalação

### 1. Clone o Repositório

git clone https://github.com/seu-usuario/pdf-extractor.git
cd pdf-extractor

text

### 2. Crie e Ative um Ambiente Virtual

#### No Windows:
python -m venv venv
venv\Scripts\activate

text

#### No macOS/Linux:
python3 -m venv venv
source venv/bin/activate

text

### 3. Instale as Dependências

pip install -r requirements.txt

text

### 4. Instale o Tesseract OCR

#### No Windows:
1. Baixe o instalador do [Tesseract OCR para Windows](https://github.com/UB-Mannheim/tesseract/wiki)
2. Execute o instalador e siga as instruções
3. Adicione o diretório de instalação ao PATH do sistema ou configure o caminho no arquivo config.json

#### No macOS:
brew install tesseract

text

#### No Linux (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev

text

### 5. Instale o Java Runtime Environment (JRE)

#### No Windows:
1. Baixe o [JRE](https://www.java.com/download/)
2. Execute o instalador e siga as instruções
3. Adicione o diretório de instalação do Java ao PATH do sistema

#### No macOS:
brew install java

text

#### No Linux (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install default-jre

text

### 6. Configuração

1. Copie o arquivo `config.example.json` para `config.json`
2. Edite `config.json` e ajuste as configurações conforme necessário:
   - `download_dir`: Diretório para salvar PDFs baixados
   - `export_dir`: Diretório para salvar dados exportados
   - `template_dir`: Diretório contendo templates de extração
   - `schema_dir`: Diretório contendo esquemas de validação
   - `tesseract_path`: Caminho para o executável do Tesseract OCR (se não estiver no PATH)

### 7. Teste a Instalação

Execute o script de teste para verificar se tudo está configurado corretamente:

python -m unittest discover tests

text

Se todos os testes passarem, a instalação foi bem-sucedida.

## Solução de Problemas

- Se o Tesseract OCR não for encontrado, verifique se o caminho está correto em `config.json` ou se está no PATH do sistema.
- Se houver problemas com o tabula-py, verifique se o Java está instalado corretamente e acessível pelo sistema.
- Para problemas de dependências Python, tente reinstalar as dependências com `pip install -r requirements.txt --upgrade`.

## Próximos Passos

Após a instalação, consulte o arquivo `usage.md` para instruções sobre como usar o PDF Data Extractor.