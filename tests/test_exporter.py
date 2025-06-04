# test_exporter.py
import unittest
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock
from src.core.exporter import DataExporter

class TestDataExporter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.exporter = DataExporter(self.temp_dir)
        
        # Dados de teste
        self.test_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        
        self.test_dict = {
            'table_1': pd.DataFrame({
                'col1': [1, 2],
                'col2': ['x', 'y']
            }),
            'page_1': 'Text content'
        }

    def tearDown(self):
        # Limpar arquivos temporários
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_export_to_csv_dataframe(self):
        filename = "test_export.csv"
        result = self.exporter.export_to_csv(self.test_df, filename, structured=True)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verificar conteúdo
        exported_df = pd.read_csv(result)
        pd.testing.assert_frame_equal(exported_df, self.test_df)

    def test_export_to_csv_dict(self):
        filename = "test_export.csv"
        result = self.exporter.export_to_csv(self.test_dict, filename, structured=True)
        
        self.assertIsNotNone(result)
        
        # Verificar se os arquivos foram criados
        base_path = os.path.join(self.temp_dir, "test_export")
        self.assertTrue(os.path.exists(f"{base_path}_table_1.csv"))
        
        # Verificar conteúdo
        exported_df = pd.read_csv(f"{base_path}_table_1.csv")
        pd.testing.assert_frame_equal(exported_df, self.test_dict['table_1'])

    def test_export_to_json(self):
        filename = "test_export.json"
        result = self.exporter.export_to_json(self.test_dict, filename)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verificar conteúdo
        import json
        with open(result, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        self.assertIn('table_1', exported_data)
        self.assertIn('page_1', exported_data)
        self.assertEqual(exported_data['page_1'], 'Text content')

    @patch('sqlite3.connect')
    def test_export_to_sql(self, mock_connect):
        # Configurar mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        filename = "test_export.sql"
        result = self.exporter.export_to_sql(self.test_df, filename)
        
        self.assertIsNotNone(result)
        mock_connect.assert_called_once()
        self.test_df.to_sql.assert_called_once()

    def test_export_to_excel(self):
        filename = "test_export.xlsx"
        result = self.exporter.export_to_excel(self.test_dict, filename)
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))
        
        # Verificar conteúdo
        imported_dfs = pd.read_excel(result, sheet_name=None)
        self.assertIn('table_1', imported_dfs)
        pd.testing.assert_frame_equal(imported_dfs['table_1'], self.test_dict['table_1'])

if __name__ == "__main__":
    unittest.main()