from django.urls import path
from inventory import views

urlpatterns=[
    path('add_sales/',views.add_sales,name='add_sales'),
    path('edit_sales/<id>',views.edit_sales,name='edit_sales'),
    path('delete_sales/<id>',views.delete_sales,name='delete_sales'),
    
    path('stocks/',views.stocks,name='stocks'),
    path('add_stocks/',views.add_stocks,name='add_stock'),
    path('edit_stocks/<id>',views.edit_stocks,name='edit_stocks'),

    path('pending_sales/',views.pending_sales,name='pending_sales'),
    path('edit_pending_sales/<id>',views.edit_pending_sales,name='edit_pending_sales'),
    path('canceled/<id>',views.canceled,name='canceled'),


    path('sales/',views.sales_history,name='sales'), 
                              
             ]