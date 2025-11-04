from django.contrib import admin
from .models import Category, MenuItem, Modifier, Combo, Promotion


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'name', 'category', 'price', 'is_available', 'is_vegetarian')
    list_filter = ('category', 'is_available', 'is_vegetarian', 'is_vegan', 'is_spicy')
    search_fields = ('reference_number', 'name', 'description')
    list_editable = ('price', 'is_available')
    ordering = ('reference_number',)


@admin.register(Modifier)
class ModifierAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_adjustment', 'is_active')
    list_filter = ('is_active',)


@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    list_filter = ('is_available',)
    filter_horizontal = ('items',)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active')
    list_filter = ('discount_type', 'is_active', 'start_date')
    filter_horizontal = ('applicable_items',)
