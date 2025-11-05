from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('sales/', views.sales, name='sales'),
    path('sales/order/<int:table_id>/', views.order_entry, name='order_entry'),
    path('sales/order/<int:table_id>/items/', views.get_order_items, name='get_order_items'),
    path('sales/order/create/<int:table_id>/', views.create_order, name='create_order'),
    path('sales/order/<int:table_id>/add-item/', views.add_order_item, name='add_order_item'),
    path('sales/order/item/<int:item_id>/update/', views.update_order_item, name='update_order_item'),
    path('sales/order/item/<int:item_id>/remove/', views.remove_order_item, name='remove_order_item'),
    path('sales/order/<int:table_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('sales/order/<int:table_id>/change-table/', views.change_table, name='change_table'),
    path('sales/order/<int:table_id>/print-kot/', views.print_kot, name='print_kot'),
    path('sales/order/<int:table_id>/payment/', views.payment_page, name='payment_page'),
    path('sales/order/<int:table_id>/process-payment/', views.process_payment, name='process_payment'),
    path('sales/order/<int:table_id>/<int:order_id>/receipt/', views.print_receipt, name='print_receipt'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
