from django.test import TestCase
from django.core.exceptions import ValidationError
from neumscan.utils import valida_cedula


class CedulaValidationTests(TestCase):
    def test_rejects_a_non_numeric_cedula(self):
        with self.assertRaises(ValidationError):
            valida_cedula('abcdefghij')

    def test_rejects_a_cedula_with_invalid_length(self):
        with self.assertRaises(ValidationError):
            valida_cedula('123456789')
