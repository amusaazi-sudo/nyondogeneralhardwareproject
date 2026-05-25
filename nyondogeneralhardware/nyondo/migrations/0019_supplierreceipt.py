from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nyondo', '0018_customer_nin_unique_stock_item_constraint'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_number', models.CharField(editable=False, max_length=30, unique=True)),
                ('issued_on', models.DateTimeField(auto_now_add=True)),
                ('supplier', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='receipt', to='nyondo.supplier')),
            ],
        ),
    ]
