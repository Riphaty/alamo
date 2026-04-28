from django.utils.text import slugify
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    thumbnail = models.ImageField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category_view = models.PositiveBigIntegerField(default=0)
    slug = models.SlugField(unique=True, blank=True)
    sort_category=models.PositiveIntegerField(default=2)
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=0, validators=[MinValueValidator(0)])
    caption = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    product_view = models.PositiveBigIntegerField(default=0)
    sort_product=models.PositiveIntegerField(default=2)
    def __str__(self):
        return self.name

class ProductMedia(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='media')
    file = CloudinaryField(resource_type="auto")  
    def is_video(self):
        if not self.file:
            return False
        return self.file.resource_type == "video"
    def __str__(self):
        return f'Media for {self.product.name}'
        
class Order(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Fake', 'Fake'),
    ]
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.location

class SiteSetting(models.Model):
    meta_pixel = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Site Settings"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MaxValueValidator(5)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}"