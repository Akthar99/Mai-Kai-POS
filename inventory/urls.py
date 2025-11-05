from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path('stock-items/', views.stock_items, name='stock_items'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    
    # Vendors
    path('vendors/', views.vendors_list, name='vendors_list'),
    path('vendors/add/', views.add_vendor, name='add_vendor'),
    path('vendors/<int:vendor_id>/edit/', views.edit_vendor, name='edit_vendor'),
    path('vendors/<int:vendor_id>/delete/', views.delete_vendor, name='delete_vendor'),
    
    # Purchase Orders
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('purchase-orders/create/', views.create_purchase_order, name='create_purchase_order'),
    path('purchase-orders/<int:po_id>/', views.view_purchase_order, name='view_purchase_order'),
    path('purchase-orders/<int:po_id>/edit/', views.edit_purchase_order, name='edit_purchase_order'),
    path('purchase-orders/<int:po_id>/delete/', views.delete_purchase_order, name='delete_purchase_order'),
    path('purchase-orders/<int:po_id>/send/', views.send_purchase_order, name='send_purchase_order'),
    path('purchase-orders/<int:po_id>/receive/', views.receive_purchase_order, name='receive_purchase_order'),
    
    path('movements/', views.stock_movements, name='stock_movements'),
    path('add-item/', views.add_stock_item, name='add_stock_item'),
    path('update-stock/<int:item_id>/', views.update_stock, name='update_stock'),
]
