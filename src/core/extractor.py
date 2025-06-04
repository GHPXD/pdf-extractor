import PyPDF2
import pdfplumber
import camelot
import tabula
import pandas as pd
import os
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import json
from ..utils.logger import get_logger
from ..utils.language_detector import LanguageDetector

logger = get_logger(__name__)

class PDFExtractor:
    def __init__(self):
        self.extraction_methods = {
            'text': self.extract_text,
            'tables': self.extract_tables,
            'ocr': self.extract_with_ocr
        }
        self.language_detector = LanguageDetector()
    
    def extract_data(self, pdf_path, extraction_method='text', pages='all', template=None):
        """Extract data from PDF using specified method"""
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        if extraction_method not in self.extraction_methods:
            logger.error(f"Unsupported extraction method: {extraction_method}")
            return None
        
        return self.extraction_methods[extraction_method](pdf_path, pages, template)
    
    def extract_text(self, pdf_path, pages='all', template=None):
        """Extract text from PDF using PyPDF2 and pdfplumber"""
        try:
            # Use PyPDF2 for basic text extraction
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                if pages == 'all':
                    pages = range(num_pages)
                elif isinstance(pages, int):
                    pages = [pages]
                elif isinstance(pages, str):
                    pages = [int(p) for p in pages.split(',')]
                
                extracted_data = {}
                
                # Use pdfplumber for more accurate text extraction
                with pdfplumber.open(pdf_path) as pdf:
                    # Amostra para detecção de idioma
                    sample_text = ""
                    for i, page_num in enumerate(pages):
                        if i >= 3:  # Limita a 3 páginas para a amostra
                            break
                        if page_num < num_pages:
                            page = pdf.pages[page_num]
                            sample_text += page.extract_text() or ""
                    
                    # Detecta o idioma do documento
                    lang_code = "unknown"
                    if sample_text:
                        lang_code = self.language_detector.detect_language(sample_text)
                        logger.info(f"Idioma detectado: {lang_code} ({self.language_detector.get_language_name(lang_code)})")
                    
                    # Extrai texto de todas as páginas solicitadas
                    for page_num in pages:
                        if page_num < num_pages:
                            page = pdf.pages[page_num]
                            page_text = page.extract_text() or ""
                            
                            # Pré-processa o texto de acordo com o idioma
                            if page_text:
                                page_text = self.language_detector.preprocess_for_language(page_text, lang_code)
                            
                            extracted_data[f'page_{page_num+1}'] = page_text
                
                # Adiciona metadados
                extracted_data['_metadata'] = {
                    'language': lang_code,
                    'language_name': self.language_detector.get_language_name(lang_code),
                    'num_pages': num_pages,
                    'extraction_method': 'text'
                }
                
                return extracted_data
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def extract_tables(self, pdf_path, pages='all', template=None):
        """Extract tables from PDF using camelot and tabula"""
        try:
            # Detecta o idioma para processamento específico
            sample_text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for i in range(min(3, len(reader.pages))):
                    sample_text += reader.pages[i].extract_text() or ""
            
            lang_code = "unknown"
            if sample_text:
                lang_code = self.language_detector.detect_language(sample_text)
            
            # Try camelot first (better for complex tables)
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor='lattice')
            
            if len(tables) == 0:
                # If camelot fails, try tabula
                tables = tabula.read_pdf(pdf_path, pages=pages, multiple_tables=True)
            
            extracted_tables = {}
            for i, table in enumerate(tables):
                if hasattr(table, 'df'):  # camelot table
                    df = table.df
                else:  # tabula table
                    df = table
                
                # Processa a tabela de acordo com o idioma
                if lang_code in ['zh', 'ja', 'ko']:
                    # Para idiomas asiáticos, pode ser necessário um processamento especial
                    pass
                
                extracted_tables[f'table_{i+1}'] = df
            
            # Adiciona metadados
            extracted_tables['_metadata'] = {
                'language': lang_code,
                'language_name': self.language_detector.get_language_name(lang_code),
                'num_tables': len(tables),
                'extraction_method': 'tables'
            }
            
            return extracted_tables
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {str(e)}")
            return None
    
    def extract_with_ocr(self, pdf_path, pages='all', template=None):
        """Extract text using OCR for scanned PDFs"""
        try:
            images = convert_from_path(pdf_path)
            
            if pages == 'all':
                pages = range(len(images))
            elif isinstance(pages, int):
                pages = [pages]
            elif isinstance(pages, str):
                pages = [int(p) for p in pages.split(',')]
            
            extracted_data = {}
            
            # Amostra para detecção de idioma
            sample_img = None
            if len(images) > 0:
                sample_img = images[0]
            
            # Detecta o idioma para configurar o OCR
            lang_code = "eng"  # Padrão para inglês
            if sample_img:
                # Converte para OpenCV
                img = cv2.cvtColor(np.array(sample_img), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                
                # Tenta detectar idioma com OCR
                sample_text = pytesseract.image_to_string(thresh)
                if sample_text:
                    detected_lang = self.language_detector.detect_language(sample_text)
                    # Mapeia o código de idioma para o formato do Tesseract
                    tesseract_lang_map = {
                        'en': 'eng',
                        'pt': 'por',
                        'es': 'spa',
                        'fr': 'fra',
                        'de': 'deu',
                        'it': 'ita',
                        'nl': 'nld',
                        'ru': 'rus',
                        'zh': 'chi_sim',
                        'ja': 'jpn',
                        'ko': 'kor',
                        'ar': 'ara',
                        'hi': 'hin'
                    }
                    lang_code = tesseract_lang_map.get(detected_lang, 'eng')
            
            logger.info(f"Usando idioma para OCR: {lang_code}")
            
            for i, page_num in enumerate(pages):
                if page_num < len(images):
                    # Convert to OpenCV format
                    img = cv2.cvtColor(np.array(images[page_num]), cv2.COLOR_RGB2BGR)
                    
                    # Preprocess image for better OCR results
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                    
                                        # Apply OCR with the detected language
                    text = pytesseract.image_to_string(thresh, lang=lang_code)
                    
                    # Pré-processa o texto extraído
                    if text:
                        text = self.language_detector.preprocess_for_language(text, lang_code.split('_')[0])
                    
                    extracted_data[f'page_{page_num+1}'] = text
            
            # Adiciona metadados
            extracted_data['_metadata'] = {
                'language': lang_code,
                'num_pages': len(images),
                'extraction_method': 'ocr'
            }
            
            return extracted_data
        except Exception as e:
            logger.error(f"Error extracting text with OCR: {str(e)}")
            return None
    
    def extract_with_template(self, pdf_path, template_path):
        """Extract data using a predefined template"""
        try:
            if not os.path.exists(template_path):
                logger.error(f"Template file not found: {template_path}")
                return None
            
            # Load template
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # Extract text from PDF
            text_data = self.extract_text(pdf_path)
            if not text_data:
                return None
            
            # Combine all text for processing
            all_text = ""
            for key, value in text_data.items():
                if key != '_metadata' and isinstance(value, str):
                    all_text += value + "\n"
            
            # Extract data according to template
            extracted_data = {}
            
            # Process fields
            for field_name, field_info in template.get('fields', {}).items():
                if 'regex' in field_info:
                    pattern = field_info['regex']
                    match = re.search(pattern, all_text, re.MULTILINE)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
                        
                        # Convert value based on type
                        if field_info.get('type') == 'date' and 'format' in field_info:
                            try:
                                from datetime import datetime
                                value = datetime.strptime(value, field_info['format'])
                            except:
                                pass
                        elif field_info.get('type') == 'decimal':
                            try:
                                value = float(value.replace(',', '.'))
                            except:
                                pass
                        
                        extracted_data[field_name] = value
            
            # Process tables if needed
            if 'tables' in template:
                tables_data = self.extract_tables(pdf_path)
                if tables_data:
                    for table_info in template['tables']:
                        table_name = table_info.get('name')
                        if table_name:
                            # Find the best matching table
                            best_table = None
                            for key, table in tables_data.items():
                                if key != '_metadata' and isinstance(table, pd.DataFrame):
                                    # Simple heuristic: check if column headers match
                                    if any(col in table.columns.str.upper().tolist() for col in 
                                          [col['header'].upper() for col in table_info.get('columns', [])]):
                                        best_table = table
                                        break
                            
                            if best_table is not None:
                                extracted_data[table_name] = best_table
            
            # Add metadata
            if '_metadata' in text_data:
                extracted_data['_metadata'] = text_data['_metadata']
                extracted_data['_metadata']['template_used'] = os.path.basename(template_path)
            
            return extracted_data
        
        except Exception as e:
            logger.error(f"Error extracting with template: {str(e)}")
            return None