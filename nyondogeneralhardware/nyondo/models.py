from django.db import models

# Create your models here.

class Stock(models.Model):
    product_name = models.CharField(max_length=25)
    product_code = models.PositiveIntegerField(unique=True)
    category = models.CharField(
    max_length=25, 
    choices=[('electrical', 'Electrical'), ('plumbing', 'Plumbing'), ('building', 'Building')]
)
    quantity = models.PositiveIntegerField()
    buying_price = models.PositiveBigIntegerField()
    selling_price = models.PositiveBigIntegerField()


class Sale(models.Model):
    product_sold = models.CharField(max_length=30)
    date = models.DateField(auto_now_add=True)
    quantity_sold = models.PositiveIntegerField()
    receipt_number = models.PositiveBigIntegerField(unique=True)
    payment_method = models.TextField(max_length=50)
