from django.test import TestCase
from django.urls import reverse


class PublicPagesTests(TestCase):
    def test_home_page_is_available_without_the_ai_model(self):
        """The basic app must start even when the optional .h5 model is absent."""
        response = self.client.get(reverse('core:home'))

        self.assertEqual(response.status_code, 200)
