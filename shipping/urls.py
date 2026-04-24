from django.urls import path
from shipping import views

urlpatterns=[
    path('shipping/',views.shipment,name='shipping_home'),
    path('add_shipment/',views.add_shipment,name='add_shipment'),
    path('edit_shipment/<id>',views.edit_shipment,name='edit_shipment'),
    path('delete_shipment/<id>',views.delete_shipment,name='delete_shipment'),

    path('products/',views.registered_products_list,name='products'),
    path('edit_products/<id>',views.edit_registered_product,name='edit_products'),
    path('delete_products/<id>',views.delete_registered_product,name='delete_products'),
]   