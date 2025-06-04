import os
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import pickle
import PyPDF2
import pdfplumber
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DocumentClassifier:
    """Classifica automaticamente o tipo de documento"""
    
    def __init__(self, model_path=None, patterns_dir=None):
        self.model_path = model_path
        self.patterns_dir = patterns_dir
        self.model = None
        self.vectorizer = None
        self.document_patterns = {}
        
        # Carregar padrões para classificação baseada em regras
        self.load_patterns()
        
        # Carregar modelo ML se disponível
        if model_path and os.path.exists(model_path):
            self.load_model()
    
    def load_patterns(self):
        """Carrega padrões de reconhecimento de documentos"""
        if not self.patterns_dir or not os.path.exists(self.patterns_dir):
            logger.warning("Diretório de padrões não encontrado")
            return
        
        try:
            for file in os.listdir(self.patterns_dir):
                if file.endswith('.json'):
                    with open(os.path.join(self.patterns_dir, file), 'r', encoding='utf-8') as f:
                        pattern_data = json.load(f)
                        doc_type = pattern_data.get('document_type')
                        if doc_type:
                            self.document_patterns[doc_type] = pattern_data
            
            logger.info(f"Carregados {len(self.document_patterns)} padrões de documentos")
        except Exception as e:
            logger.error(f"Erro ao carregar padrões de documentos: {str(e)}")
    
    def load_model(self):
        """Carrega o modelo de classificação treinado"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.vectorizer = model_data['vectorizer']
            logger.info("Modelo de classificação de documentos carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo de classificação: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrai texto de um PDF para classificação"""
        try:
            text = ""
            
            # Tenta primeiro com PyPDF2
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            # Se não obtiver texto suficiente, tenta com pdfplumber
            if len(text.strip()) < 100:
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or "" + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF para classificação: {str(e)}")
            return ""
    
    def classify_by_rules(self, text):
        """Classifica o documento com base em regras e padrões"""
        if not text or not self.document_patterns:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for doc_type, pattern_data in self.document_patterns.items():
            score = 0
            max_score = 0
            
            # Verifica palavras-chave
            for keyword in pattern_data.get('keywords', []):
                max_score += 1
                if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                    score += 1
            
            # Verifica padrões de regex
            for pattern in pattern_data.get('patterns', []):
                max_score += 2  # Regex tem peso maior
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    score += 2
            
            # Calcula pontuação normalizada
            if max_score > 0:
                normalized_score = score / max_score
                if normalized_score > best_score:
                    best_score = normalized_score
                    best_match = doc_type
        
        return best_match, best_score
    
    def classify_by_ml(self, text):
        """Classifica o documento usando o modelo de ML"""
        if not text or not self.model or not self.vectorizer:
            return None, 0.0
        
        try:
            # Transforma o texto usando o vectorizer
            text_features = self.vectorizer.transform([text])
            
            # Prediz a classe
            prediction = self.model.predict(text_features)[0]
            
            # Obtém a probabilidade
            probabilities = self.model.predict_proba(text_features)[0]
            confidence = max(probabilities)
            
            return prediction, confidence
        except Exception as e:
            logger.error(f"Erro ao classificar documento com ML: {str(e)}")
            return None, 0.0
    
    def classify_document(self, pdf_path):
        """Classifica o documento combinando regras e ML"""
        if not os.path.exists(pdf_path):
            logger.error(f"Arquivo não encontrado: {pdf_path}")
            return None, 0.0
        
        # Extrai texto do PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"Não foi possível extrair texto do PDF: {pdf_path}")
            return None, 0.0
        
        # Tenta classificação por regras
        rule_type, rule_score = self.classify_by_rules(text)
        
        # Tenta classificação por ML se disponível
        ml_type, ml_score = self.classify_by_ml(text)
        
        # Decide qual classificação usar
        if ml_score > 0.7:  # Alta confiança no ML
            return ml_type, ml_score
        elif rule_score > 0.6:  # Boa confiança nas regras
            return rule_type, rule_score
        elif ml_score > 0 and rule_score > 0:
            # Se ambos detectaram algo, usa o de maior confiança
            if ml_score > rule_score:
                return ml_type, ml_score
            else:
                return rule_type, rule_score
        elif ml_score > 0:
            return ml_type, ml_score
        elif rule_score > 0:
            return rule_type, rule_score
        
        # Não foi possível classificar
        return None, 0.0