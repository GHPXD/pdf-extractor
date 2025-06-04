# test_downloader.py
import unittest
import os
from unittest.mock import patch, MagicMock
from src.core.downloader import PDFDownloader

class TestPDFDownloader(unittest.TestCase):

    def setUp(self):
        self.download_dir = "test_downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        self.downloader = PDFDownloader(self.download_dir)

    def tearDown(self):
        for file in os.listdir(self.download_dir):
            os.remove(os.path.join(self.download_dir, file))
        os.rmdir(self.download_dir)

    @patch('requests.get')
    def test_download_pdf_direct_success(self, mock_get):
        # Configurar o mock
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b"PDF content"]
        mock_get.return_value = mock_response

        url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        file_path = self.downloader.download_pdf_direct(url)
        
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.endswith("dummy.pdf"))
        mock_get.assert_called_once_with(url, stream=True)

    @patch('requests.get')
    def test_download_pdf_direct_invalid_url(self, mock_get):
        # Configurar o mock para lançar uma exceção
        mock_get.side_effect = Exception("Connection error")

        url = "https://invalid-url.com/dummy.pdf"
        file_path = self.downloader.download_pdf_direct(url)
        
        self.assertIsNone(file_path)
        mock_get.assert_called_once_with(url, stream=True)

    @patch('selenium.webdriver.Chrome')
    @patch('selenium.webdriver.chrome.service.Service')
    @patch('webdriver_manager.chrome.ChromeDriverManager')
    def test_download_pdf_with_selenium(self, mock_manager, mock_service, mock_chrome):
        # Configurar os mocks
        mock_manager.install.return_value = "path/to/chromedriver"
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Simular download bem-sucedido
        mock_driver.find_element_by_xpath.return_value = MagicMock()
        
        # Simular arquivo baixado
        test_file = os.path.join(self.download_dir, "test_download.pdf")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        url = "https://example.com/pdf-page"
        download_button_xpath = "//button[@id='download']"
        
        file_path = self.downloader.download_pdf_with_selenium(url, download_button_xpath=download_button_xpath)
        
        self.assertIsNotNone(file_path)
        mock_chrome.assert_called_once()
        mock_driver.get.assert_called_once_with(url)
        mock_driver.find_element_by_xpath.assert_called_once_with(download_button_xpath)

if __name__ == "__main__":
    unittest.main()