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

    # path('login/', views.login_view, name='login'),

    path("", views.dashboard, name="dashboard"),
    path("sales/", views.sales_dashboard, name="sales_dashboard"),
    path("sales-list/", views.sales, name="sales"),   
    path("add_sales/", views.add_sales, name="add_sales"),
    path('sales/<int:pk>/edit/', views.sales_edit, name='sales_edit'),
    path('sales/<int:pk>/delete/', views.sales_delete, name='sales_delete'),
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
    path('suppliers/reports/', views.supply_reports, name='supply_reports'),
]