# views
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import Stock, Sale, Receipt, Supplier, SupplierPayment, SupplierReceipt, Customer, CustomerPayment, Deposit, DepositPayment, DepositPaymentReceipt, SCHEME_ITEMS
from datetime import date as date_type
import re


# ─────────────────────────────────────────────
# CONSTANTS & VALIDATORS
# ─────────────────────────────────────────────

ALLOWED_ROLES = {'sales_manager', 'stock_manager', 'admin'}

SPEC_CHOICES = {
    'cement': {'cem_iin', 'cem_iiin'},
    'iron_bars': {'10mm', '12mm', '16mm'},
    'nails': {'1inch', '3inch', '4inch', '5inch', 'roofing_5kg'},
    'barbed_wire': {'high_tensile', 'low_tensile'},
    'iron_sheets': {
        f'{gauge}_{color}'
        for gauge in ('gauge_28', 'gauge_30', 'gauge_32')
        for color in ('red', 'blue', 'green', 'brown', 'grey')
    },
}
SPEC_REQUIRED = set(SPEC_CHOICES)
CUSTOMER_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z\s'.-]*$")
UG_PHONE_RE = re.compile(r'^\+2567\d{8}$')
NIN_RE = re.compile(r'^\d{13}$')


# ─────────────────────────────────────────────
# ROLE CHECKER FUNCTIONS
# ─────────────────────────────────────────────

def is_admin(user):
    """Admin (superuser or admin group) — full access to everything."""
    return user.is_superuser or user.groups.filter(name='admin').exists()

def is_stock_manager(user):
    return user.groups.filter(name='stock_manager').exists()

def is_sales_manager(user):
    return user.groups.filter(name='sales_manager').exists()

# --- Combined access checkers ---

def can_access_stock(user):
    """Stock pages: admin + stock_manager only."""
    return is_admin(user) or is_stock_manager(user)

def can_access_sales(user):
    """Sales pages: all three roles."""
    return is_admin(user) or is_stock_manager(user) or is_sales_manager(user)

def can_access_suppliers(user):
    """Supplier pages: admin + stock_manager only."""
    return is_admin(user) or is_stock_manager(user)

def can_access_reports(user):
    """Reports: admin only."""
    return is_admin(user)

def can_access_dashboard(user):
    """General pages (dashboard, customers, deposits): any authenticated, allowed role."""
    return (
        user.is_superuser
        or user.groups.filter(name='admin').exists()
    )
def can_access_any(user):
    """General pages (customers, deposits, receipts): any allowed role."""
    return (
        user.is_superuser
        or user.groups.filter(name__in=['admin', 'stock_manager', 'sales_manager']).exists()
    )

# ─────────────────────────────────────────────
# SHARED VALIDATION HELPERS
# ─────────────────────────────────────────────

def validate_product_spec(product, specification, errors):
    if product in SPEC_REQUIRED and not specification:
        errors.append('Please select a gauge/size for the chosen product.')
        return
    if specification and specification not in SPEC_CHOICES.get(product, set()):
        errors.append('Selected gauge/size is not allowed for the chosen product.')


def validate_customer_identity(name, phone, nin, email, errors, customer_id=None, require_nin=False):
    if not name:
        errors.append('Customer name is required.')
    elif not CUSTOMER_NAME_RE.match(name) or any(char.isdigit() for char in name):
        errors.append('Customer name must contain letters only, with no numbers.')

    if not phone:
        errors.append('Phone number is required.')
    elif not UG_PHONE_RE.match(phone):
        errors.append('Phone number must use Ugandan format +2567XXXXXXXX.')

    if require_nin and not nin:
        errors.append('NIN is required.')
    if nin:
        if len(nin) > 15:
            errors.append('NIN must be maximum 15 characters long.')
        elif not nin.isalnum():
            errors.append('NIN must contain only letters and numbers (alphanumeric).')
        else:
            nin_matches = Customer.objects.filter(NIN=nin)
            if customer_id:
                nin_matches = nin_matches.exclude(pk=customer_id)
            if nin_matches.exists():
                errors.append('NIN is already registered to another customer.')

    if email:
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Email address must be valid.')


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────

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

        # Role-based redirect after login
        if user.is_superuser or user.groups.filter(name='admin').exists():
            return redirect('dashboard')
        elif user.groups.filter(name='sales_manager').exists():
            return redirect('sales_dashboard')
        elif user.groups.filter(name='stock_manager').exists():
            return redirect('stock_dashboard')
        else:
            return redirect('dashboard')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ─────────────────────────────────────────────
# STOCK VIEWS
# Access: admin + stock_manager only
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_stock, login_url='login')
def stocks(request):
    all_stock = Stock.objects.all()
    return render(request, 'stock.html', {'stocks': all_stock})


@login_required
@user_passes_test(can_access_stock, login_url='login')
def add_stock(request):
    today = timezone.now().date()
    if request.method == 'POST':
        body = request.POST
        sent_product_name = body.get('product_name')
        sent_specification = body.get('specification', '').strip()
        sent_product_code = body.get('product_code')
        sent_category = body.get('category')
        sent_quantity = body.get('quantity')
        sent_buying_price = body.get('buying_price')
        sent_selling_price = body.get('selling_price')
        sent_date = body.get('date')

        errors = []
        validate_product_spec(sent_product_name, sent_specification, errors)

        try:
            sent_quantity = int(sent_quantity)
            if sent_quantity < 0:
                errors.append('Quantity must be zero or greater.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')

        try:
            sent_buying_price = int(sent_buying_price)
            if sent_buying_price <= 0:
                errors.append('Unit cost must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Unit cost must be a valid number.')

        try:
            sent_selling_price = int(sent_selling_price)
            if sent_selling_price < 0:
                errors.append('Selling price cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Selling price must be a valid number.')

        if not errors and sent_selling_price < sent_buying_price:
            errors.append('Selling price must be greater than or equal to unit cost.')

        if Stock.objects.filter(product_name=sent_product_name, specification=sent_specification or None).exists():
            errors.append('This stock item already exists.')

        try:
            parsed_date = date_type.fromisoformat(sent_date)
            if parsed_date != today:
                errors.append('Stock order date must be today.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid date.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'stock_reg.html', {'data': body, 'today_date': today.isoformat()})

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
    return render(request, 'stock_reg.html', {'today_date': today.isoformat()})


@login_required
@user_passes_test(can_access_stock, login_url='login')
def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    today = timezone.now().date()
    if request.method == 'POST':
        body = request.POST
        errors = []

        sent_date = body.get('date')
        try:
            parsed_date = date_type.fromisoformat(sent_date)
            if parsed_date != today:
                errors.append('Stock order date must be today.')
        except (ValueError, TypeError):
            errors.append('Please enter a valid date.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'stock_edit.html', {'stock': stock, 'today_date': today.isoformat()})

        sent_product_name = body.get('product_name')
        sent_specification = body.get('specification', '').strip()
        validate_product_spec(sent_product_name, sent_specification, errors)

        try:
            sent_quantity = int(body.get('quantity'))
            if sent_quantity < 0:
                errors.append('Quantity must be zero or greater.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            sent_quantity = None

        try:
            sent_buying_price = int(body.get('buying_price'))
            if sent_buying_price <= 0:
                errors.append('Unit cost must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Unit cost must be a valid number.')
            sent_buying_price = None

        try:
            sent_selling_price = int(body.get('selling_price'))
            if sent_selling_price < 0:
                errors.append('Selling price cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Selling price must be a valid number.')
            sent_selling_price = None

        if sent_buying_price is not None and sent_selling_price is not None and sent_selling_price < sent_buying_price:
            errors.append('Selling price must be greater than or equal to unit cost.')

        if Stock.objects.filter(product_name=sent_product_name, specification=sent_specification or None).exclude(pk=stock.pk).exists():
            errors.append('This stock item already exists.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'stock_edit.html', {'stock': stock, 'today_date': today.isoformat()})

        stock.product_name = sent_product_name
        stock.specification = sent_specification or None
        stock.product_code = body.get('product_code')
        stock.category = body.get('category')
        stock.quantity = sent_quantity
        stock.buying_price = sent_buying_price
        stock.selling_price = sent_selling_price
        stock.date = parsed_date
        stock.save()
        return redirect('stocks')
    return render(request, 'stock_edit.html', {'stock': stock, 'today_date': today.isoformat()})


@login_required
@user_passes_test(can_access_stock, login_url='login')
def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        stock.delete()
        return redirect('stocks')
    return render(request, 'stock_delete.html', {'stock': stock})


# ─────────────────────────────────────────────
# SALES VIEWS
# Access: all three roles
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_sales, login_url='login')
def sales(request):
    all_sales = Sale.objects.all()
    return render(request, 'sales.html', {'sales': all_sales})


@login_required
@user_passes_test(can_access_sales, login_url='login')
def add_sales(request):
    if request.method == 'POST':
        payload = request.POST
        sent_customer_name = payload.get('customer_name', '').strip()
        sent_product_sold = payload.get('product_sold')
        sent_specification = payload.get('specification', '').strip()
        sent_payment_method = payload.get('payment_method')
        sent_delivery = payload.get('delivery') == 'on'
        sent_distance = payload.get('address_distance')
        sent_address = payload.get('address', '').strip()

        errors = []

        if not sent_customer_name:
            errors.append('Please enter a customer name.')
        elif not CUSTOMER_NAME_RE.match(sent_customer_name) or any(char.isdigit() for char in sent_customer_name):
            errors.append('Customer name must contain letters only, with no numbers.')

        validate_product_spec(sent_product_sold, sent_specification, errors)

        try:
            sent_quantity_sold = int(payload.get('quantity_sold'))
            if sent_quantity_sold <= 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            sent_quantity_sold = None

        sent_address_distance = None
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

        stock = Stock.objects.filter(
            product_name=sent_product_sold,
            specification=sent_specification or None
        ).first()

        if not stock:
            messages.error(request, 'No stock record found for this product and specification.')
            return render(request, 'sales_reg.html', {'data': payload})

        if stock.quantity < sent_quantity_sold:
            messages.error(request, f'Not enough stock. Only {stock.quantity} unit(s) available.')
            return render(request, 'sales_reg.html', {'data': payload})

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

        new_sale = Sale(
            customer=customer,
            product_sold=sent_product_sold,
            specification=sent_specification or None,
            quantity_sold=sent_quantity_sold,
            payment_method=sent_payment_method,
            delivery=sent_delivery,
        )
        new_sale.save()
        Receipt.objects.create(sale=new_sale)
        return redirect('sales')
    return render(request, 'sales_reg.html')


@login_required
@user_passes_test(can_access_sales, login_url='login')
def sales_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        payload = request.POST
        sent_product_sold = payload.get('product_sold')
        sent_specification = payload.get('specification', '').strip()
        errors = []
        validate_product_spec(sent_product_sold, sent_specification, errors)

        try:
            sent_quantity_sold = int(payload.get('quantity_sold'))
            if sent_quantity_sold <= 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            sent_quantity_sold = None

        if sent_quantity_sold is not None:
            stock = Stock.objects.filter(
                product_name=sent_product_sold,
                specification=sent_specification or None
            ).first()
            if not stock:
                errors.append('No stock record found for this product and specification.')
            else:
                available_quantity = stock.quantity + sale.quantity_sold
                if sent_product_sold != sale.product_sold or (sent_specification or None) != sale.specification:
                    available_quantity = stock.quantity
                if sent_quantity_sold > available_quantity:
                    errors.append(f'Not enough stock. Only {available_quantity} unit(s) available.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'sales_edit.html', {'sale': sale})

        sale.product_sold = sent_product_sold
        sale.specification = sent_specification or None
        sale.quantity_sold = sent_quantity_sold
        sale.payment_method = payload.get('payment_method')
        sale.save()
        return redirect('sales')
    return render(request, 'sales_edit.html', {'sale': sale})


@login_required
@user_passes_test(can_access_sales, login_url='login')
def sales_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        return redirect('sales')
    return render(request, 'sales_delete.html', {'sale': sale})


# ─────────────────────────────────────────────
# DASHBOARD VIEWS
# Access: all roles (redirected to role-appropriate dashboard after login)
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_dashboard, login_url='login')
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


@login_required
@user_passes_test(can_access_sales, login_url='login')
def sales_receipt(request):
    receipts = Receipt.objects.select_related('sale').order_by('-issued_on')
    return render(request, 'sales_receipt.html', {'receipts': receipts})


@login_required
@user_passes_test(can_access_sales, login_url='login')
def sale_receipt(request, pk):
    receipt = get_object_or_404(Receipt, sale_id=pk)
    return render(request, 'sale_receipt.html', {'receipt': receipt})


@login_required
@user_passes_test(can_access_sales, login_url='login')
def sales_dashboard(request):
    today = timezone.now().date()
    sales = Sale.objects.prefetch_related('receipt').order_by('-date')
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


@login_required
@user_passes_test(can_access_stock, login_url='login')
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


# ─────────────────────────────────────────────
# REPORTS VIEWS
# Access: admin only
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_reports, login_url='login')
def reports(request):
    start_date_raw = request.GET.get('start_date', '').strip()
    end_date_raw = request.GET.get('end_date', '').strip()
    export_requested = request.GET.get('export') == 'full'
    errors = []
    start_date = None
    end_date = None

    if start_date_raw:
        try:
            start_date = date_type.fromisoformat(start_date_raw)
        except (ValueError, TypeError):
            errors.append('Start date must be valid.')
    if end_date_raw:
        try:
            end_date = date_type.fromisoformat(end_date_raw)
        except (ValueError, TypeError):
            errors.append('End date must be valid.')
    if start_date and end_date and start_date > end_date:
        errors.append('Start date must be earlier than or equal to end date.')

    # Export is admin-only — already enforced by the decorator, but kept for template context
    if export_requested and not is_admin(request.user):
        errors.append('Only Admin can export full reports.')

    for error in errors:
        messages.error(request, error)

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

    if not errors:
        if start_date:
            sales = sales.filter(date__gte=start_date)
            sales_receipts = sales_receipts.filter(issued_on__date__gte=start_date)
            stocks = stocks.filter(date__gte=start_date)
            suppliers = suppliers.filter(delivery_date__gte=start_date)
            supplier_payments = supplier_payments.filter(date__gte=start_date)
            customers = customers.filter(date_registered__gte=start_date)
            customer_payments = customer_payments.filter(date__gte=start_date)
            deposits = deposits.filter(date__gte=start_date)
            deposit_payments = deposit_payments.filter(date__gte=start_date)
            deposit_payment_receipts = deposit_payment_receipts.filter(payment_date__date__gte=start_date)
        if end_date:
            sales = sales.filter(date__lte=end_date)
            sales_receipts = sales_receipts.filter(issued_on__date__lte=end_date)
            stocks = stocks.filter(date__lte=end_date)
            suppliers = suppliers.filter(delivery_date__lte=end_date)
            supplier_payments = supplier_payments.filter(date__lte=end_date)
            customers = customers.filter(date_registered__lte=end_date)
            customer_payments = customer_payments.filter(date__lte=end_date)
            deposits = deposits.filter(date__lte=end_date)
            deposit_payments = deposit_payments.filter(date__lte=end_date)
            deposit_payment_receipts = deposit_payment_receipts.filter(payment_date__date__lte=end_date)

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
        'start_date': start_date_raw,
        'end_date': end_date_raw,
        'can_export_full_reports': True,  # always True here since only admin reaches this view
    }
    return render(request, 'reports.html', context)


# ─────────────────────────────────────────────
# SUPPLIER VIEWS
# Access: admin + stock_manager only
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_suppliers, login_url='login')
def supply_reports(request):
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


@login_required
@user_passes_test(can_access_suppliers, login_url='login')
def suppliers(request):
    all_suppliers = Supplier.objects.all()
    return render(request, 'supplier.html', {'suppliers': all_suppliers})


@login_required
@user_passes_test(can_access_suppliers, login_url='login')
def add_supplier(request):
    if request.method == 'POST':
        body = request.POST
        errors = []

        supplier_name = body.get('name', '').strip()
        supplier_email = body.get('email', '').strip()
        if not supplier_name:
            errors.append('Supplier name is required.')
        if supplier_email:
            try:
                validate_email(supplier_email)
            except ValidationError:
                errors.append('Supplier email address must be valid.')

        validate_product_spec(body.get('product'), body.get('specification', '').strip(), errors)

        try:
            qty = int(body.get('quantity'))
            if qty < 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            qty = None

        try:
            deposit = int(body.get('deposit', 0))
            if deposit <= 0:
                errors.append('Credit amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Credit amount must be a valid whole number.')
            deposit = None

        try:
            amount_owed = int(body.get('amount_owed') or 0)
            if bool(body.get('is_credit')) and amount_owed <= 0:
                errors.append('Credit amount owed must be greater than zero.')
            elif amount_owed < 0:
                errors.append('Amount owed cannot be negative.')
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
            name=supplier_name,
            phone=body.get('phone'),
            email=supplier_email or None,
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


@login_required
@user_passes_test(can_access_suppliers, login_url='login')
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        body = request.POST
        errors = []

        supplier_name = body.get('name', '').strip()
        supplier_email = body.get('email', '').strip()
        if not supplier_name:
            errors.append('Supplier name is required.')
        if supplier_email:
            try:
                validate_email(supplier_email)
            except ValidationError:
                errors.append('Supplier email address must be valid.')

        validate_product_spec(body.get('product'), body.get('specification', '').strip(), errors)

        try:
            qty = int(body.get('quantity'))
            if qty < 0:
                errors.append('Quantity must be a positive number.')
        except (ValueError, TypeError):
            errors.append('Quantity must be a valid whole number.')
            qty = None

        try:
            deposit = int(body.get('deposit', 0))
            if deposit <= 0:
                errors.append('Credit amount must be greater than zero.')
        except (ValueError, TypeError):
            errors.append('Credit amount must be a valid whole number.')
            deposit = None

        try:
            amount_owed = int(body.get('amount_owed') or 0)
            if bool(body.get('is_credit')) and amount_owed <= 0:
                errors.append('Credit amount owed must be greater than zero.')
            elif amount_owed < 0:
                errors.append('Amount owed cannot be negative.')
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
        supplier.name = supplier_name
        supplier.phone = body.get('phone')
        supplier.email = supplier_email or None
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


@login_required
@user_passes_test(can_access_suppliers, login_url='login')
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        return redirect('suppliers')
    return render(request, 'supplier_delete.html', {'supplier': supplier})


@login_required
@user_passes_test(can_access_suppliers, login_url='login')
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
            new_paid = supplier.total_paid
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


@login_required
@user_passes_test(can_access_suppliers, login_url='login')
def supplier_receipt(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    receipt, created = SupplierReceipt.objects.get_or_create(supplier=supplier)
    payments = supplier.payments.order_by('-date')
    return render(request, 'supplier_receipt.html', {
        'supplier': supplier,
        'receipt': receipt,
        'payments': payments,
    })


# ─────────────────────────────────────────────
# CUSTOMER VIEWS
# Access: all three roles
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_any, login_url='login')
def customers(request):
    all_customers = Customer.objects.all().order_by('-date_registered')
    return render(request, 'customer.html', {'customers': all_customers})


@login_required
@user_passes_test(can_access_any, login_url='login')
def add_customer(request):
    if request.method == 'POST':
        body = request.POST
        errors = []

        name = body.get('name', '').strip()
        phone = body.get('phone', '').strip()
        email = body.get('email', '').strip()
        nin = body.get('NIN', '').strip().upper()
        address_distance = None

        try:
            address_distance = int(body.get('address_distance')) if body.get('address_distance') else None
            if address_distance is not None and address_distance < 0:
                errors.append('Address distance must be zero or greater.')
        except (ValueError, TypeError):
            errors.append('Address distance must be a valid integer.')

        validate_customer_identity(name, phone, nin, email, errors, require_nin=True)

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'customer_reg.html', {'data': body})

        Customer.objects.create(
            name=name,
            phone=phone,
            email=email or None,
            address=body.get('address') or None,
            address_distance=address_distance,
            NIN=nin,
            bought_on_credit=bool(body.get('bought_on_credit')),
        )
        messages.success(request, 'Customer registered successfully.')
        return redirect('customer')
    return render(request, 'customer_reg.html')


@login_required
@user_passes_test(can_access_any, login_url='login')
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        body = request.POST
        errors = []
        name = body.get('name', '').strip()
        phone = body.get('phone', '').strip()
        email = body.get('email', '').strip()
        nin = body.get('NIN', '').strip().upper()

        validate_customer_identity(name, phone, nin, email, errors, customer_id=customer.pk, require_nin=True)

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
        customer.email = email or None
        customer.address = body.get('address') or None
        customer.address_distance = address_distance
        customer.NIN = nin
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


@login_required
@user_passes_test(can_access_any, login_url='login')
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully.')
        return redirect('customer')
    return render(request, 'customer_delete.html', {'customer': customer})


@login_required
@user_passes_test(can_access_any, login_url='login')
def customer_view(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.order_by('-date')
    return render(request, 'customer_tracker.html', {
        'customer': customer,
        'sales': sales,
    })


# ─────────────────────────────────────────────
# DEPOSIT SCHEME VIEWS
# Access: all three roles
# ─────────────────────────────────────────────

@login_required
@user_passes_test(can_access_any, login_url='login')
def deposits(request):
    all_deposits = Deposit.objects.select_related('customer').order_by('-date')
    total_debtors = all_deposits.count()
    total_received = all_deposits.aggregate(total=Sum('deposit_amount'))['total'] or 0
    return render(request, 'deposit.html', {
        'deposits': all_deposits,
        'total_debtors': total_debtors,
        'total_received': total_received,
    })


@login_required
@user_passes_test(can_access_any, login_url='login')
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
        contact = body.get('contact', '').strip()
        nin = body.get('NIN', '').strip()
        selected_customer = None

        if not customer_field and not customer_manual:
            errors.append('Please select or enter a customer.')
        elif customer_field:
            try:
                selected_customer = Customer.objects.get(pk=customer_field)
            except Customer.DoesNotExist:
                errors.append('Selected customer was not found.')

        if body.get('item') not in dict(SCHEME_ITEMS):
            errors.append('Only cement, iron sheets, and iron bars are eligible for the deposit scheme.')

        customer_name = customer_manual or (selected_customer.name if selected_customer else '')
        validate_customer_identity(
            customer_name,
            contact,
            nin,
            selected_customer.email if selected_customer else '',
            errors,
            customer_id=selected_customer.pk if selected_customer else None,
            require_nin=True,
        )

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'deposit_reg.html', {'customers': customers, 'scheme_items': SCHEME_ITEMS, 'data': body})

        if customer_manual:
            customer_obj, created = Customer.objects.get_or_create(
                NIN=nin,
                defaults={'name': customer_manual, 'phone': contact},
            )
            if not created:
                customer_obj.name = customer_manual
                customer_obj.phone = contact
                customer_obj.save(update_fields=['name', 'phone'])
        else:
            customer_obj = selected_customer
            if customer_obj.NIN != nin or customer_obj.phone != contact:
                customer_obj.NIN = nin
                customer_obj.phone = contact
                customer_obj.save(update_fields=['NIN', 'phone'])

        Deposit.objects.create(
            customer=customer_obj,
            item=body.get('item'),
            NIN=nin,
            contact=contact,
            deposit_amount=deposit_amount,
            expiry_date=expiry_date,
            total_balance=total_balance,
        )
        messages.success(request, 'Deposit recorded successfully.')
        return redirect('deposits')
    return render(request, 'deposit_reg.html', {'customers': customers, 'scheme_items': SCHEME_ITEMS})


@login_required
@user_passes_test(can_access_any, login_url='login')
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

        if body.get('item') not in dict(SCHEME_ITEMS):
            errors.append('Only cement, iron sheets, and iron bars are eligible for the deposit scheme.')

        customer_obj = None
        if body.get('customer'):
            customer_obj = get_object_or_404(Customer, pk=body.get('customer'))

        contact = body.get('contact', '').strip()
        nin = body.get('NIN', '').strip()
        validate_customer_identity(
            customer_obj.name if customer_obj else '',
            contact,
            nin,
            customer_obj.email if customer_obj else '',
            errors,
            customer_id=customer_obj.pk if customer_obj else None,
            require_nin=True,
        )

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'deposit_edit.html', {'deposit': deposit, 'customers': customers, 'scheme_items': SCHEME_ITEMS})

        if customer_obj.NIN != nin or customer_obj.phone != contact:
            customer_obj.NIN = nin
            customer_obj.phone = contact
            customer_obj.save(update_fields=['NIN', 'phone'])

        deposit.customer = customer_obj
        deposit.item = body.get('item')
        deposit.NIN = nin
        deposit.contact = contact
        deposit.deposit_amount = deposit_amount
        deposit.expiry_date = expiry_date
        deposit.total_balance = total_balance
        deposit.save()
        messages.success(request, 'Deposit updated successfully.')
        return redirect('deposits')
    return render(request, 'deposit_edit.html', {'deposit': deposit, 'customers': customers, 'scheme_items': SCHEME_ITEMS})


@login_required
@user_passes_test(can_access_any, login_url='login')
def deposit_delete(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    if request.method == 'POST':
        deposit.delete()
        messages.success(request, 'Deposit deleted.')
        return redirect('deposits')
    return render(request, 'deposit_delete.html', {'deposit': deposit})


@login_required
@user_passes_test(can_access_any, login_url='login')
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
            balance_before = remaining
            deposit_payment = DepositPayment.objects.create(
                deposit=deposit,
                amount=amount,
                note=request.POST.get('note', '').strip(),
            )
            balance_after = max(balance_before - amount, 0)
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


@login_required
@user_passes_test(can_access_any, login_url='login')
def deposit_receipts(request):
    receipts = Deposit.objects.select_related('customer').order_by('-date')
    return render(request, 'deposit_receipts.html', {'receipts': receipts})


@login_required
@user_passes_test(can_access_any, login_url='login')
def deposit_receipt(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    return render(request, 'deposit_reciept.html', {'deposit': deposit})


@login_required
@user_passes_test(can_access_any, login_url='login')
def payment_receipt(request, receipt_id):
    receipt = get_object_or_404(DepositPaymentReceipt, pk=receipt_id)
    return render(request, 'payment_receipt.html', {'receipt': receipt})


@login_required
@user_passes_test(can_access_any, login_url='login')
def payment_receipts_list(request):
    receipts = DepositPaymentReceipt.objects.select_related('deposit_payment__deposit__customer').order_by('-payment_date')

    customer_filter = request.GET.get('customer', '').strip()
    if customer_filter:
        receipts = receipts.filter(customer_name__icontains=customer_filter)

    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    if from_date:
        from datetime import datetime
        try:
            receipts = receipts.filter(payment_date__gte=datetime.fromisoformat(from_date))
        except (ValueError, TypeError):
            pass

    if to_date:
        from datetime import datetime
        try:
            receipts = receipts.filter(payment_date__lte=datetime.fromisoformat(to_date))
        except (ValueError, TypeError):
            pass

    context = {
        'receipts': receipts,
        'customer_filter': customer_filter,
        'from_date': from_date,
        'to_date': to_date,
        'total_amount_paid': sum(r.amount_paid for r in receipts),
    }
    return render(request, 'payment_receipts_list.html', context)