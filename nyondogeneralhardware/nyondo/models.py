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
    product_sold = models.CharField(max_length=30, choices=PRODUCT_CHOICES)
    specification = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField(auto_now_add=True)  # set automatically on creation
    quantity_sold = models.IntegerField()
    payment_method = models.TextField(max_length=50)

    def __str__(self):
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


class Deposit(models.Model):
    receipt_number = models.CharField(max_length=50)
    date = models.DateField(auto_now_add=True)
    customer_name = models.CharField(max_length=200)
    NIN = models.TextField(max_length=50, blank=True, null=True)
    contact = models.IntegerField()
    signature = models.CharField(max_length=100, blank=True, null=True)
    deposit_amount = models.IntegerField()
    expiry_date = models.DateField()
    total_balance = models.IntegerField()



class Credit(models.Model):
    receipt_number = models.CharField()




class Signup(models.Model):
    username = models.CharField(max_length=50)
    email = models.EmailField()
    password = models.TextField(max_length=12)


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
