from django.urls import path,include
from website.views import *
from django.contrib.auth import views as auth_views

urlpatterns=[
    path('manager/',include('inventory.urls')),
    path('shipping/',include('shipping.urls')),

    path('',categories,name='categories'),
    path('admin-panel',admin_panel,name='admin_panel'),
    path('add-category/',add_category,name='add_category'),
    path('edit-category/<int:category_id>/',edit_category,name='edit_category'),
    path('delete-category/<int:category_id>/',delete_category,name='delete_category'),
    
    path('admin-panel-products/<slug:slug>/',admin_panel_products,name='admin_panel_products'),
    path('admin-panel/',admin_panel,name='admin_panel'),  
    
    
    path('products/<slug:slug>/',products,name='products'),
    path('add-product/',add_product,name='add_product'),
    path('edit-product/<int:product_id>/',edit_product,name='edit_product'),
    path('delete-product/<int:product_id>/',delete_product,name='delete_product'),

    path('order/<int:product_id>/',order,name='order'),
    path('order-flow/',order_flow,name='order_flow'),
    path('set-fake/<int:order_id>/',set_fake,name='set_fake'),
    
    path('meta-pixel/',save_meta_pixel,name='meta_pixel'),

    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),

    path('delete-media/<int:media_id>/', delete_media, name='delete_media'),
]   