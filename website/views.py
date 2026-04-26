from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from website.models import *
from django.core.mail import send_mail
from datetime import datetime, date
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

# Create your views here.
#Admin Panel Ziko Hapa
#Admin-Categories
@login_required
def add_category(request):
    if request.method=='POST':
        name=request.POST.get('name')

        # 🔧 FIX: removed FILES dependency (Cloudinary consistency)
        Category.objects.create(
            name=name,
            thumbnail_url=request.POST.get('thumbnail_url'),
            media_type=request.POST.get('thumbnail_type','image'),
            public_id=request.POST.get('thumbnail_public_id',''),
            description=request.POST.get('description')
        )
        return redirect('admin_panel')

    context={
        'message':'Category created successfully'
        }
    return render(request,'website/add_category.html',context)    

@login_required
def edit_category(request, category_id):
    category = Category.objects.get(id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')

        # 🔧 FIX: no FILES usage
        if request.POST.get('thumbnail_url'):
            category.thumbnail_url = request.POST.get('thumbnail_url')

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
    categories=Category.objects.all()
    context={'categories':categories}
    return render(request, 'website/admin_panel_categories.html',context)

@login_required
def admin_panel_products(request, slug):
    category=get_object_or_404(Category, slug=slug)
    products=Product.objects.filter(category=category).order_by('name')
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
        is_available = request.POST.get('is_available') == 'on'

        category = get_object_or_404(Category, id=category_id)

        with transaction.atomic():
            product = Product.objects.create(
                category=category,
                name=name,
                price=price,
                caption=caption,
                is_available=is_available
            )

            # 🔧 FIX ONLY HERE (Cloudinary JSON style)
            media_data = request.POST.get('media_data')
            if media_data:
                import json
                for m in json.loads(media_data):
                    ProductImage.objects.create(
                        product=product,
                        product_url=m.get('url'),
                        product_media_type=m.get('type'),
                        product_public_id=m.get('public_id')
                    )

        return redirect('admin_panel')

    return render(request, 'website/add_product.html', {'categories': categories})

@login_required
def edit_product(request, product_id):
    product = Product.objects.get(id=product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        category_id = request.POST.get('category')
        product.category = Category.objects.get(id=category_id)
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.caption = request.POST.get('caption')
        product.is_available = request.POST.get('is_available') == 'on'
        product.save()

        # 🔧 FIX ONLY HERE (media sync)
        media_data = request.POST.get('media_data')
        if media_data:
            import json
            product.images.all().delete()
            for m in json.loads(media_data):
                ProductImage.objects.create(
                    product=product,
                    product_url=m.get('url'),
                    product_media_type=m.get('type'),
                    product_public_id=m.get('public_id')
                )

        return redirect('admin_panel_products', slug=product.category.slug)

    context = {
        'edit_product': product,
        'categories': categories,
        'message': 'Product updated successfully'
    }
    return render(request, 'website/edit_product.html', context)

@login_required
def delete_product(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('admin_panel_products')
    context = {
        'product': product
    }
    return render(request, 'website/delete_product.html', context)

#Site Categories Zipo Hapa
def categories(request):
    categories=Category.objects.all()
    context={'categories':categories}
    return render(request, 'website/categories.html',context)
                                                                 
#Site Products Ziko Hapa.
def products(request, slug):
    category=get_object_or_404(Category, slug=slug)
    products=Product.objects.filter(category=category, is_available=True).order_by('-id')   
    if not products.exists():
            message='Hakuna bidhaa katika category hii'
    else:
        message='Hakuna bidhaa kwa sasa!'
    context={
        'products':products, 
        'category': category,
        'message': message
        }
    return render(request, 'website/products.html',context)

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
        from_email=None,
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