from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('financial/', views.financial_report, name='financial_report'),
    path('orders-export/', views.orders_export_page, name='orders_export_page'),
    path('export/orders-pdf/', views.export_orders_pdf, name='export_orders_pdf'),
]
