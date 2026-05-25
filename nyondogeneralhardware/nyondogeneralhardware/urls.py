# COMMENT-HEADER
# File: nyondogeneralhardware/urls.py
# Simple review note: use this file for code logic and Django app behavior.
"""
URL configuration for nyondogeneralhardware project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from nyondo import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path("", views.dashboard, name="dashboard"),
    path("sales/", views.sales_dashboard, name="sales_dashboard"),
    path("sales-list/", views.sales, name="sales"),   
    path("add_sales/", views.add_sales, name="add_sales"),
    path('sales/<int:pk>/edit/', views.sales_edit, name='sales_edit'),
    path('sales/<int:pk>/delete/', views.sales_delete, name='sales_delete'),
    path('sales/<int:pk>/receipt/', views.sale_receipt, name='sale_receipt'),
    path('sales/receipt/', views.sales_receipt, name='sales_receipt'),
#stock

    path("stocks/", views.stock_dashboard, name="stock_dashboard"),
    path("stocks/list/", views.stocks, name="stocks"),
    path("add_stock/", views.add_stock, name="add_stock"),
    path('stock/<int:pk>/edit/', views.stock_edit, name='stock_edit'),
    path('stock/<int:pk>/delete/', views.stock_delete, name='stock_delete'),
    

# SUPPLIER
	path('suppliers/', views.suppliers, name='suppliers'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('suppliers/<int:pk>/view/', views.supplier_view, name='supplier_view'),
    path('suppliers/<int:pk>/receipt/', views.supplier_receipt, name='supplier_receipt'),
    path('suppliers/reports/', views.supply_reports, name='supply_reports'),

# CUSTOMER
    path('customers/', views.customers, name='customer'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/<int:pk>/view/', views.customer_view, name='customer_view'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

# DEPOSIT SCHEME
    path('deposits/', views.deposits, name='deposits'),
    path('deposits/add/', views.add_deposit, name='add_deposit'),
    path('deposits/receipts/', views.deposit_receipts, name='deposit_receipts'),
    path('deposits/<int:pk>/receipt/', views.deposit_receipt, name='deposit_receipt'),
    path('deposits/<int:pk>/progress/', views.deposit_progress, name='deposit_progress'),
    path('deposits/<int:pk>/edit/', views.deposit_edit, name='deposit_edit'),
    path('deposits/<int:pk>/delete/', views.deposit_delete, name='deposit_delete'),
    
    # Payment receipts
    path('payment-receipt/<int:receipt_id>/', views.payment_receipt, name='payment_receipt'),
    path('payment-receipts/', views.payment_receipts_list, name='payment_receipts_list'),
    path('reports/', views.reports, name='reports'),
]
