# test_language_detector.py
import unittest
from unittest.mock import patch, MagicMock
from src.utils.language_detector import LanguageDetector

class TestLanguageDetector(unittest.TestCase):

    def setUp(self):
        self.detector = LanguageDetector(use_transformers=False)

    @patch('langdetect.detect')
    def test_detect_language(self, mock_detect):
        # Configurar mock
        mock_detect.return_value = "en"
        
        # Testar detecção de idioma
        lang = self.detector.detect_language("This is an English text.")
        self.assertEqual(lang, "en")
        mock_detect.assert_called_once_with("This is an English text.")
        
        # Testar com texto muito curto
        lang = self.detector.detect_language("Hi")
        self.assertEqual(lang, "unknown")
        
        # Testar com texto vazio
        lang = self.detector.detect_language("")
        self.assertEqual(lang, "unknown")

    def test_get_language_name(self):
        self.assertEqual(self.detector.get_language_name("en"), "English")
        self.assertEqual(self.detector.get_language_name("pt"), "Portuguese")
        self.assertEqual(self.detector.get_language_name("unknown"), "Unknown")
        self.assertEqual(self.detector.get_language_name("xx"), "xx")  # Código desconhecido

    def test_preprocess_for_language(self):
        # Testar pré-processamento para idiomas ocidentais
        text = "  This   is  a   text   with   extra   spaces.  "
        processed = self.detector.preprocess_for_language(text, "en")
        self.assertEqual(processed, "This is a text with extra spaces.")
        
        # Testar pré-processamento para idiomas asiáticos
        text = "这是  中文  文本"
        processed = self.detector.preprocess_for_language(text, "zh")
        self.assertEqual(processed, "这是  中文  文本")  # Espaços mantidos
        
        # Testar com texto vazio
        self.assertEqual(self.detector.preprocess_for_language("", "en"), "")
        
        # Testar remoção de caracteres de controle
        text = "Text with \x00 control \x1F characters"
        processed = self.detector.preprocess_for_language(text, "en")
        self.assertEqual(processed, "Text with control characters")

if __name__ == "__main__":
    unittest.main()