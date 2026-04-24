from django.forms import ModelForm
from shipping.models import *
from django import forms

class ProductForm(ModelForm):
    class Meta:
        model=Product
        fields='__all__'

class ShipmentForm(ModelForm):
    class Meta:
        model=Shipment
        fields='__all__'
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'shipped_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
