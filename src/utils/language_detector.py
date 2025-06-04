import re
from langdetect import detect, DetectorFactory
from transformers import pipeline
import os
from ..utils.logger import get_logger

# Torna a detecção de idioma determinística
DetectorFactory.seed = 0

logger = get_logger(__name__)

class LanguageDetector:
    """Detecta e processa texto em múltiplos idiomas"""
    
    def __init__(self, use_transformers=False, model_name=None):
        self.use_transformers = use_transformers
        self.model_name = model_name or "papluca/xlm-roberta-base-language-detection"
        self.transformer_pipeline = None
        
        # Carrega o modelo de transformers se solicitado
        if self.use_transformers:
            try:
                self.transformer_pipeline = pipeline("text-classification", model=self.model_name)
                logger.info(f"Modelo de detecção de idioma carregado: {self.model_name}")
            except Exception as e:
                logger.error(f"Erro ao carregar modelo de detecção de idioma: {str(e)}")
                self.use_transformers = False
    
    def detect_language(self, text):
        """Detecta o idioma de um texto"""
        if not text or len(text.strip()) < 10:
            return "unknown"
        
        try:
            if self.use_transformers and self.transformer_pipeline:
                # Limita o texto para evitar problemas com textos muito longos
                sample = text[:1000]
                result = self.transformer_pipeline(sample)[0]
                return result['label']
            else:
                # Usa langdetect como fallback
                return detect(text)
        except Exception as e:
            logger.error(f"Erro ao detectar idioma: {str(e)}")
            return "unknown"
    
    def get_language_name(self, lang_code):
        """Retorna o nome completo do idioma a partir do código"""
        language_names = {
            'en': 'English',
            'pt': 'Portuguese',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'nl': 'Dutch',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'unknown': 'Unknown'
        }
        return language_names.get(lang_code, lang_code)
    
    def preprocess_for_language(self, text, lang_code):
        """Pré-processa o texto de acordo com o idioma"""
        if not text:
            return text
        
        # Processamento comum para todos os idiomas
        text = text.strip()
        
        # Remove caracteres de controle
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        
        # Processamento específico por idioma
        if lang_code == 'zh' or lang_code == 'ja' or lang_code == 'ko':
            # Para idiomas asiáticos, não remove espaços em branco extras
            pass
        else:
            # Para outros idiomas, normaliza espaços em branco
            text = re.sub(r'\s+', ' ', text)
        
        return text