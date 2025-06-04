# test_analytics.py
import unittest
import os
import tempfile
import json
from datetime import datetime, timedelta
from src.core.analytics import DataAnalytics

class TestDataAnalytics(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analytics = DataAnalytics(self.temp_dir)
        
        # Criar alguns dados de teste
        self.create_test_data()

    def tearDown(self):
        # Limpar arquivos temporários
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def create_test_data(self):
        # Criar alguns registros de teste
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        test_data = [
            {
                "pdf_path": "/path/to/invoice1.pdf",
                "doc_type": "invoice",
                "success": True,
                "confidence": 0.85,
                "timestamp": today.isoformat(),
                "processing_time": 1.5
            },
            {
                "pdf_path": "/path/to/receipt1.pdf",
                "doc_type": "receipt",
                "success": True,
                "confidence": 0.75,
                "timestamp": today.isoformat(),
                "processing_time": 0.8
            },
            {
                "pdf_path": "/path/to/invoice2.pdf",
                "doc_type": "invoice",
                "success": False,
                "error": "Failed to extract data",
                "timestamp": yesterday.isoformat(),
                "processing_time": 2.1
            }
        ]
        
        # Salvar dados em arquivos
        for i, data in enumerate(test_data):
            file_path = os.path.join(self.temp_dir, f"log_{i}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        
        # Salvar também um log de lote
        batch_log = {
            "timestamp": today.isoformat(),
            "stats": {
                "total_files": 5,
                "successful": 4,
                "failed": 1,
                "success_rate": 80.0
            },
            "details": [
                {
                    "pdf_path": "/path/to/doc1.pdf",
                    "doc_type": "other",
                    "success": True,
                    "confidence": 0.65,
                    "timestamp": yesterday.isoformat()
                },
                {
                    "pdf_path": "/path/to/doc2.pdf",
                    "doc_type": "other",
                    "success": True,
                    "confidence": 0.70,
                    "timestamp": yesterday.isoformat()
                }
            ]
        }
        
        batch_file_path = os.path.join(self.temp_dir, "batch_log.json")
        with open(batch_file_path, 'w', encoding='utf-8') as f:
            json.dump(batch_log, f)
        
        # Recarregar dados
        self.analytics.load_data()

    def test_load_data(self):
        # Verificar se os dados foram carregados corretamente
        self.assertEqual(len(self.analytics.data), 5)  # 3 logs individuais + 2 do lote

    def test_get_document_types(self):
        doc_types = self.analytics.get_document_types()
        self.assertIn("invoice", doc_types)
        self.assertIn("receipt", doc_types)
        self.assertIn("other", doc_types)
        self.assertEqual(len(doc_types), 3)

    def test_get_filtered_data(self):
        # Filtrar por data (hoje)
        today = datetime.now()
        today_data = self.analytics.get_filtered_data(
            start_date=today.replace(hour=0, minute=0, second=0, microsecond=0)
        )
        self.assertEqual(len(today_data), 2)
        
        # Filtrar por tipo de documento
        invoice_data = self.analytics.get_filtered_data(doc_type="invoice")
        self.assertEqual(len(invoice_data), 2)
        
        # Filtrar por data e tipo
        yesterday = today - timedelta(days=1)
        yesterday_invoice = self.analytics.get_filtered_data(
            start_date=yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=yesterday.replace(hour=23, minute=59, second=59, microsecond=999999),
            doc_type="invoice"
        )
        self.assertEqual(len(yesterday_invoice), 1)

    def test_get_success_rate(self):
        # Taxa de sucesso geral
        success_rate = self.analytics.get_success_rate()
        self.assertEqual(success_rate, 80.0)  # 4 sucessos em 5 documentos
        
        # Taxa de sucesso para um tipo específico
        invoice_success_rate = self.analytics.get_success_rate(doc_type="invoice")
        self.assertEqual(invoice_success_rate, 50.0)  # 1 sucesso em 2 faturas

    def test_get_avg_confidence(self):
        # Confiança média geral
        avg_confidence = self.analytics.get_avg_confidence()
        self.assertAlmostEqual(avg_confidence, 0.74, places=2)  # Média de 0.85, 0.75, 0.65, 0.70
        
        # Confiança média para um tipo específico
        invoice_confidence = self.analytics.get_avg_confidence(doc_type="invoice")
        self.assertEqual(invoice_confidence, 0.85)  # Apenas uma fatura com confiança

    def test_log_processing_result(self):
        # Registrar um novo resultado
        new_result = {
            "pdf_path": "/path/to/new_doc.pdf",
            "doc_type": "contract",
            "success": True,
            "confidence": 0.90
        }
        
        log_path = self.analytics.log_processing_result(new_result)
        
        self.assertIsNotNone(log_path)
        self.assertTrue(os.path.exists(log_path))
        
        # Verificar se foi adicionado aos dados
        self.assertEqual(len(self.analytics.data), 6)
        
        # Verificar se o timestamp foi adicionado
        with open(log_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            self.assertIn('timestamp', saved_data)

if __name__ == "__main__":
    unittest.main()