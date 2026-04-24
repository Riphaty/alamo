from django.forms import ModelForm
from .models import *   
from django import forms

class SaleForm(ModelForm):
    class Meta:
        model=Sale
        exclude=['status']
        widgets={'date':forms.DateInput(attrs={'type':'date'})}    

class StockForm(ModelForm):
    class Meta:
        model=Stock
        fields='__all__'
