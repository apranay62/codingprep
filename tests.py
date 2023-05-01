from django.test import TestCase
from rest_framework.test import APIClient
from .models import Invoice


# Create your tests here.

class OdoAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_invoice(self):
        data = {
            "customer": "abc",
            "transactions": [
                {
                    "product": "test_prod",
                    "quantity": 2,
                    "price": "10.00"
                },
                {
                    "product": "test_prod",
                    "quantity": 1,
                    "price": "10.00"
                }
            ]
        }

        response = self.client.post('/invoices/', data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Invoice.objects.count(), 1)

        invoice = Invoice.objects.first()
        self.assertEqual(invoice.customer, "abc")
        self.assertEqual(invoice.total_quantity, 3)
        self.assertEqual(str(invoice.total_amount), "30.00")

    def test_update_invoice(self):
        invoice = Invoice.objects.create(customer="test")
        transaction1 = invoice.transactions.create(product="test prod", quantity=2, price="10.00")

        data = {
            "id": invoice.id,
            "customer": "updated test",
            "transactions": [
                {
                    "id": transaction1.id,
                    "product": "updated prod",
                    "quantity": 3,
                    "price": "15.00"
                },
                {
                    "product": "new prod",
                    "quantity": 1,
                    "price": "10.00"
                }
            ]
        }

        response = self.client.put(f'/invoices/{invoice.id}/', data, format='json')

        self.assertEqual(response.status_code, 200)

        updated_invoice = Invoice.objects.get(id=invoice.id)
        self.assertEqual(updated_invoice.customer, "updated test")
        self.assertEqual(updated_invoice.total_quantity, 4)
        self.assertEqual(str(updated_invoice.total_amount), "55.00")