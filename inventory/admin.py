from django.contrib import admin
from .models import Vendor, StockLocation, StockItem, Recipe, StockMovement, PurchaseOrder, PurchaseOrderItem, StockAlert


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'phone', 'email')


@admin.register(StockLocation)
class StockLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'current_quantity', 'min_quantity', 'unit', 'unit_cost', 'stock_value', 'is_low_stock')
    list_filter = ('category', 'location', 'vendor')
    search_fields = ('name', 'sku')
    readonly_fields = ('stock_value',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'category')
        }),
        ('Quantity & Unit', {
            'fields': ('unit', 'current_quantity', 'min_quantity', 'max_quantity')
        }),
        ('Pricing', {
            'fields': ('unit_cost', 'stock_value')
        }),
        ('References', {
            'fields': ('vendor', 'location')
        }),
        ('Expiry Tracking', {
            'fields': ('expiry_tracking', 'expiry_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'status', 'order_date', 'expected_delivery', 'total_amount')
    list_filter = ('status', 'order_date')
    search_fields = ('po_number', 'vendor__name')


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'stock_item', 'quantity', 'unit_cost', 'total_cost')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('stock_item', 'movement_type', 'quantity', 'created_by', 'created_at')
    list_filter = ('movement_type', 'created_at')
    search_fields = ('stock_item__name', 'reference')
    readonly_fields = ('created_at',)


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('stock_item', 'alert_type', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'is_resolved', 'created_at')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'stock_item', 'quantity_required')
    list_filter = ('menu_item__category',)
    search_fields = ('menu_item__name', 'stock_item__name')
