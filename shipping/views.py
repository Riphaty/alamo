from django.shortcuts import render,get_object_or_404,redirect
from shipping.models import *
from shipping.forms import *
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

# Create your views here.
# shipments
@login_required
def shipment(request):
    shipments = list(Shipment.objects.all())
    status_order = {
        'Ordered': 0,
        'Shipped': 1,
        'Delivered': 2,
    }
    shipments.sort(key=lambda s: status_order.get(s.status, 99))
    shipment= Shipment.objects.filter(payment_date__isnull=False,delivery_date__isnull=True)
    total_capital=sum(ship.price or 0 for ship in shipment)
    total_shipping_cost=sum(ship.shipping_price_tzs or 0 for ship in shipment)
    context={
        'shipment':shipments,
        'total_capital':total_capital,
        'total_shipping_cost':total_shipping_cost,
        }
    return render(request, 'shipping/shipment.html',context)

@login_required
def add_shipment(request):
    form=ShipmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('shipping_home')
    context={
        'form':form,
        }
    return render (request, 'shipping/add_shipment.html',context)

@login_required
def edit_shipment(request,id):
    shipment=get_object_or_404(Shipment,id=id)
    form=ShipmentForm(request.POST or None, instance=shipment)
    if form.is_valid():
        form.save()
        return redirect ('shipping_home')
    context={'edit_shipment':form}
    return render (request, 'shipping/edit_shipment.html',context)

@login_required
def delete_shipment(request,id):
    shipment=get_object_or_404(Shipment,id=id)
    if request.method == 'POST':
        shipment.delete()
        return redirect ('shipping_home')
    context={'delete_shipment':shipment}
    return render (request, 'shipping/delete_shipment.html',context)

# products
@login_required
def registered_products_list(request):
    products=Product.objects.all().order_by('name')
    form=ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect ('products')
    context={
        'products':products,
        'form':form,
        }
    return render (request, 'shipping/products.html',context)

@login_required
def edit_registered_product(request,id):
    products=get_object_or_404(Product,id=id)
    form=ProductForm(request.POST or None, instance=products)
    if form.is_valid():
        form.save()
        return redirect('products')
    context={'form':form}
    return render (request, 'shipping/edit_products.html',context)

@login_required
def delete_registered_product(request,id):
    product=get_object_or_404(Product,id=id)
    if request.method=='POST':
        product.delete()
        return redirect('products')
    context={'product':product}
    return render (request, 'shipping/delete_products.html',context)