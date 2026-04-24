from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator

# Create your models here.

class Stock(models.Model):
    name=models.CharField(max_length=100)
    cogs=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)])
    bei=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)])
    quantity=models.IntegerField(validators=[MinValueValidator(0)])
    def __str__(self):
        return self.name

class Sale(models.Model):
    CONDTION_CHOICES=[('ndani', 'Ndani'),('mkoa', 'Mkoa') ]
    STATUS_CHOICES=[('paid','Paid'), ('pending', 'Pending'), ('canceled',('Canceled'))]

    date=models.DateField()
    bidhaa=models.ForeignKey(Stock,on_delete=models.PROTECT)
    mahali=models.CharField(max_length=100)
    aina=models.CharField(max_length=100,choices=CONDTION_CHOICES)
    idadi=models.IntegerField(validators=[MinValueValidator(1)],default=0)
    makusanyo=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)],default=0)
    matumizi=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)],default=0)
    status=models.CharField(max_length=10,choices=STATUS_CHOICES)
    created_at=models.DateTimeField(auto_now_add=True)

    @property
    def mapato(self):
        return self.makusanyo-self.matumizi

    def faida(self):
        if self.status == 'canceled':
            return 0
        else:
            return self.mapato-(self.bidhaa.cogs*self.idadi)
        
    def save(self, *args, **kwargs):
        stock = self.bidhaa
        if self.status!='canceled':
            if self.makusanyo ==0:
                new_status='pending'
            else:
                new_status='paid'
        else:
            new_status='canceled'

        if self.status=='canceled':
            self.faida=0

        # Sale mpya
        if not self.pk:
            self.status = new_status
            if self.idadi > stock.quantity:
                raise ValidationError("Stock haitoshi.")
            stock.quantity -= self.idadi
            stock.save()

        else:
            old_sale = Sale.objects.get(pk=self.pk)
            old_status = old_sale.status
            old_idadi = old_sale.idadi

            # Pending → paid
            if old_status == 'pending' and new_status == 'paid':
                # Stock haipungui tena, imepunguliwa wakati sale ilikuwepo
                self.status = 'paid'

            # Paid → paid
            elif old_status == 'paid' and new_status == 'paid':
                difference = self.idadi - old_idadi
                if difference > 0 and difference > stock.quantity:
                    raise ValidationError("Stock haitoshi.")
                stock.quantity -= difference
                stock.save()

            # Pending / Paid → pending
            # Stock haibadiliki, status inabadilika
            else:
                self.status = new_status

        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.date)    
            

    




    
    