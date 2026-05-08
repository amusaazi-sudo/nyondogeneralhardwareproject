from django.shortcuts import render, redirect
from .models import  Stock, Sale
# create your views here

def stocks (request):
    all_stock = Stock.objects.all()
    context = {
        "stock":all_stock
    }   
    return render(request, 'stock.html', context)

def add_stock (request):
    if request.method == "POST":
        body = request.POST
        sent_product_name = body.get('product_name')
        sent_product_code = body.get('product_code')
        sent_category = body.get('category')
        sent_quantity = body.get('quantity')
        sent_buying_price = body.get('buying_price')
        sent_selling_price = body.get('selling_price')
        print(sent_selling_price)

        new_stock = Stock()

        new_stock.product_name = sent_product_name
        new_stock.product_code = sent_product_code
        new_stock.category = sent_category
        new_stock.quantity = sent_quantity
        new_stock.buying_price = sent_buying_price
        new_stock.selling_price = sent_selling_price

        new_stock.save()

        return redirect('stocks')
    return render(request, 'stock_reg.html')


def sales (request):
    all_sales = Sale.objects.all()
    context = {
        "sales":all_sales
    }
    return render(request, 'sales.html', context)

def add_sales (request):
    if request.method == "POST":
        payload = request.POST
        sent_product_sold = payload.get('product_sold')
        sent_date = payload.get('date')
        sent_quantity_sold = payload.get('quantity_sold')
        sent_receipt_number = payload.get('receipt_number')
        sent_payment_method = payload.get('payment_method')

        new_sale = Sale()

        new_sale.product_sold = sent_product_sold
        new_sale.date = sent_date
        new_sale.quantity_sold = sent_quantity_sold
        new_sale.receipt_number = sent_receipt_number
        new_sale.payment_method = sent_payment_method

        new_sale.save()

        return redirect('sales')
    return render(request, 'sales_reg.html')

def dashboard(request):
    # Collect summary data from your models
    sales_count = Sale.objects.count() or 0
    stock_count = Stock.objects.count()
    # transport_count = Transport.objects.count()
    # credit_count = CreditScheme.objects.count()

    # Example: recent activities (last 5 records)
    recent_sales = Sale.objects.order_by('-date')[:5]

    context = {
        "sales_count": sales_count,
        "stock_count": stock_count,
        # "transport_count": transport_count,
        # "credit_count": credit_count,
        "recent_sales": recent_sales,
    }
    return render(request, "dashboard.html", context)







        
