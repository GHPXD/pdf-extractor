# test_extractor.py
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.core.extractor import PDFExtractor

class TestPDFExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = PDFExtractor()
        # Criar um arquivo PDF temporário para testes
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.5\nMock PDF content")

    def tearDown(self):
        # Limpar arquivos temporários
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)

    @patch('PyPDF2.PdfReader')
    @patch('pdfplumber.open')
    def test_extract_text(self, mock_pdfplumber_open, mock_pdf_reader):
        # Configurar mocks
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_pdf_reader.return_value = mock_reader
        
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Extracted text from page"
        mock_pdf.pages = [mock_page, mock_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
        
        # Testar extração de texto
        result = self.extractor.extract_text(self.test_pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn("page_1", result)
        self.assertEqual(result["page_1"], "Extracted text from page")
        mock_pdfplumber_open.assert_called_once_with(self.test_pdf_path)

    @patch('camelot.read_pdf')
    @patch('tabula.read_pdf')
    def test_extract_tables(self, mock_tabula, mock_camelot):
        # Configurar mocks
        mock_table = MagicMock()
        mock_table.df = "DataFrame content"
        mock_camelot.return_value = [mock_table]
        
        # Testar extração de tabelas
        result = self.extractor.extract_tables(self.test_pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn("table_1", result)
        self.assertEqual(result["table_1"], "DataFrame content")
        mock_camelot.assert_called_once_with(self.test_pdf_path, pages='all', flavor='lattice')

    @patch('pytesseract.image_to_string')
    @patch('pdf2image.convert_from_path')
    @patch('cv2.cvtColor')
    @patch('cv2.threshold')
    def test_extract_with_ocr(self, mock_threshold, mock_cvtcolor, mock_convert, mock_image_to_string):
        # Configurar mocks
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image, mock_image]
        mock_threshold.return_value = (None, "threshold_result")
        mock_image_to_string.return_value = "OCR extracted text"
        
        # Testar extração OCR
        result = self.extractor.extract_with_ocr(self.test_pdf_path)
        
        self.assertIsNotNone(result)
        self.assertIn("page_1", result)
        self.assertEqual(result["page_1"], "OCR extracted text")
        mock_convert.assert_called_once_with(self.test_pdf_path)
        mock_image_to_string.assert_called()

if __name__ == "__main__":
    unittest.main()