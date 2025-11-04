from django.db import models
from django.conf import settings
from orders.models import Order


class Payment(models.Model):
    """Payment records"""
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Wallet'),
        ('qr', 'QR Payment'),
        ('loyalty', 'Loyalty Points'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    payment_number = models.CharField(max_length=20, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    reference_number = models.CharField(max_length=100, blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_number} - {self.get_payment_method_display()}"


class Bill(models.Model):
    """Bills/Invoices"""
    bill_number = models.CharField(max_length=20, unique=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='bill')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_paid = models.BooleanField(default=False)
    is_printed = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bills'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bill #{self.bill_number}"


class SplitPayment(models.Model):
    """Split payment among multiple people"""
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='split_payments')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='splits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        db_table = 'split_payments'
    
    def __str__(self):
        return f"{self.bill.bill_number} - {self.amount}"


class Refund(models.Model):
    """Refund records"""
    refund_number = models.CharField(max_length=20, unique=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'refunds'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund #{self.refund_number}"


class Receipt(models.Model):
    """Receipt records"""
    receipt_number = models.CharField(max_length=20, unique=True)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='receipts')
    receipt_type = models.CharField(max_length=20, choices=[('digital', 'Digital'), ('paper', 'Paper')])
    email_sent_to = models.EmailField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'receipts'
    
    def __str__(self):
        return f"Receipt #{self.receipt_number}"
