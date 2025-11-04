from django.db import models
from django.conf import settings


class Table(models.Model):
    """Restaurant tables"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('cleaning', 'Cleaning'),
    ]
    
    table_number = models.CharField(max_length=10, unique=True)
    capacity = models.IntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=100, blank=True, help_text='e.g., Indoor, Outdoor, VIP')
    is_active = models.BooleanField(default=True)
    
    assigned_server = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tables'
    )
    
    occupied_since = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tables'
        ordering = ['table_number']
    
    def __str__(self):
        return f"Table {self.table_number}"


class TableCombination(models.Model):
    """For combining multiple tables"""
    name = models.CharField(max_length=100)
    tables = models.ManyToManyField(Table, related_name='combinations')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'table_combinations'
    
    def __str__(self):
        return self.name


class Reservation(models.Model):
    """Table reservations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    reservation_number = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    customer_email = models.EmailField(blank=True)
    
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, related_name='reservations')
    party_size = models.IntegerField()
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reservations'
        ordering = ['-reservation_date', '-reservation_time']
    
    def __str__(self):
        return f"{self.customer_name} - {self.reservation_date} {self.reservation_time}"


class Waitlist(models.Model):
    """Restaurant waitlist"""
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('seated', 'Seated'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    party_size = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    estimated_wait_time = models.IntegerField(help_text='Wait time in minutes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    seated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'waitlist'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.customer_name} - Party of {self.party_size}"
