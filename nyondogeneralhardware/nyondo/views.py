# COMMENT-HEADER
# File: nyondo/views.py
# Simple review note: use this file for code logic and Django app behavior.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from django.utils import timezone
from .models import Stock, Sale, Receipt, Supplier, SupplierPayment, Customer, CustomerPayment, Deposit, DepositPayment, DepositPaymentReceipt, SCHEME_ITEMS
from datetime import date as date_type
# create your views here

ALLOWED_ROLES = {'sales_manager', 'stock_manager', 'admin'}

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Both username and password are required.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')

        user_groups = set(user.groups.values_list('name', flat=True))
        if not user_groups.intersection(ALLOWED_ROLES) and not user.is_superuser:
            messages.error(request, 'You are not authorised to access this system.')
            return render(request, 'login.html')

        login(request, user)
        return redirect('dashboard')

    return render(request, 'login.html')


def logout_view(request):
    """Logout the current user and redirect to login page"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


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
        sent_specification = body.get('specification', '').strip()
        sent_product_code = body.get('product_code')
        sent_category = body.get('category')
        sent_quantity = body.get('quantity')
        sent_buying_price = body.get('buying_price')
        sent_selling_price = body.get('selling_price')
        sent_date = body.get('date')

        # collect all validation errors before saving
        errors = []
        SPEC_REQUIRED = ['cement', 'iron_bars', 'nails', 'barbed_wire', 'iron_sheets']
        if sent_product_name in SPEC_REQUIRED and not sent_specification:
            errors.append('Please select a specification for the chosen product.')

        # validate quantity is a whole positive number
        try:
            sent_quantity = int(sent_quantity)
            if sent_quantity < 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')

        # validate buying price is a positive number
        try:
            sent_buying_price = int(sent_buying_price)
            if sent_buying_price < 0:
                errors.append('Buying price must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Buying price must be a valid number.')

        # validate selling price is a positive number
        try:
            sent_selling_price = int(sent_selling_price)
            if sent_selling_price < 0:
                errors.append('Selling price must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Selling price must be a valid number.')

        # validate date is not in the future
        try:
            from datetime import date as date_type
            parsed_date = date_type.fromisoformat(sent_date)
            if parsed_date > timezone.now().date():
                errors.append('Date cannot be in the future.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid date.')

        # if any errors exist, show them and re-render the form with the user's input
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'stock_reg.html', {'data': body})

        new_stock = Stock()
        new_stock.product_name = sent_product_name
        new_stock.specification = sent_specification or None
        new_stock.product_code = sent_product_code
        new_stock.category = sent_category
        new_stock.quantity = sent_quantity
        new_stock.buying_price = sent_buying_price
        new_stock.selling_price = sent_selling_price
        new_stock.date = parsed_date
        new_stock.save()

        messages.success(request, 'Stock added successfully.')
        return redirect('stocks')
    return render(request, 'stock_reg.html')

def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        body = request.POST
        errors = []

        sent_date = body.get('date')
        # validate date is not in the future and not before the original record date
        try:
            from datetime import date as date_type
            parsed_date = date_type.fromisoformat(sent_date)
            if parsed_date > timezone.now().date():
                errors.append('Date cannot be in the future.')
            if parsed_date < stock.date:
                errors.append('Date cannot be earlier than the original record date.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid date.')

        # if date is invalid, show errors and re-render the edit form
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'stock_edit.html', {'stock': stock})

        sent_specification = body.get('specification', '').strip()
        SPEC_REQUIRED = ['cement', 'iron_bars', 'nails', 'barbed_wire', 'iron_sheets']
        if body.get('product_name') in SPEC_REQUIRED and not sent_specification:
            errors.append('Please select a specification for the chosen product.')
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'stock_edit.html', {'stock': stock})
        stock.product_name = body.get('product_name')
        stock.specification = sent_specification or None
        stock.product_code = body.get('product_code')
        stock.category = body.get('category')
        stock.quantity = body.get('quantity')
        stock.buying_price = body.get('buying_price')
        stock.selling_price = body.get('selling_price')
        stock.date = parsed_date
        stock.save()
        return redirect('stocks')
    return render(request, 'stock_edit.html', {"stock": stock})

def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        stock.delete()
        return redirect('stocks')
    return render(request, 'stock_delete.html', {"stock": stock})








# SALES VIEWS

# Shows all sales records
def sales(request):
    sales = Sale.objects.all()
    context = {
        "sales":sales
    }
    return render(request, 'sales.html', context)


# Saves a new sale, deducts from stock automatically, then auto-creates its receipt
def add_sales(request):
    if request.method == "POST":
        payload = request.POST
        sent_customer_name = payload.get('customer_name', '').strip()
        sent_product_sold = payload.get('product_sold')
        sent_specification = payload.get('specification', '').strip()
        sent_payment_method = payload.get('payment_method')
        sent_delivery = payload.get('delivery') == 'on'
        sent_distance = payload.get('address_distance')
        sent_address = payload.get('address', '').strip()

        SPEC_REQUIRED = ['cement', 'iron_bars', 'nails', 'barbed_wire', 'iron_sheets']
        errors = []

        if not sent_customer_name:
            errors.append('Please enter a customer name.')

        # validate specification is provided for products that require it
        if sent_product_sold in SPEC_REQUIRED and not sent_specification:
            errors.append('Please select a specification for the chosen product.')

        # validate quantity is a positive whole number
        try:
            sent_quantity_sold = int(payload.get('quantity_sold'))
            if sent_quantity_sold <= 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            sent_quantity_sold = None

        if sent_delivery:
            if not sent_address:
                errors.append('Please enter the delivery address.')
            if sent_distance:
                try:
                    sent_address_distance = int(sent_distance)
                    if sent_address_distance < 0:
                        errors.append('Distance must be zero or greater.')
                except (ValueError, TypeError):
                    errors.append('Please select a valid delivery distance.')
            else:
                errors.append('Please choose delivery distance.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'sales_reg.html', {'data': payload})

        # find the matching stock item by product name and specification
        stock = Stock.objects.filter(
            product_name=sent_product_sold,
            specification=sent_specification or None
        ).first()

        # block the sale if no matching stock record exists
        if not stock:
            messages.error(request, 'No stock record found for this product and specification.')
            return render(request, 'sales_reg.html', {'data': payload})

        # block the sale if there is not enough stock available
        if stock.quantity < sent_quantity_sold:
            messages.error(request, f'Not enough stock. Only {stock.quantity} unit(s) available.')
            return render(request, 'sales_reg.html', {'data': payload})

        # deduct the sold quantity from stock
        stock.quantity -= sent_quantity_sold
        stock.save()

        customer = Customer.objects.filter(name__iexact=sent_customer_name).first()
        if not customer:
            customer = Customer.objects.create(
                name=sent_customer_name,
                address=sent_address if sent_delivery else None,
                address_distance=sent_address_distance if sent_delivery else None,
            )
        else:
            if sent_delivery:
                customer.address = sent_address
                customer.address_distance = sent_address_distance
                customer.save()

        # save the sale record
        new_sale = Sale(
            customer=customer,
            product_sold=sent_product_sold,
            specification=sent_specification or None,
            quantity_sold=sent_quantity_sold,
            payment_method=sent_payment_method,
            delivery=sent_delivery,
        )
        new_sale.save()

        # auto-create the receipt linked to this sale
        Receipt.objects.create(sale=new_sale)
        return redirect('sales')
    return render(request, 'sales_reg.html')


# Edits an existing sale (receipt stays linked, no changes needed there)
def sales_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        payload = request.POST
        sent_product_sold = payload.get('product_sold')
        sent_specification = payload.get('specification', '').strip()
        SPEC_REQUIRED = ['cement', 'iron_bars', 'nails', 'barbed_wire', 'iron_sheets']
        errors = []
        if sent_product_sold in SPEC_REQUIRED and not sent_specification:
            errors.append('Please select a specification for the chosen product.')
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'sales_edit.html', {'sale': sale})
        sale.product_sold = sent_product_sold
        sale.specification = sent_specification or None
        sale.quantity_sold = payload.get('quantity_sold')
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
    today = timezone.now().date()
    sales_count = Sale.objects.count() or 0
    stock_count = Stock.objects.count() or 0
    transport_count = Sale.objects.filter(delivery=True).count() or 0
    credit_count = Customer.objects.filter(bought_on_credit=True).count() or 0
    active_debtors = Deposit.objects.filter(total_balance__gt=0).count() or 0
    deposit_scheme_total = Deposit.objects.aggregate(
        total_amount=Sum('deposit_amount'),
        total_balance=Sum('total_balance')
    )
    deposit_scheme_value = (deposit_scheme_total.get('total_amount') or 0) + (deposit_scheme_total.get('total_balance') or 0)
    receipts_today = Receipt.objects.filter(issued_on__date=today).count() or 0
    recent_receipts = Receipt.objects.select_related('sale').order_by('-issued_on')[:5]
    recent_supplier_payments = SupplierPayment.objects.select_related('supplier').order_by('-date')[:5]
    recent_deposit_payments = DepositPayment.objects.select_related('deposit__customer').order_by('-date')[:5]

    context = {
        'sales_count': sales_count,
        'stock_count': stock_count,
        'transport_count': transport_count,
        'credit_count': credit_count,
        'active_debtors': active_debtors,
        'deposit_scheme_value': deposit_scheme_value,
        'receipts_today': receipts_today,
        'recent_receipts': recent_receipts,
        'recent_supplier_payments': recent_supplier_payments,
        'recent_deposit_payments': recent_deposit_payments,
    }
    return render(request, 'dashboard.html', context)

# Shows all auto-generated receipts, newest first
def sales_receipt(request):
    receipts = Receipt.objects.select_related('sale').order_by('-issued_on')  # select_related avoids extra DB queries
    return render(request, 'sales_receipt.html', {'receipts': receipts})


def sale_receipt(request, pk):
    receipt = get_object_or_404(Receipt, sale_id=pk)
    return render(request, 'sale_receipt.html', {'receipt': receipt})


# Sales dashboard — passes real sale + receipt data to the template
def sales_dashboard(request):
    today = timezone.now().date()
    sales = Sale.objects.prefetch_related('receipt').order_by('-date')  # prefetch_related loads receipts efficiently
    todays_sales = Sale.objects.filter(date=today).count() or 0
    transport_trips = Sale.objects.filter(delivery=True).count() or 0
    total_revenue = sum(s.sale_total for s in sales)

    context = {
        'sales': sales,
        'todays_sales': todays_sales,
        'transport_trips': transport_trips,
        'total_revenue': total_revenue,
    }
    return render(request, 'sales_dashboard.html', context)

def stock_dashboard(request):
    stocks = Stock.objects.all()
    low_stock_items = stocks.filter(quantity__gt=0, quantity__lte=10)
    out_of_stock_items = stocks.filter(quantity=0)
    context = {
        'stocks': stocks,
        'total_items': stocks.count(),
        'low_stock': low_stock_items.count(),
        'out_of_stock': out_of_stock_items.count(),
        'category_count': stocks.values('category').distinct().count(),
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
    }
    return render(request, 'stock_dashboard.html', context)


def reports(request):
    """Aggregate domain records and receipts for a reports interface."""
    sales = Sale.objects.select_related('customer').prefetch_related('receipt').order_by('-date')
    sales_receipts = Receipt.objects.select_related('sale').order_by('-issued_on')
    stocks = Stock.objects.all().order_by('-date')
    suppliers = Supplier.objects.all().order_by('-delivery_date')
    supplier_payments = SupplierPayment.objects.select_related('supplier').order_by('-date')
    customers = Customer.objects.all().order_by('-date_registered')
    customer_payments = CustomerPayment.objects.select_related('customer').order_by('-date')
    deposits = Deposit.objects.select_related('customer').order_by('-date')
    deposit_payments = DepositPayment.objects.select_related('deposit').order_by('-date')
    deposit_payment_receipts = DepositPaymentReceipt.objects.order_by('-payment_date')

    context = {
        'sales': sales,
        'sales_receipts': sales_receipts,
        'stocks': stocks,
        'suppliers': suppliers,
        'supplier_payments': supplier_payments,
        'customers': customers,
        'customer_payments': customer_payments,
        'deposits': deposits,
        'deposit_payments': deposit_payments,
        'deposit_payment_receipts': deposit_payment_receipts,
        'sales_total': sum(s.sale_total for s in sales),
        'stock_value': sum(st.quantity * st.selling_price for st in stocks),
        'supplier_amount_owed': sum(s.amount_remaining for s in suppliers),
        'customer_amount_owed': sum(c.amount_remaining for c in customers),
        'deposit_amount_outstanding': sum(d.amount_remaining for d in deposits),
        'supplier_payment_total': sum(p.amount for p in supplier_payments),
        'customer_payment_total': sum(p.amount for p in customer_payments),
    }
    return render(request, 'reports.html', context)


# SUPPLIER VIEWS

def supply_reports(request):
    from django.db.models import Sum, Count
    suppliers = Supplier.objects.all()
    total_suppliers = suppliers.count()
    paid = suppliers.filter(payment_status='Paid').count()
    partial = suppliers.filter(payment_status='Partial').count()
    pending = suppliers.filter(payment_status='Pending').count()
    total_cost = sum(s.total_cost for s in suppliers)
    total_paid = sum(s.total_paid for s in suppliers)
    total_owed = total_cost - total_paid
    return render(request, 'supply_reports.html', {
        'suppliers': suppliers,
        'total_suppliers': total_suppliers,
        'paid': paid,
        'partial': partial,
        'pending': pending,
        'total_cost': total_cost,
        'total_paid': total_paid,
        'total_owed': total_owed,
    })

def suppliers(request):
    all_suppliers = Supplier.objects.all()
    return render(request, 'supplier.html', {'suppliers': all_suppliers})


def add_supplier(request):
    if request.method == 'POST':
        body = request.POST
        errors = []

        SPEC_REQUIRED = ['cement', 'iron_bars', 'nails', 'barbed_wire', 'iron_sheets']
        if body.get('product') in SPEC_REQUIRED and not body.get('specification', '').strip():
            errors.append('Please select a specification for the chosen product.')

        try:
            qty = int(body.get('quantity'))
            if qty < 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            qty = None

        try:
            deposit = int(body.get('deposit', 0))
            if deposit < 0:
                errors.append('Deposit must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Deposit must be a valid whole number.')
            deposit = None

        try:
            amount_owed = int(body.get('amount_owed') or 0)
            if amount_owed < 0:
                errors.append('Amount owed must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Amount owed must be a valid whole number.')
            amount_owed = 0

        try:
            delivery_date = date_type.fromisoformat(body.get('delivery_date'))
        except (ValueError, TypeError):
            errors.append('Please enter a valid delivery date.')
            delivery_date = None

        due_date = None
        if body.get('due_date'):
            try:
                due_date = date_type.fromisoformat(body.get('due_date'))
            except (ValueError, TypeError):
                errors.append('Please enter a valid due date.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'supplier_reg.html', {'data': body})

        Supplier.objects.create(
            supplier_company=body.get('supplier_company'),
            name=body.get('name'),
            phone=body.get('phone'),
            email=body.get('email') or None,
            address=body.get('address') or None,
            product=body.get('product'),
            specification=body.get('specification', '').strip() or None,
            quantity=qty,
            deposit=deposit,
            selling_price=None,
            delivery_date=delivery_date,
            is_credit=bool(body.get('is_credit')),
            amount_owed=amount_owed,
            payment_status=body.get('payment_status', 'Pending'),
            due_date=due_date,
        )
        messages.success(request, 'Supplier added successfully.')
        return redirect('suppliers')
    return render(request, 'supplier_reg.html')


def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        body = request.POST
        errors = []

        SPEC_REQUIRED = ['cement', 'iron_bars', 'nails', 'barbed_wire', 'iron_sheets']
        if body.get('product') in SPEC_REQUIRED and not body.get('specification', '').strip():
            errors.append('Please select a specification for the chosen product.')

        try:
            qty = int(body.get('quantity'))
            if qty < 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            qty = None

        try:
            deposit = int(body.get('deposit', 0))
            if deposit < 0:
                errors.append('Deposit must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Deposit must be a valid whole number.')
            deposit = None

        try:
            amount_owed = int(body.get('amount_owed') or 0)
            if amount_owed < 0:
                errors.append('Amount owed must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Amount owed must be a valid whole number.')
            amount_owed = 0

        try:
            delivery_date = date_type.fromisoformat(body.get('delivery_date'))
        except (ValueError, TypeError):
            errors.append('Please enter a valid delivery date.')
            delivery_date = None

        due_date = None
        if body.get('due_date'):
            try:
                due_date = date_type.fromisoformat(body.get('due_date'))
            except (ValueError, TypeError):
                errors.append('Please enter a valid due date.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'supplier_reg.html', {'data': body, 'supplier': supplier})

        supplier.supplier_company = body.get('supplier_company')
        supplier.name = body.get('name')
        supplier.phone = body.get('phone')
        supplier.email = body.get('email') or None
        supplier.address = body.get('address') or None
        supplier.product = body.get('product')
        supplier.specification = body.get('specification', '').strip() or None
        supplier.quantity = qty
        supplier.deposit = deposit
        supplier.delivery_date = delivery_date
        supplier.is_credit = bool(body.get('is_credit'))
        supplier.amount_owed = amount_owed
        supplier.payment_status = body.get('payment_status', 'Pending')
        supplier.due_date = due_date
        supplier.save()
        messages.success(request, 'Supplier updated successfully.')
        return redirect('suppliers')
    return render(request, 'supplier_reg.html', {'data': supplier.__dict__, 'supplier': supplier})


def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('suppliers')
    return render(request, 'supplier_delete.html', {'supplier': supplier})


def supplier_view(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    payments = supplier.payments.order_by('-date')

    if request.method == 'POST':
        errors = []
        try:
            amount = int(request.POST.get('amount', '0'))
            if amount <= 0:
                errors.append('Payment amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Enter a valid whole number for the amount.')
            amount = 0

        remaining = supplier.total_cost - supplier.total_paid
        if not errors and amount > remaining:
            errors.append(f'Amount exceeds remaining balance of UGX {remaining}.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            SupplierPayment.objects.create(
                supplier=supplier,
                amount=amount,
                note=request.POST.get('note', '').strip(),
            )
            new_paid = supplier.total_paid  # recalculated after save
            if new_paid >= supplier.total_cost:
                supplier.payment_status = 'Paid'
                supplier.amount_owed = 0
            else:
                supplier.payment_status = 'Partial'
                supplier.amount_owed = supplier.total_cost - new_paid
            supplier.save()
            messages.success(request, 'Payment recorded successfully.')
            return redirect('supplier_view', pk=pk)

    return render(request, 'supply_credit_track.html', {
        'supplier': supplier,
        'payments': payments,
    })



# CUSTOMER VIEWS

def customers(request):
    all_customers = Customer.objects.all().order_by('-date_registered')
    return render(request, 'customer.html', {'customers': all_customers})


def add_customer(request):
    if request.method == 'POST':
        body = request.POST
        errors = []

        name = body.get('name', '').strip()
        phone = body.get('phone', '').strip()

        address_distance = None
        try:
            address_distance = int(body.get('address_distance')) if body.get('address_distance') else None
            if address_distance is not None and address_distance < 0:
                errors.append('Address distance must be zero or greater.')
        except (ValueError, TypeError):
            errors.append('Address distance must be a valid integer.')

        if not name:
            errors.append('Customer name is required.')
        if not phone:
            errors.append('Phone number is required.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'customer_reg.html', {'data': body})

        Customer.objects.create(
            name=name,
            phone=phone,
            email=body.get('email') or None,
            address=body.get('address') or None,
            address_distance=address_distance,
            NIN=body.get('NIN') or None,
            bought_on_credit=bool(body.get('bought_on_credit')),
        )
        messages.success(request, 'Customer registered successfully.')
        return redirect('customer')
    return render(request, 'customer_reg.html')


def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        body = request.POST
        errors = []
        name = body.get('name', '').strip()
        phone = body.get('phone', '').strip()

        if not name:
            errors.append('Customer name is required.')
        if not phone:
            errors.append('Phone number is required.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'customer_edit.html', {'data': body, 'customer': customer})

        address_distance = None
        try:
            address_distance = int(body.get('address_distance')) if body.get('address_distance') else None
            if address_distance is not None and address_distance < 0:
                errors.append('Address distance must be zero or greater.')
        except (ValueError, TypeError):
            errors.append('Address distance must be a valid integer.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'customer_edit.html', {'data': body, 'customer': customer})

        customer.name = name
        customer.phone = phone
        customer.email = body.get('email') or None
        customer.address = body.get('address') or None
        customer.address_distance = address_distance
        customer.NIN = body.get('NIN') or None
        customer.bought_on_credit = bool(body.get('bought_on_credit'))
        customer.save()

        messages.success(request, 'Customer updated successfully.')
        return redirect('customer')

    return render(request, 'customer_edit.html', {
        'data': {
            'name': customer.name,
            'phone': customer.phone,
            'email': customer.email,
            'address': customer.address,
            'address_distance': customer.address_distance,
            'NIN': customer.NIN,
            'bought_on_credit': customer.bought_on_credit,
        },
        'customer': customer,
    })


def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('customer')
    return render(request, 'customer_delete.html', {'customer': customer})


def customer_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.order_by('-date')
    return render(request, 'customer_tracker.html', {
        'customer': customer,
        'sales': sales,
    })


# DEPOSIT SCHEME VIEWS

def deposits(request):
    all_deposits = Deposit.objects.select_related('customer').order_by('-date')
    total_debtors = all_deposits.count()
    total_received = all_deposits.aggregate(total=Sum('deposit_amount'))['total'] or 0
    return render(request, 'deposit.html', {
        'deposits': all_deposits,
        'total_debtors': total_debtors,
        'total_received': total_received,
    })


def add_deposit(request):
    customers = Customer.objects.all().order_by('name')
    if request.method == 'POST':
        body = request.POST
        errors = []
        try:
            deposit_amount = int(body.get('deposit_amount'))
            if deposit_amount <= 0:
                errors.append('Deposit amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Deposit amount must be a valid number.')
            deposit_amount = None
        try:
            total_balance = int(body.get('total_balance'))
            if total_balance < 0:
                errors.append('Total balance must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Total balance must be a valid number.')
            total_balance = None
        try:
            expiry_date = date_type.fromisoformat(body.get('expiry_date'))
            if expiry_date <= date_type.today():
                errors.append('Expiry date must be in the future.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid expiry date.')
            expiry_date = None
        customer_manual = (body.get('customer_manual') or '').strip()
        customer_field = body.get('customer')
        if not customer_field and not customer_manual:
            errors.append('Please select or enter a customer.')
        if not body.get('contact', '').strip():
            errors.append('Contact is required.')
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'deposit_reg.html', {'customers': customers, 'scheme_items': SCHEME_ITEMS, 'data': body})
        # determine customer object: prefer manual name if provided
        if customer_manual:
            customer_obj, created = Customer.objects.get_or_create(name=customer_manual)
        else:
            try:
                customer_obj = Customer.objects.get(pk=customer_field)
            except Customer.DoesNotExist:
                messages.error(request, 'Selected customer was not found.')
                return render(request, 'deposit_reg.html', {'customers': customers, 'scheme_items': SCHEME_ITEMS, 'data': body})
        Deposit.objects.create(
            customer=customer_obj,
            item=body.get('item'),
            NIN=body.get('NIN') or None,
            contact=body.get('contact', '').strip(),
            deposit_amount=deposit_amount,
            expiry_date=expiry_date,
            total_balance=total_balance,
        )
        messages.success(request, 'Deposit recorded successfully.')
        return redirect('deposits')
    return render(request, 'deposit_reg.html', {'customers': customers, 'scheme_items': SCHEME_ITEMS})


def deposit_edit(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    customers = Customer.objects.all().order_by('name')
    if request.method == 'POST':
        body = request.POST
        errors = []
        try:
            deposit_amount = int(body.get('deposit_amount'))
            if deposit_amount <= 0:
                errors.append('Deposit amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Deposit amount must be a valid number.')
            deposit_amount = None
        try:
            total_balance = int(body.get('total_balance'))
            if total_balance < 0:
                errors.append('Total balance must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Total balance must be a valid number.')
            total_balance = None
        try:
            expiry_date = date_type.fromisoformat(body.get('expiry_date'))
        except (ValueError, TypeError):
            errors.append('Please enter a valid expiry date.')
            expiry_date = None
        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'deposit_edit.html', {'deposit': deposit, 'customers': customers, 'scheme_items': SCHEME_ITEMS})
        deposit.customer = get_object_or_404(Customer, pk=body.get('customer'))
        deposit.item = body.get('item')
        deposit.NIN = body.get('NIN') or None
        deposit.contact = body.get('contact', '').strip()
        deposit.deposit_amount = deposit_amount
        deposit.expiry_date = expiry_date
        deposit.total_balance = total_balance
        deposit.save()
        messages.success(request, 'Deposit updated successfully.')
        return redirect('deposits')
    return render(request, 'deposit_edit.html', {'deposit': deposit, 'customers': customers, 'scheme_items': SCHEME_ITEMS})


def deposit_delete(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    if request.method == 'POST':
        deposit.delete()
        messages.success(request, 'Deposit deleted.')
        return redirect('deposits')
    return render(request, 'deposit_delete.html', {'deposit': deposit})


def deposit_progress(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    payments = deposit.payments.order_by('-date')

    if request.method == 'POST':
        errors = []
        try:
            amount = int(request.POST.get('amount', '0'))
            if amount <= 0:
                errors.append('Payment amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Enter a valid whole number for the amount.')
            amount = 0

        remaining = deposit.amount_remaining
        if not errors and amount > remaining:
            errors.append(f'Amount exceeds remaining balance of UGX {remaining}.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            # Create the deposit payment
            deposit_payment = DepositPayment.objects.create(
                deposit=deposit,
                amount=amount,
                note=request.POST.get('note', '').strip(),
            )
            
            # Calculate balance tracking
            balance_before = deposit.amount_remaining
            balance_after = max(balance_before - amount, 0)
            
            # Create temporary receipt for this payment
            receipt = DepositPaymentReceipt.objects.create(
                deposit_payment=deposit_payment,
                customer_name=deposit.customer.name,
                customer_phone=deposit.contact,
                customer_nin=deposit.customer.NIN,
                customer_address=deposit.customer.address,
                deposit_receipt_number=deposit.receipt_number,
                item_name=deposit.get_item_display(),
                amount_paid=amount,
                payment_method=request.POST.get('note', 'Cash').split()[0] if request.POST.get('note') else 'Cash',
                balance_before_payment=balance_before,
                balance_after_payment=balance_after,
                total_deposit_amount=deposit.deposit_amount,
                total_balance_owed=deposit.total_balance,
                note=request.POST.get('note', '').strip(),
            )
            
            messages.success(request, 'Installment payment recorded successfully.')
            return redirect('payment_receipt', receipt_id=receipt.id)

    return render(request, 'deposit_progress.html', {
        'deposit': deposit,
        'payments': payments,
    })


def deposit_receipts(request):
    receipts = Deposit.objects.select_related('customer').order_by('-date')
    return render(request, 'deposit_receipts.html', {'receipts': receipts})


def deposit_receipt(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    return render(request, 'deposit_reciept.html', {'deposit': deposit})


def payment_receipt(request, receipt_id):
    """Display temporary receipt issued for a deposit payment"""
    receipt = get_object_or_404(DepositPaymentReceipt, pk=receipt_id)
    return render(request, 'payment_receipt.html', {'receipt': receipt})


def payment_receipts_list(request):
    """List all payment receipts with filtering options"""
    receipts = DepositPaymentReceipt.objects.select_related('deposit_payment__deposit__customer').order_by('-payment_date')
    
    # Filter by customer name if provided
    customer_filter = request.GET.get('customer', '').strip()
    if customer_filter:
        receipts = receipts.filter(customer_name__icontains=customer_filter)
    
    # Filter by date range if provided
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    
    if from_date:
        from datetime import datetime
        try:
            from_datetime = datetime.fromisoformat(from_date)
            receipts = receipts.filter(payment_date__gte=from_datetime)
        except (ValueError, TypeError):
            pass
    
    if to_date:
        from datetime import datetime
        try:
            to_datetime = datetime.fromisoformat(to_date)
            receipts = receipts.filter(payment_date__lte=to_datetime)
        except (ValueError, TypeError):
            pass
    
    # Calculate totals
    total_amount_paid = sum(r.amount_paid for r in receipts)
    
    context = {
        'receipts': receipts,
        'customer_filter': customer_filter,
        'from_date': from_date,
        'to_date': to_date,
        'total_amount_paid': total_amount_paid,
    }
    return render(request, 'payment_receipts_list.html', context)
