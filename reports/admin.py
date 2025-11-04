from django.contrib import admin
from .models import SalesReport, InventoryReport


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'period', 'start_date', 'end_date', 'total_sales')


@admin.register(InventoryReport)
class InventoryReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_date', 'total_items', 'total_value')
