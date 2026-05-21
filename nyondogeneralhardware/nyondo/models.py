from django.db import models

# Create your models here.

PRODUCT_CHOICES = [
    ('cement', 'Cement'),
    ('iron_bars', 'Iron Bars'),
    ('nails', 'Nails'),
    ('wheelbarrows', 'Wheelbarrows'),
    ('wire_mesh', 'Wire Mesh'),
    ('barbed_wire', 'Barbed Wire'),
    ('iron_sheets', 'Iron Sheets'),
]

CEMENT_SPECS = [('cem_iin', 'CEM IIN'), ('cem_iiin', 'CEM IIIN')]
IRON_BAR_SPECS = [('10mm', '10mm'), ('12mm', '12mm'), ('16mm', '16mm')]
NAIL_SPECS = [('1inch', '1 inch'), ('3inch', '3 inch'), ('4inch', '4 inch'), ('5inch', '5 inch'), ('roofing_5kg', 'Roofing Nails 5kg')]
BARBED_WIRE_SPECS = [('high_tensile', 'High Tensile'), ('low_tensile', 'Low Tensile')]
IRON_SHEET_GAUGES = [('gauge_28', 'Gauge 28'), ('gauge_30', 'Gauge 30'), ('gauge_32', 'Gauge 32')]
IRON_SHEET_COLORS = [('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'), ('brown', 'Brown'), ('grey', 'Grey')]


class Stock(models.Model):
    product_name = models.CharField(max_length=25, choices=PRODUCT_CHOICES)
    specification = models.CharField(max_length=50, blank=True, null=True)
    product_code = models.IntegerField(unique=True)
    category = models.CharField(
    max_length=25,
    choices=[('electrical', 'Electrical'), ('plumbing', 'Plumbing'), ('building', 'Building')]
)
    quantity = models.IntegerField()
    buying_price = models.IntegerField()
    selling_price = models.IntegerField()
    date = models.DateField(default='2025-01-01')

    def __str__(self):
        return self.product_name


# Stores each sale transaction
class Sale(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, blank=True, null=True, related_name='sales')
    product_sold = models.CharField(max_length=30, choices=PRODUCT_CHOICES)
    specification = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField(auto_now_add=True)  # set automatically on creation
    quantity_sold = models.IntegerField()
    payment_method = models.TextField(max_length=50)
    delivery = models.BooleanField(default=False)
    transport_cost = models.PositiveIntegerField(default=30000)

    TRANSPORT_FREE_THRESHOLD = 500000
    TRANSPORT_CHARGE = 30000

    @property
    def unit_price(self):
        stock = Stock.objects.filter(
            product_name=self.product_sold,
            specification=self.specification or None
        ).first()
        return stock.selling_price if stock else 0

    @property
    def sale_total(self):
        return (self.quantity_sold or 0) * self.unit_price

    @property
    def transport_status(self):
        if not self.delivery:
            return 'Not requested'
        return 'Free' if self.transport_cost == 0 else 'Charged'

    @property
    def transport_display(self):
        if not self.delivery:
            return '—'
        return 'Free' if self.transport_cost == 0 else f'UGX {self.transport_cost}'

    def calculate_transport_cost(self):
        if self.sale_total >= self.TRANSPORT_FREE_THRESHOLD and self.customer and self.customer.address_distance is not None and self.customer.address_distance <= 10:
            return 0
        return self.TRANSPORT_CHARGE

    def save(self, *args, **kwargs):
        # Recalculate transport cost whenever the sale is saved.
        if not self.delivery:
            self.transport_cost = 0
        elif self.customer_id is not None:
            self.transport_cost = self.calculate_transport_cost()
        super().save(*args, **kwargs)

    @property
    def receipt_number(self):
        return self.receipt.receipt_number if hasattr(self, 'receipt') else '—'

    def __str__(self):
        if self.customer:
            return f"{self.product_sold} ({self.customer.name})"
        return self.product_sold


# Auto-created when a Sale is saved — no manual form needed
class Receipt(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name='receipt')  # one receipt per sale
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)  # set in save(), not by user
    issued_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Build receipt number from sale pk e.g. REC-0001
        if not self.receipt_number:
            self.receipt_number = f'REC-{self.sale.pk:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    address_distance = models.PositiveIntegerField(blank=True, null=True, help_text='Distance from store in km')
    NIN = models.CharField(max_length=50, blank=True, null=True)
    date_registered = models.DateField(auto_now_add=True)
    bought_on_credit = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @property
    def total_debt(self):
        deposits = self.deposit_set.all()
        return sum(d.total_due for d in deposits)

    @property
    def total_paid(self):
        deposit_paid = sum(d.amount_paid for d in self.deposit_set.all())
        payment_total = sum(p.amount for p in self.payments.all())
        return deposit_paid + payment_total

    @property
    def amount_remaining(self):
        owed = sum(d.amount_remaining for d in self.deposit_set.all())
        paid_against_balance = sum(p.amount for p in self.payments.all())
        return max(owed - paid_against_balance, 0)

    @property
    def payment_percent(self):
        if self.total_debt == 0:
            return 100
        return min(int((self.total_paid / self.total_debt) * 100), 100)

    @property
    def payment_status(self):
        if self.total_debt == 0:
            return 'No Debt'
        if self.amount_remaining == 0:
            return 'Paid'
        if self.total_paid > 0:
            return 'Partial'
        return 'Pending'


SCHEME_ITEMS = [
    ('cement', 'Cement'),
    ('iron_sheets', 'Iron Sheets'),
    ('iron_bars', 'Iron Bars'),
]


class Deposit(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, )
    item = models.CharField(max_length=20, choices=SCHEME_ITEMS)
    receipt_number = models.CharField(max_length=50, unique=True, editable=False)
    date = models.DateField(auto_now_add=True)
    NIN = models.CharField(max_length=50, blank=True, null=True)
    contact = models.CharField(max_length=20)
    deposit_amount = models.PositiveIntegerField()
    expiry_date = models.DateField()
    total_balance = models.PositiveIntegerField()

    @property
    def total_due(self):
        return self.deposit_amount + self.total_balance

    @property
    def amount_paid(self):
        return self.deposit_amount + sum(p.amount for p in self.payments.all())

    @property
    def amount_remaining(self):
        return max(self.total_balance - sum(p.amount for p in self.payments.all()), 0)

    @property
    def progress_percent(self):
        if self.total_due == 0:
            return 100
        return min(int((self.amount_paid / self.total_due) * 100), 100)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            super().save(*args, **kwargs)
            self.receipt_number = f'DEP-{self.pk:05d}'
            Deposit.objects.filter(pk=self.pk).update(receipt_number=self.receipt_number)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class CustomerPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.customer} - {self.amount}"


class DepositPayment(models.Model):
    deposit = models.ForeignKey(Deposit, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.deposit.receipt_number} - {self.amount}"


class DepositPaymentReceipt(models.Model):
    """
    Temporary receipt issued to customer when they make an installment payment.
    Tracks all payment transaction details and customer credentials for record keeping.
    """
    deposit_payment = models.OneToOneField(DepositPayment, on_delete=models.CASCADE, related_name='receipt')
    payment_receipt_number = models.CharField(max_length=30, unique=True, editable=False)
    
    # Customer credentials snapshot at time of payment
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    customer_nin = models.CharField(max_length=50, blank=True, null=True)
    customer_address = models.CharField(max_length=200, blank=True, null=True)
    
    # Deposit details
    deposit_receipt_number = models.CharField(max_length=50)
    item_name = models.CharField(max_length=50)
    
    # Payment details
    amount_paid = models.PositiveIntegerField()
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=100, default='Cash')
    
    # Running balance tracking
    balance_before_payment = models.PositiveIntegerField()
    balance_after_payment = models.PositiveIntegerField()
    total_deposit_amount = models.PositiveIntegerField()
    total_balance_owed = models.PositiveIntegerField()
    
    # Additional info
    note = models.CharField(max_length=200, blank=True)
    issued_by = models.CharField(max_length=100, default='System')
    
    def save(self, *args, **kwargs):
        if not self.payment_receipt_number:
            super().save(*args, **kwargs)
            self.payment_receipt_number = f'PAY-REC-{self.pk:06d}'
            DepositPaymentReceipt.objects.filter(pk=self.pk).update(payment_receipt_number=self.payment_receipt_number)
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.payment_receipt_number} - {self.customer_name}"


class Credit(models.Model):
    receipt_number = models.CharField()


class Signup(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    password = models.TextField(max_length=12)

    def __str__(self):
        return self.username


class Supplier(models.Model):
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Partial', 'Partial'), ('Paid', 'Paid')]

    supplier_company = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    product = models.CharField(max_length=25, choices=PRODUCT_CHOICES)
    specification = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.IntegerField()
    deposit = models.PositiveIntegerField(default=0)
    selling_price = models.PositiveIntegerField(blank=True, null=True)
    delivery_date = models.DateField()
    is_credit = models.BooleanField(default=False)
    amount_owed = models.PositiveIntegerField(default=0)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='Pending')
    due_date = models.DateField(blank=True, null=True)

    @property
    def total_cost(self):
        return self.deposit * self.quantity

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def amount_remaining(self):
        return max(self.total_cost - self.total_paid, 0)

    @property
    def amount_remaining(self):
        return max(self.total_cost - self.total_paid, 0)

    @property
    def payment_percent(self):
        if self.total_cost == 0:
            return 100
        return min(int((self.total_paid / self.total_cost) * 100), 100)

    def get_specification_display(self):
        all_specs = (
            CEMENT_SPECS + IRON_BAR_SPECS + NAIL_SPECS +
            BARBED_WIRE_SPECS + IRON_SHEET_GAUGES + IRON_SHEET_COLORS
        )
        return dict(all_specs).get(self.specification, self.specification)

    def __str__(self):
        return f"{self.supplier_company} - {self.product}"


class SupplierPayment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='payments')
    amount = models.PositiveIntegerField()
    date = models.DateField(auto_now_add=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.supplier} - {self.amount}"
