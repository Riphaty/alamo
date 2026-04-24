from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render,get_object_or_404,redirect
from django.db.models import *
from inventory.models import *
from inventory.forms import *
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils import timezone
from shipping.models import Shipment

# Create your views here.
# home
@login_required
def home(request):
    sales=Sale.objects.all()
    stocks=Stock.objects.all()
    for stock in stocks:
        stock.stock_value=(stock.cogs*stock.quantity)
    for sale in sales:
        sale.faida=sale.mapato-(sale.bidhaa.cogs*sale.idadi)    
    total_mapato=sum(sale.mapato for sale in sales)
    totals=Sale.objects.aggregate(total_matumizi=Sum('matumizi'), total_units=Sum('idadi'))
    total_matumizi=totals['total_matumizi'] or 0
    total_units=totals['total_units'] or 0
    total_faida=sum(sale.faida for sale in sales)
    total_stocks=sum(stock.stock_value for stock in stocks)

    context={
            'total_units':total_units,
            'total_matumizi':total_matumizi,
            'total_stocks':total_stocks or 0,
            'total_mapato':total_mapato or 0,
            'total_faida':total_faida or 0,                                               
            }
    return render(request, 'inventory/nav.html',context) 

# sales views
@login_required
def sales(request):
    now = timezone.now()
    month = now.month
    year = now.year

    sales = Sale.objects.filter(
        date__year=year,
        date__month=month
    ).order_by('-date', '-id')

    stocks = Stock.objects.all()

    # Calculate stock value
    for stock in stocks:
        stock.stock_value = (stock.cogs or 0) * (stock.quantity or 0)

    # Calculate profit per sale
    for sale in sales:
        cost = (sale.bidhaa.cogs or 0) * (sale.idadi or 0)
        sale.faida = (sale.mapato or 0) - cost

    # Totals
    totals = sales.aggregate(
        total_matumizi=Sum('matumizi'),
        total_units=Sum('idadi'),
    )

    total_matumizi = totals['total_matumizi'] or 0
    total_units = totals['total_units'] or 0

    total_mapato = sales.aggregate(total=(Sum(F('makusanyo')-F('matumizi'))))['total'] or 0
    total_faida = sum((sale.faida or 0) for sale in sales)
    total_stocks = sum((stock.stock_value or 0) for stock in stocks)

    context = {
        'sales': sales,
        'month': month,
        'year': year,
        'total_units': total_units,
        'total_matumizi': total_matumizi,
        'total_mapato': total_mapato,
        'total_faida': total_faida,
        'total_stocks': total_stocks,
    }

    return render(request, 'inventory/sales.html', context)

@login_required
def add_sales(request):
    form=SaleForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('sales')
    context={'add_sales':form}
    return render(request, 'inventory/add_sales.html',context)

@login_required
def edit_sales(request,id):
    sales=get_object_or_404(Sale,id=id)
    form=SaleForm(request.POST or None, instance=sales)
    if form.is_valid():
        form.save()
        return redirect('sales')
    context={'edit_sales':form}
    return render(request, 'inventory/edit_sales.html',context)

@login_required
def delete_sales(request,id):
    sales=get_object_or_404(Sale,id=id)
    if request.method == 'POST':
        sales.delete()
        return redirect('sales')
    context={'delete_sales':sales}
    return render(request, 'inventory/delete_sales.html',context)

@login_required
def sales_history(request):

    # -----------------------------
    # 1. SALES BASE QUERYSET
    # -----------------------------
    sales = Sale.objects.all()
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)

        if start and end:
            sales = sales.filter(date__gte=start, date__lte=end)

    # -----------------------------
    # 2. MONTH FILTER
    # -----------------------------
    now = timezone.now()
    month = now.month
    year = now.year

    sales = sales.filter(
        date__year=year,
        date__month=month
    ).order_by('-date', '-id')

    # -----------------------------
    # 3. STOCKS
    # -----------------------------
    stocks = Stock.objects.all()

    for stock in stocks:
        stock.stock_value = (stock.cogs or 0) * (stock.quantity or 0)

    # -----------------------------
    # 4. PROFIT CALCULATION (UPDATED RULE)
    # -----------------------------
    for sale in sales:
        cost = (sale.bidhaa.cogs or 0) * (sale.idadi or 0)

        if getattr(sale, 'status', None) == 'canceled':
            sale.faida = 0
        else:
            sale.faida = (sale.mapato or 0) - cost

    # -----------------------------
    # 4. TOTAL CAPITAL
    # -----------------------------

    shipment= Shipment.objects.filter(payment_date__isnull=False,delivery_date__isnull=True)
    total_capital=sum(ship.price or 0 for ship in shipment)

    # -----------------------------
    # 5. TOTALS
    # -----------------------------
    totals = sales.aggregate(
        total_matumizi=Sum('matumizi'),
        total_units=Sum('idadi'),
    )

    total_matumizi = totals['total_matumizi'] or 0
    total_units = totals['total_units'] or 0

    total_mapato = sales.aggregate(
        total=Sum(F('makusanyo') - F('matumizi'))
    )['total'] or 0

    total_faida = sum((sale.faida or 0) for sale in sales)
    total_stocks = sum((stock.stock_value or 0) for stock in stocks)
    theCapital=total_capital+total_stocks

    # -----------------------------
    # 7. ANALYTICS (FIXED)
    # -----------------------------
    analytics = (
        Sale.objects.values('bidhaa__name')
        .annotate(
            total_sold=Sum('idadi'),
            total_faida=Sum(
                F('makusanyo') - F('matumizi')
            )
        )
        .order_by('-total_sold')
    )

    labels = [item['bidhaa__name'] for item in analytics]
    sold_data = [item['total_sold'] for item in analytics]
    faida_data = [item['total_faida'] for item in analytics]

    # -----------------------------
    # 8. CONTEXT
    # -----------------------------
    context = {
        'theCapital':theCapital,
        'sales': sales,
        'stocks': stocks,
        'month': month,
        'year': year,
        'total_units': total_units,
        'total_matumizi': total_matumizi,
        'total_mapato': total_mapato,
        'total_faida': total_faida,
        'total_stocks': total_stocks,
        'analytics': analytics,
        'labels': labels,
        'sold_data': sold_data,
        'faida_data': faida_data,
    }

    return render(request, 'inventory/sales_history.html', context)

# cancel views
@login_required
def canceled(request,id):
    sale=get_object_or_404(Sale,id=id)
    if sale.status != 'canceled':
        stock=sale.bidhaa
        stock.quantity+=sale.idadi
        stock.save()

        sale.status ='canceled'
        sale.save()
        return redirect ('pending_sales')

# Pending views
@login_required
def pending_sales(request):
    pending_sales=Sale.objects.filter(status='pending')     
    idadi_pending=pending_sales.aggregate(total=Sum('idadi'))['total'] or 0
    context={
        'pending_sales':pending_sales,
        'idadi':idadi_pending
        }
    return render(request, 'inventory/pending_sales.html',context)

@login_required
def edit_pending_sales(request,id):
    pending_sales=get_object_or_404(Sale,id=id)
    form=SaleForm(request.POST or None, instance=pending_sales)
    if form.is_valid():
        form.save()
        return redirect('pending_sales')
    context={'edit_pending_sales':form}
    return render(request, 'inventory/edit_pending_sales.html',context)

# stocks views
@login_required
def stocks(request):
    stocks = Stock.objects.all()
    for stock in stocks:
        stock.margin = stock.bei - stock.cogs
        stock.total_value = stock.cogs * stock.quantity
    total_stocks=sum(stock.total_value for stock in stocks)
    context = {
        'stocks': stocks, 
        'total_stocks': total_stocks, 
    }
    return render(request, 'inventory/stocks.html', context)

@login_required
def add_stocks(request):
    form = StockForm(request.POST or None)
    if form.is_valid():
        name = form.cleaned_data['name']
        quantity = form.cleaned_data['quantity']
        cogs = form.cleaned_data['cogs']
        bei = form.cleaned_data['bei']

        try:
            stock = Stock.objects.get(name=name)
            stock.quantity += quantity
            stock.cogs = cogs   
            stock.bei = bei
            stock.save()
        except Stock.DoesNotExist:
            form.save()
        return redirect('stocks')   
    context = {'add_stocks': form}
    return render(request, 'inventory/add_stocks.html', context)

@login_required
def edit_stocks(request,id):
    stocks=get_object_or_404(Stock,id=id)
    form=StockForm(request.POST or None, instance=stocks)
    if form.is_valid():
        form.save()
        return redirect('stocks')
    context={'edit_stocks':form}
    return render(request, 'inventory/edit_stocks.html',context)

@login_required
def delete_stocks(request,id):
    stocks=get_object_or_404(Stock,id=id)
    if request.method == 'POST':
        stocks.delete()
        return redirect('stocks')
    context={'delete_stocks':stocks}
    return render(request, 'inventory/delete_stocks.html',context)


# Dashaboard.
@login_required
def dashboard(request):
    sales=Sale.objects.all()
    stocks=Stock.objects.all()
    for stock in stocks:
        stock.stock_value=(stock.cogs*stock.quantity)
    for sale in sales:
        sale.faida=sale.mapato-(sale.bidhaa.cogs*sale.idadi)   
    total_mapato=sum(sale.mapato for sale in sales)
    totals=Sale.objects.aggregate(total_matumizi=Sum('matumizi'),total_units=Sum('idadi'))
    total_matumizi=totals['total_matumizi'] or 0
    total_units=totals['total_units'] or 0
    total_faida=sum(sale.faida for sale in sales)
    total_stocks=sum(stock.stock_value for stock in stocks)
    
    context={'total_matumizi':total_matumizi,
             'total_stocks':total_stocks or 0,
             'total_mapato':total_mapato or 0,
             'total_faida':total_faida or 0,                                               
             'total_units':total_units
             }
    return render(request, 'inventory/dashboard.html',context)

@login_required
def analytics(request):
    # Pata sales zote
    sales = Sale.objects.all()

    # Optional: date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)
        if start and end:
            sales = sales.filter(date__gte=start, date__lte=end)

    # Puuza canceled orders
    sales = sales.exclude(status='canceled')

    # Annotate totals kwa kila bidhaa
    analytics = sales.values('bidhaa__name').annotate(
        total_sold=Sum('idadi'),
        total_faida=Sum(
            ExpressionWrapper(
                (F('makusanyo') - F('matumizi')) - (F('bidhaa__cogs') * F('idadi')),
                output_field=FloatField()
            )
        )
    ).order_by('-total_faida')  # faida kubwa kwenda ndogo

    # Prepare data for chart
    labels = [item['bidhaa__name'] for item in analytics]
    faida_data = [item['total_faida'] for item in analytics]
    sold_data = [item['total_sold'] for item in analytics]

    context = {
        'analytics': analytics,
        'labels': labels,
        'sold_data': sold_data,
        'faida_data': faida_data,
    }

    return render(request, 'inventory/analytics.html', context)