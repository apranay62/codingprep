from django.db import models


class Invoice(models.Model):
    customer = models.CharField(max_length=255)
    date = models.DateField(auto_now=True)
    total_quantity = models.IntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'odo_invoice'


class Transaction(models.Model):
    product = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    invoice = models.ForeignKey(Invoice, related_name='transactions', on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = 'odo_transaction'
