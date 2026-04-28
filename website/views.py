from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from website.models import *
from django.core.mail import send_mail
from datetime import datetime, date
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from decimal import Decimal
import cloudinary.uploader
from django.db import transaction

# Create your views here.
#Admin Panel Ziko Hapa
#Admin-Categories
@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        thumbnail = request.FILES.get('thumbnail')
        description = request.POST.get('description')
        sort_category = int(request.POST.get('sort_category'))

        Category.objects.create(
            name=name,
            thumbnail=thumbnail,
            description=description,
            sort_category=sort_category
        )

        return redirect('admin_panel')

    return render(request, 'website/add_category.html')

@login_required
def edit_category(request, category_id):
    category = Category.objects.get(id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.sort_category = int(request.POST.get('sort_category') or 2)
        if request.FILES.get('thumbnail'):
            category.thumbnail = request.FILES.get('thumbnail')
        category.save()
        return redirect('admin_panel')
    context = {
        'edit_category': category,
        'message': 'Category updated successfully'
    }
    return render(request, 'website/edit_category.html', context)

@login_required
def delete_category(request, category_id):
    category = Category.objects.get(id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('admin_panel')
    context = {
        'category': category
    }
    return render(request, 'website/delete_category.html', context)    
 

#Admin Panel 
@login_required
def admin_panel(request):
    categories=Category.objects.all()
    context={'categories':categories}
    return render(request, 'website/admin_panel.html',context)

@login_required
def admin_panel_category(request):
    categories=Category.objects.all().order_by('sort_category','-id')
    context={'categories':categories}
    return render(request, 'website/admin_panel_categories.html',context)

@login_required
def admin_panel_products(request, slug):
    category=get_object_or_404(Category, slug=slug)
    products=Product.objects.filter(category=category).order_by('sort_product','-id')
    context={
        'products':products,
        'category':category
             }
    return render(request, 'website/admin_panel_products.html',context)

#Admin-Products
@login_required
def add_product(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        price = request.POST.get('price')
        caption = request.POST.get('caption')
        sort_product = request.POST.get('sort_product')
        is_available = request.POST.get('is_available') == 'on'
        files = request.FILES.getlist('media')

        category = get_object_or_404(Category, id=category_id)

        # STEP 1: save product FAST (no delay)
        product = Product.objects.create(
            category=category,
            name=name,
            price=Decimal(price),
            caption=caption,
            is_available=is_available,
            sort_product=sort_product
        )

        # STEP 2: upload media OUTSIDE transaction
        for f in files:
            ProductMedia.objects.create(product=product, file=f)

        return redirect('admin_panel')

    return render(request, 'website/add_product.html', {'categories': categories})

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, id=category_id)
        product.name = request.POST.get('name')
        product.price = Decimal(request.POST.get('price') or 0)
        product.caption = request.POST.get('caption')
        product.sort_product = int(request.POST.get('sort_product') or 2)
        product.is_available = request.POST.get('is_available') == 'on'
        product.save()
        files = request.FILES.getlist('media')
        for f in files:
            ProductMedia.objects.create(product=product, file=f)
        return redirect('admin_panel')
    return render(request, 'website/edit_product.html', {
        'edit_product': product,
        'categories': categories
    })

@login_required 
def delete_media(request, media_id):
    media = get_object_or_404(ProductMedia, id=media_id)
    product_id = media.product.id

    # extract public_id kutoka URL
    file_url = media.file.url

    # Cloudinary delete
    cloudinary.uploader.destroy(media.file.public_id)

    # delete DB record
    media.delete()

    return redirect('edit_product', product_id=product_id)

@login_required
def delete_product(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_panel')
    context = {
        'product': product
    }
    return render(request, 'website/delete_product.html', context)

#Site Categories Zipo Hapa
def categories(request):
    categories=Category.objects.all().order_by('sort_category','-id')
    context={'categories':categories}
    return render(request, 'website/categories.html',context)
                                                                 
#Site Products Ziko Hapa.
def products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(
        category=category,
        is_available=True
    ).order_by('sort_product','-id')

    return render(request, 'website/products.html', {
        'products': products,
        'category': category
    })

# Orders Ziko Hapa
def order(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get("phone", "")
        phone = ''.join(filter(str.isdigit, phone))
        if phone.startswith("255"):
            phone = phone[3:]
        if phone.startswith("0"):
            phone = phone
        else:
            phone = "0" + phone
        if len(phone) != 10:
            return HttpResponse("Invalid phone number")
        location = request.POST.get('location')
        quantity = int(request.POST.get('quantity'))
        Order.objects.create(
            name=name,
            phone=phone,
            location=location,
            product=product,
            quantity=quantity
        )
        message = f"""
        Name: {name}
        Phone: {phone}
        Location: {location}
        Product: {product.name}
        Quantity: {quantity}
        """
        send_mail(
        subject=f"NEW ORDER - {product.name}",
        message=message,
        from_email=None,  # uses EMAIL_HOST_USER
        recipient_list=["riphatymkude96@outlook.com"],
        fail_silently=False,
        )
        return redirect('categories')
    return render(request, "website/order.html", {"product": product})

@login_required
def order_flow(request):
    orders = Order.objects.all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if not start_date or not end_date:
        today = date.today()
        start_date = today.replace(day=1)
        end_date = today
    orders = orders.filter(created_at__date__range=[start_date, end_date])
    orders = orders.order_by('-created_at')
    total_orders = orders.count()
    confirmed_orders = orders.filter(status='Confirmed').count()
    fake_orders = orders.filter(status='Fake').count()
    percentage_confirmed = (confirmed_orders / total_orders * 100) if total_orders > 0 else 0
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'confirmed_orders': confirmed_orders,
        'fake_orders': fake_orders,
        'percentage_confirmed': percentage_confirmed,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'website/order_flow.html', context)

@login_required
def set_fake(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'Fake'
    order.save()
    return redirect('order_flow')

# Site settings
@login_required
def save_meta_pixel(request):
    settings = SiteSetting.objects.first()
    if request.method == "POST":
        if request.POST.get("delete_pixel"):
            if settings:
                settings.meta_pixel = ""
                settings.save()
            return redirect('meta_pixel')
        code = request.POST.get("meta-pixel", "").strip()
        if code:
            if not settings:
                SiteSetting.objects.create(meta_pixel=code)
            else:
                settings.meta_pixel = code
                settings.save()
        return redirect('meta_pixel')
    return render(request, 'website/meta_pixel.html', {'settings': settings})

# Review
def review_page(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == "Confirmed":
        context={
            "error": "Hauruhusiwi kutoa review kabla ya Kununua/delivery"
        }
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        Review.objects.create(
            product=order.product,
            order=order,
            customer_name=order.name,
            rating=rating,
            comment=comment
        )

        return redirect("review_thanks")

    context={
        "order": order
    }
    return render(request, "website/review.html", context)

def logout_view(request):
    logout(request)
    return redirect('login')