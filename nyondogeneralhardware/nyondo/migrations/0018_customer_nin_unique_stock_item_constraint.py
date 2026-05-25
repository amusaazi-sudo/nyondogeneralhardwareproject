from django.db import migrations, models


def normalize_blank_nins(apps, schema_editor):
    Customer = apps.get_model('nyondo', 'Customer')
    Customer.objects.filter(NIN='').update(NIN=None)


class Migration(migrations.Migration):

    dependencies = [
        ('nyondo', '0017_depositpaymentreceipt'),
    ]

    operations = [
        migrations.RunPython(normalize_blank_nins, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='customer',
            name='NIN',
            field=models.CharField(blank=True, max_length=13, null=True, unique=True),
        ),
        migrations.AddConstraint(
            model_name='stock',
            constraint=models.UniqueConstraint(fields=('product_name', 'specification'), name='unique_stock_item_specification'),
        ),
    ]
