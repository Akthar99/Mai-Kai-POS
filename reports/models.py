from django.db import models

# Reports are mostly generated from existing data, 
# but we can store generated reports here

class SalesReport(models.Model):
    """Generated sales reports"""
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=200)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    report_data = models.JSONField(default=dict)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('staff.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'sales_reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class InventoryReport(models.Model):
    """Generated inventory reports"""
    name = models.CharField(max_length=200)
    report_date = models.DateField()
    
    total_items = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_items = models.IntegerField(default=0)
    
    report_data = models.JSONField(default=dict)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('staff.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'inventory_reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.name} - {self.report_date}"
