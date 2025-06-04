# test_validator.py
import unittest
from unittest.mock import patch, MagicMock
from src.core.validator import DataValidator
from src.models.validation_schema import ValidationSchema, FieldSchema

class TestDataValidator(unittest.TestCase):

    def setUp(self):
        self.validator = DataValidator()
        
        # Definir esquema de teste
        self.test_schema = ValidationSchema(
            name="test_schema",
            description="Test schema",
            version="1.0",
            fields={
                "name": FieldSchema(type="string", required=True),
                "age": FieldSchema(type="integer", required=True),
                "email": FieldSchema(type="email", required=False),
                "cpf": FieldSchema(type="cpf", required=False)
            },
            strict=True
        )

    def test_validate_field_string_success(self):
        valid, error = self.validator.validate_field("Test String", "string")
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_field_string_failure(self):
        valid, error = self.validator.validate_field(123, "string")
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_validate_field_integer_success(self):
        valid, error = self.validator.validate_field(123, "integer")
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_field_integer_failure(self):
        valid, error = self.validator.validate_field("abc", "integer")
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_validate_field_email_success(self):
        valid, error = self.validator.validate_field("test@example.com", "email")
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_field_email_failure(self):
        valid, error = self.validator.validate_field("invalid-email", "email")
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_validate_field_cpf_success(self):
        valid, error = self.validator.validate_field("123.456.789-09", "cpf")
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_data_success(self):
        data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        
        valid, results = self.validator.validate_data(data, schema=self.test_schema)
        self.assertTrue(valid)
        self.assertEqual(len(results.get("errors", {})), 0)

    def test_validate_data_failure(self):
        data = {
            "name": "John Doe",
            "age": "thirty",  # Deveria ser um inteiro
            "email": "invalid-email"  # Email inválido
        }
        
        valid, results = self.validator.validate_data(data, schema=self.test_schema)
        self.assertFalse(valid)
        self.assertGreater(len(results.get("errors", {})), 0)
        self.assertIn("age", results.get("errors", {}))
        self.assertIn("email", results.get("warnings", {}))

if __name__ == "__main__":
    unittest.main()