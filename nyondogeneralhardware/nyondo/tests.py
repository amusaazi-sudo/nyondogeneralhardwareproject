# COMMENT-HEADER
# File: nyondo/tests.py
# Simple review note: use this file for code logic and Django app behavior.
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from .models import Customer, Deposit, DepositPayment, Supplier, SupplierPayment


class SupplierCreditWorkflowTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(
            supplier_company='Nyondo Steel',
            name='John Doe',
            phone='0777000000',
            product='iron_bars',
            specification='12mm',
            quantity=5,
            deposit=100000,
            delivery_date=date.today(),
            is_credit=True,
        )

    def test_supplier_initial_credit_status(self):
        self.assertEqual(self.supplier.payment_status, 'Pending')
        self.assertEqual(self.supplier.amount_owed, 500000)

    def test_supplier_payment_updates_status_and_amount_owed(self):
        SupplierPayment.objects.create(supplier=self.supplier, amount=200000, note='Partial payment')
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.payment_status, 'Partial')
        self.assertEqual(self.supplier.amount_owed, 300000)

        SupplierPayment.objects.create(supplier=self.supplier, amount=300000, note='Final payment')
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.payment_status, 'Paid')
        self.assertEqual(self.supplier.amount_owed, 0)


class DepositValidationTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name='Jane Buyer',
            phone='0777111222',
            address='Nansana',
        )

    def test_add_deposit_with_past_expiry_date_shows_error(self):
        response = self.client.post(reverse('add_deposit'), {
            'customer': self.customer.pk,
            'item': 'cement',
            'contact': '0777111222',
            'deposit_amount': '100000',
            'total_balance': '200000',
            'expiry_date': (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Expiry date must be in the future.')
        self.assertEqual(Deposit.objects.count(), 0)

    def test_deposit_progress_prevents_overpayment(self):
        deposit = Deposit.objects.create(
            customer=self.customer,
            item='cement',
            receipt_number='DEP-00001',
            NIN='12345',
            contact='0777111222',
            deposit_amount=100000,
            expiry_date=date.today() + timedelta(days=30),
            total_balance=200000,
        )
        response = self.client.post(reverse('deposit_progress', args=[deposit.pk]), {
            'amount': '250000',
            'note': 'Attempt too high',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amount exceeds remaining balance')
        self.assertEqual(DepositPayment.objects.count(), 0)


class ReportsViewTests(TestCase):
    def test_reports_view_includes_summary_totals(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('sales_total', response.context)
        self.assertIn('stock_value', response.context)
        self.assertIn('supplier_amount_owed', response.context)
        self.assertIn('deposit_amount_outstanding', response.context)
