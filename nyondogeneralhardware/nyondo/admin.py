# COMMENT-HEADER
# File: nyondo/admin.py
# Simple review note: use this file for code logic and Django app behavior.
from django.contrib import admin
from .models import (
    Stock, Sale, Receipt, Customer, Deposit, DepositPayment, 
    DepositPaymentReceipt, CustomerPayment, Supplier, SupplierPayment, SupplierReceipt
)

# Register your models here.

@admin.register(DepositPaymentReceipt)
class DepositPaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ('payment_receipt_number', 'customer_name', 'amount_paid', 'payment_date', 'deposit_receipt_number')
    list_filter = ('payment_date', 'payment_method')
    search_fields = ('customer_name', 'customer_phone', 'payment_receipt_number', 'deposit_receipt_number')
    readonly_fields = ('payment_receipt_number', 'payment_date')
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('payment_receipt_number', 'payment_date')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_phone', 'customer_nin', 'customer_address')
        }),
        ('Deposit Information', {
            'fields': ('deposit_receipt_number', 'item_name', 'total_deposit_amount', 'total_balance_owed')
        }),
        ('Payment Details', {
            'fields': ('amount_paid', 'payment_method', 'balance_before_payment', 'balance_after_payment', 'note')
        }),
        ('Additional Info', {
            'fields': ('issued_by',)
        }),
    )


@admin.register(DepositPayment)
class DepositPaymentAdmin(admin.ModelAdmin):
    list_display = ('deposit', 'amount', 'date', 'note')
    list_filter = ('date',)
    search_fields = ('deposit__receipt_number', 'deposit__customer__name')
    readonly_fields = ('date',)


@admin.register(SupplierReceipt)
class SupplierReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'supplier', 'issued_on')
    list_filter = ('issued_on',)
    search_fields = ('receipt_number', 'supplier__supplier_company', 'supplier__name')
    readonly_fields = ('receipt_number', 'issued_on')

