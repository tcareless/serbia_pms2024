from django.test import TestCase
from django.test import SimpleTestCase
from django.urls import reverse

# Create your tests here.
class Tests(TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    def test_urls(self):
        response = self.client.get(reverse('prod_query:prod-query_index'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('prod_query:prod-query'))
        self.assertEqual(response.status_code, 200)
        # response = self.client.get(reverse('prod_query:weekly-prod'))
        self.assertEqual(response.status_code, 200)
        # response = self.client.get(reverse('prod_query:rejects'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('prod_query:cycle-times'))
        self.assertEqual(response.status_code, 200)
        # response = self.client.get("prod-query/1710/1692586800/10/")
        self.assertEqual(response.status_code, 200)

# ./app/manage.py test app/prod_query/