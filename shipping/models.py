from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.
class Product(models.Model):
    name=models.CharField(max_length=200)
    def __str__(self):
        return self.name
    
class Shipment(models.Model):
    product=models.ForeignKey(Product,on_delete=models.DO_NOTHING)
    quantity=models.IntegerField(validators=[MinValueValidator(1)])
    price=models.DecimalField(max_digits=10, decimal_places=2,validators=[MinValueValidator(0)])
    payment_date=models.DateField()
    cbm=models.DecimalField(max_digits=5,decimal_places=4, null=True, blank= True)
    shipped_date=models.DateField(null=True, blank=True)
    delivery_date=models.DateField(null=True, blank=True)
    shipping_fee_per_Cbm=models.DecimalField(max_digits=10, decimal_places=2,default=450,validators=[MinValueValidator(0)])
    exchange_rate=models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True, validators=[MinValueValidator(0)])
    usafiri_ndani=models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True, validators=[MinValueValidator(0)])
    def __str__(self):
        return self.product.name
    @property
    def shipping_price_usd(self):
        if self.cbm is not None:
            return self.shipping_fee_per_Cbm*self.cbm
        return None

    @property
    def shipping_price_tzs(self):
        if self.shipping_price_usd is not None:
            return (self.exchange_rate or 0) * self.shipping_price_usd
        return None

    @property
    def total_cogs(self):
        if self.shipping_price_tzs is not None:
            return self.price + self.shipping_price_tzs + (self.usafiri_ndani or 0)
        return None
    
    @property
    def unit_cogs(self):
        if self.total_cogs is not None:
            return self.total_cogs/self.quantity
        return None

    @property
    def time_used(self):
        if self.delivery_date and self.shipped_date: 
            return (self.delivery_date-self.shipped_date).days
        return None
    
    @property
    def status(self):
        if self.payment_date and not self.shipped_date:
            return 'Ordered'
        elif self.shipped_date and not self.delivery_date:
            return 'Shipped'
        elif self.delivery_date:
            return 'Delivered'
        return 'Unknown'
    