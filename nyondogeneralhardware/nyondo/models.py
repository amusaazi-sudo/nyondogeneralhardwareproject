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

    def __str__(self):
        return self.product_name


class Sale(models.Model):
    product_sold = models.CharField(max_length=30)
    date = models.DateField(auto_now_add=True)
    quantity_sold = models.PositiveIntegerField()
    receipt_number = models.PositiveBigIntegerField(unique=True)
    payment_method = models.TextField(max_length=50)
    # def __str__(self):
    #     return self.product_sold


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
