from django.db import models
from django.conf import settings


class Vendor(models.Model):
    """Supplier/Vendor information"""
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vendors'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StockLocation(models.Model):
    """Inventory locations (bar, kitchen, store, etc.)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'stock_locations'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StockItem(models.Model):
    """Inventory items"""
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('l', 'Liter'),
        ('ml', 'Milliliter'),
        ('pcs', 'Pieces'),
        ('box', 'Box'),
        ('pack', 'Pack'),
    ]
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text='Stock Keeping Unit')
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    
    current_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text='Reorder level')
    max_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, related_name='items')
    
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    
    expiry_tracking = models.BooleanField(default=False)
    expiry_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'stock_items'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def is_low_stock(self):
        return self.current_quantity <= self.min_quantity
    
    @property
    def stock_value(self):
        return self.current_quantity * self.unit_cost


class Recipe(models.Model):
    """Recipes for menu items - links menu items to inventory"""
    from menu.models import MenuItem
    
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE, related_name='recipes')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2, help_text='Quantity per serving')
    
    class Meta:
        db_table = 'recipes'
        unique_together = ['menu_item', 'stock_item']
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.stock_item.name}"


class StockMovement(models.Model):
    """Track stock movements"""
    MOVEMENT_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('waste', 'Waste'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
    ]
    
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    from_location = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_movements')
    to_location = models.ForeignKey(StockLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_movements')
    
    reference = models.CharField(max_length=100, blank=True, help_text='PO number, invoice, etc.')
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.stock_item.name}"


class PurchaseOrder(models.Model):
    """Purchase orders for inventory"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=20, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    order_date = models.DateField(auto_now_add=True)
    expected_delivery = models.DateField()
    received_date = models.DateField(null=True, blank=True)
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-order_date']
    
    def __str__(self):
        return f"PO #{self.po_number}"


class PurchaseOrderItem(models.Model):
    """Items in purchase order"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'purchase_order_items'
    
    def __str__(self):
        return f"{self.stock_item.name} - {self.quantity}"


class StockAlert(models.Model):
    """Stock alert notifications"""
    ALERT_TYPE_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
    ]
    
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'stock_alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.stock_item.name}"
