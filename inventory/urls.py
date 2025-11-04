from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('stock-items/', views.stock_items, name='stock_items'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('movements/', views.stock_movements, name='stock_movements'),
    path('add-item/', views.add_stock_item, name='add_stock_item'),
    path('update-stock/<int:item_id>/', views.update_stock, name='update_stock'),
]
