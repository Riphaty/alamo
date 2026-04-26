from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from website.models import *
from django.core.mail import send_mail
from datetime import date
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from decimal import Decimal
import cloudinary.uploader
import json
import os


# =========================
# ADMIN PANEL
# =========================

@login_required
def admin_panel(request):
    categories = Category.objects.all()
    return render(request, 'website/admin_panel.html', {'categories': categories})


@login_required
def admin_panel_category(request):
    categories = Category.objects.all()
    return render(request, 'website/admin_panel_categories.html', {'categories': categories})


@login_required
def admin_panel_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category).order_by('name')

    return render(request, 'website/admin_panel_products.html', {
        'products': products,
        'category': category
    })


# =========================
# CATEGORY (CLOUDINARY)
# =========================

@login_required
def add_category(request):
    if request.method == 'POST':

        Category.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            thumbnail_url=request.POST.get('thumbnail_url'),
            media_type=request.POST.get('thumbnail_type', 'image'),
            public_id=request.POST.get('thumbnail_public_id', '')
        )

        return redirect('admin_panel')

    return render(request, 'website/add_category.html')


@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':

        category.name = request.POST.get('name')
        category.description = request.POST.get('description')

        thumbnail_url = request.POST.get('thumbnail_url')
        if thumbnail_url:
            category.thumbnail_url = thumbnail_url

        category.save()
        return redirect('admin_panel')

    return render(request, 'website/edit_category.html', {
        'edit_category': category
    })


@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        category.delete()
        return redirect('admin_panel')

    return render(request, 'website/delete_category.html', {'category': category})


# =========================
# PRODUCTS (CLOUDINARY JSON PIPELINE)
# =========================

@login_required
def add_product(request):
    categories = Category.objects.all()

    if request.method == 'POST':

        category = get_object_or_404(Category, id=request.POST.get('category'))

        name = request.POST.get('name')
        price = request.POST.get('price')
        caption = request.POST.get('caption')
        is_available = request.POST.get('is_available') == 'on'

        media_data = request.POST.get('media_data')

        if not name or not price:
            return render(request, 'website/add_product.html', {
                'categories': categories,
                'message': 'Jaza taarifa zote muhimu'
            })

        product = Product.objects.create(
            category=category,
            name=name,
            price=price,
            caption=caption,
            is_available=is_available
        )

        # CLOUDINARY MEDIA SAVE
        if media_data:
            media_list = json.loads(media_data)

            for m in media_list:
                ProductImage.objects.create(
                    product=product,
                    product_url=m['url'],
                    product_media_type=m['type'],
                    product_public_id=m['public_id']
                )

        return redirect('admin_panel_products', slug=category.slug)

    return render(request, 'website/add_product.html', {
        'categories': categories
    })


@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()

    if request.method == 'POST':

        product.category = get_object_or_404(Category, id=request.POST.get('category'))
        product.name = request.POST.get('name', '').strip()
        product.caption = request.POST.get('caption', '').strip()

        try:
            product.price = Decimal(request.POST.get('price', 0))
        except:
            product.price = Decimal('0')

        product.is_available = bool(request.POST.get('is_available'))
        product.save()

        media_data = request.POST.get('media_data')

        if media_data:
            product.images.all().delete()

            media_list = json.loads(media_data)

            for m in media_list:
                ProductImage.objects.create(
                    product=product,
                    product_url=m['url'],
                    product_media_type=m['type'],
                    product_public_id=m['public_id']
                )

        return redirect('admin_panel_products', slug=product.category.slug)

    return render(request, 'website/edit_product.html', {
        'edit_product': product,
        'categories': categories
    })


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    slug = product.category.slug if product.category else None

    if request.method == 'POST':
        product.delete()
        return redirect('admin_panel_products', slug=slug)

    return render(request, 'website/delete_product.html', {'product': product})


# =========================
# SITE VIEWS
# =========================

def categories(request):
    return render(request, 'website/categories.html', {
        'categories': Category.objects.all()
    })


def products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category, is_available=True).order_by('-id')

    message = 'Hakuna bidhaa katika category hii' if not products.exists() else ''

    return render(request, 'website/products.html', {
        'products': products,
        'category': category,
        'message': message
    })


# =========================
# ORDERS
# =========================

def order(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':

        name = request.POST.get('name')
        phone = ''.join(filter(str.isdigit, request.POST.get("phone", "")))

        if not phone.startswith("0"):
            phone = "0" + phone[-9:]

        if len(phone) != 10:
            return HttpResponse("Invalid phone number")

        Order.objects.create(
            name=name,
            phone=phone,
            location=request.POST.get('location'),
            product=product,
            quantity=int(request.POST.get('quantity'))
        )

        send_mail(
            subject=f"NEW ORDER - {product.name}",
            message=f"{name} ordered {product.name}",
            from_email=None,
            recipient_list=["riphatymkude96@outlook.com"],
            fail_silently=False,
        )

        return redirect('categories')

    return render(request, "website/order.html", {"product": product})


# =========================
# AUTH
# =========================

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')