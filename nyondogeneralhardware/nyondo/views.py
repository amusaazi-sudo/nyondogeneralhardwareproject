from django.shortcuts import render, redirect,get_object_or_404
from .models import  Stock, Sale
# create your views here
#STOCK VIEWS
def stocks (request):
    all_stock = Stock.objects.all()
    context = {
        "stocks":all_stock
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

def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        body = request.POST
        stock.product_name = body.get('product_name')
        stock.product_code = body.get('product_code')
        stock.category = body.get('category')
        stock.quantity = body.get('quantity')
        stock.buying_price = body.get('buying_price')
        stock.selling_price = body.get('selling_price')
        stock.save()
        return redirect('stocks')
    return render(request, 'stock_edit.html', {"stock": stock})

def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        stock.delete()
        return redirect('stocks')
    return render(request, 'stock_delete.html', {"stock": stock})


#SALES VIEWS
def sales(request):
    sales = Sale.objects.all()
    context = {
        "sales":sales
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

        return redirect('/sales/')
    return render(request, 'sales_reg.html')

def sales_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        payload = request.POST
        sale.product_sold = payload.get('product_sold')
        sale.date = payload.get('date')
        sale.quantity_sold = payload.get('quantity_sold')
        sale.receipt_number = payload.get('receipt_number')
        sale.payment_method = payload.get('payment_method')
        sale.save()
        return redirect('sales')
    return render(request, 'sales_edit.html', {"sale": sale})

def sales_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        sale.delete()
        return redirect('sales')
    return render(request, 'sales_delete.html', {"sale": sale})



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

def sales_dashboard(request):
    return render(request, 'sales_dashboard.html')

def stock_dashboard(request):
    stocks = Stock.objects.all()
    context = {
        'stocks': stocks,
        'total_items': stocks.count(),
        'low_stock': stocks.filter(quantity__gt=0, quantity__lte=10).count(),
        'out_of_stock': stocks.filter(quantity=0).count(),
        'category_count': stocks.values('category').distinct().count(),
    }
    return render(request, 'stock_dashboard.html', context)
        
# def deposit_create(request):
#     """Create a new deposit receipt"""
#     if request.method == 'POST':
#         # Create new deposit from form data
#         deposit = Deposit(
#             receipt_number=request.POST.get('receipt_number'),
#             date=request.POST.get('date'),
#             customer_name=request.POST.get('customer_name'),
#             NIN=request.POST.get('NIN'),
#             contact=request.POST.get('contact'),
#             signature=request.POST.get('signature'),
#             deposit_amount=request.POST.get('deposit_amount'),
#             expiry_date=request.POST.get('expiry_date'),
#             total_balance=request.POST.get('total_balance')
#         )
#         deposit.save()
#         messages.success(request, 'Deposit saved successfully!')
#         return redirect('deposit_list')
    
#     return render(request, 'deposit_form.html')

# def deposit_list(request):
#     """Display all deposits"""
#     deposits = Deposit.objects.all()
#     return render(request, 'deposit_list.html', {'deposits': deposits})

# def deposit_edit(request, pk):
#     """Edit a deposit"""
#     deposit = get_object_or_404(Deposit, pk=pk)
    
#     if request.method == 'POST':
#         # Update the deposit with new values
#         deposit.receipt_number = request.POST.get('receipt_number')
#         deposit.date = request.POST.get('date')
#         deposit.customer_name = request.POST.get('customer_name')
#         deposit.NIN = request.POST.get('NIN')
#         deposit.contact = request.POST.get('contact')
#         deposit.signature = request.POST.get('signature')
#         deposit.deposit_amount = request.POST.get('deposit_amount')
#         deposit.expiry_date = request.POST.get('expiry_date')
#         deposit.total_balance = request.POST.get('total_balance')
#         deposit.save()
#         messages.success(request, 'Deposit updated successfully!')
#         return redirect('deposit_list')
    
#     return render(request, 'deposit_edit.html', {'deposit': deposit})

# def deposit_delete(request, pk):
#     """Delete a deposit"""
#     deposit = get_object_or_404(Deposit, pk=pk)
    
#     if request.method == 'POST':
#         deposit.delete()
#         messages.success(request, 'Deposit deleted successfully!')
#         return redirect('deposit_list')
    
#     return render(request, 'deposit_confirm_delete.html', {'deposit': deposit})




# fssuming you have a Credit model

# def credit_view(request):
#     if request.method == 'POST':
#         # Get form data
#         receipt_number = request.POST.get('receipt_number')
#         date = request.POST.get('date')
#         customer_name = request.POST.get('customer_name')
#         nin = request.POST.get('nin')
#         contact = request.POST.get('contact')
#         credit_amount = request.POST.get('credit_amount')
#         expiry_date = request.POST.get('expiry_date')
#         balance = request.POST.get('balance')
        
#         # Save to database
#         credit = Credit.objects.create(
#             receipt_number=receipt_number,
#             date=date,
#             customer_name=customer_name,
#             nin=nin,
#             contact=contact,
#             credit_amount=credit_amount,
#             expiry_date=expiry_date,
#             balance=balance
#         )
        
#         messages.success(request, 'Credit saved successfully!')
#         return redirect('credit')  # Redirect to clear form or show success
    
#     return render(request, 'credit.html')