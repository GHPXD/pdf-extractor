# test_document_classifier.py
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.core.document_classifier import DocumentClassifier

class TestDocumentClassifier(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.patterns_dir = os.path.join(self.temp_dir, "patterns")
        os.makedirs(self.patterns_dir, exist_ok=True)
        
        # Criar padrões de teste
        self.create_test_patterns()
        
        self.classifier = DocumentClassifier(patterns_dir=self.patterns_dir)

    def tearDown(self):
        # Limpar arquivos temporários
        for file in os.listdir(self.patterns_dir):
            os.remove(os.path.join(self.patterns_dir, file))
        os.rmdir(self.patterns_dir)
        os.rmdir(self.temp_dir)

    def create_test_patterns(self):
        # Criar arquivo de padrões para fatura
        invoice_patterns = {
            "document_type": "invoice",
            "keywords": ["DANFE", "Nota Fiscal", "NF-e"],
            "patterns": ["NF-e nº\\s*\\d+", "CNPJ:\\s*\\d{2}\\.\\d{3}\\.\\d{3}/\\d{4}-\\d{2}"]
        }
        
        with open(os.path.join(self.patterns_dir, "invoice_patterns.json"), "w") as f:
            import json
            json.dump(invoice_patterns, f)

    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        # Configurar mock
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "DANFE\nNF-e nº 123456\nCNPJ: 12.345.678/0001-90"
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Criar PDF de teste
        test_pdf = os.path.join(self.temp_dir, "test_invoice.pdf")
        with open(test_pdf, "wb") as f:
            f.write(b"%PDF-1.5\nTest content")
        
        text = self.classifier.extract_text_from_pdf(test_pdf)
        self.assertIn("DANFE", text)
        self.assertIn("NF-e", text)
        self.assertIn("CNPJ", text)

    def test_classify_by_rules(self):
        # Texto que corresponde aos padrões de fatura
        invoice_text = "DANFE\nNF-e nº 123456\nCNPJ: 12.345.678/0001-90"
        doc_type, score = self.classifier.classify_by_rules(invoice_text)
        
        self.assertEqual(doc_type, "invoice")
        self.assertGreater(score, 0.5)
        
        # Texto que não corresponde a nenhum padrão
        random_text = "Este é um texto aleatório que não contém padrões específicos."
        doc_type, score = self.classifier.classify_by_rules(random_text)
        
        self.assertIsNone(doc_type)
        self.assertEqual(score, 0.0)

    @patch('PyPDF2.PdfReader')
    def test_classify_document(self, mock_pdf_reader):
        # Configurar mock
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "DANFE\nNF-e nº 123456\nCNPJ: 12.345.678/0001-90"
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader
        
        # Criar PDF de teste
        test_pdf = os.path.join(self.temp_dir, "test_invoice.pdf")
        with open(test_pdf, "wb") as f:
            f.write(b"%PDF-1.5\nTest content")
        
        doc_type, confidence = self.classifier.classify_document(test_pdf)
        
        self.assertEqual(doc_type, "invoice")
        self.assertGreater(confidence, 0.5)
        
        # Testar com arquivo inexistente
        doc_type, confidence = self.classifier.classify_document("non_existent.pdf")
        
        self.assertIsNone(doc_type)
        self.assertEqual(confidence, 0.0)

if __name__ == "__main__":
    unittest.main()
