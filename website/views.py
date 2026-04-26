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

# Create your views here.
#Admin Panel Ziko Hapa
#Admin-Categories
@login_required
def add_category(request):
    if request.method=='POST':
        name=request.POST.get('name')
        thumbnail=request.FILES.get('thumbnail')
        description=request.POST.get('description')
        Category.objects.create(name=name,thumbnail=thumbnail,description=description)
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
        files = request.FILES.getlist('images')
        if not name or not price:
            return render(request, 'website/add_product.html', {
                'categories': categories,
                'message': 'Jaza taarifa zote muhimu'
            })
        category = get_object_or_404(Category, id=category_id)
        ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.mp4', '.webm')
        with transaction.atomic():
            product = Product.objects.create(
                category=category,
                name=name,
                price=price,
                caption=caption,
                is_available=is_available
            )

            for f in files:
                if f.name.lower().endswith(ALLOWED_EXTENSIONS):
                    ProductImage.objects.create(product=product, file=f)
        return redirect('admin_panel')
    return render(request, 'website/add_product.html', {'categories': categories})

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':

        # =====================
        # BASIC FIELDS
        # =====================
        product.category = get_object_or_404(Category, id=request.POST.get('category'))
        product.name = request.POST.get('name', '').strip()
        product.caption = request.POST.get('caption', '').strip()

        try:
            product.price = Decimal(request.POST.get('price', 0))
        except:
            product.price = Decimal('0')

        product.is_available = bool(request.POST.get('is_available'))

        product.save()
        files = request.FILES.getlist('images')

        # fallback (mobile sometimes sends single file)
        if not files:
            single_file = request.FILES.get('images')
            if single_file:
                files = [single_file]

        valid_files = []

        for f in files:
            if not f:
                continue

            content_type = f.content_type.lower()

            # accept images + videos + HEIC
            if not (
                content_type.startswith('image/')
                or content_type.startswith('video/')
                or 'heic' in content_type
            ):
                continue

            # size limits
            if content_type.startswith('image/') and f.size > 5 * 1024 * 1024:
                continue

            if content_type.startswith('video/') and f.size > 25 * 1024 * 1024:
                continue

            valid_files.append(f)

        # =====================
        # SAVE MEDIA
        # =====================
        if valid_files:
            # delete old media
            product.images.all().delete()

            for f in valid_files:
                ProductImage.objects.create(
                    product=product,
                    file=f
                )

        return redirect('admin_panel_products', slug=product.category.slug)
    return render(request, 'website/edit_product.html', {
        'edit_product': product,
        'categories': categories
    })

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # 🔥 SAFE EXTRACTION
    category_slug = None
    if product.category:
        category_slug = product.category.slug

    if request.method == 'POST':
        product.delete()

        if category_slug:
            return redirect('admin_panel_products', slug=category_slug)
        return redirect('admin_panel_products')

    return render(request, 'website/delete_product.html', {
        'product': product
    })

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
@login_required
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