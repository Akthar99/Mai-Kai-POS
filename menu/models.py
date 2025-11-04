from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """Menu categories"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'categories'
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Menu items/dishes"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    reference_number = models.CharField(max_length=10, unique=True, help_text='Menu reference number (e.g., 001, 002)')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(upload_to='menu/items/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    preparation_time = models.IntegerField(help_text='Preparation time in minutes', default=15)
    calories = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_items'
        ordering = ['reference_number']
    
    def __str__(self):
        return f"#{self.reference_number} - {self.name} - Rs.{self.price}"


class Modifier(models.Model):
    """Item modifiers (e.g., extra cheese, no onions)"""
    name = models.CharField(max_length=100)
    price_adjustment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Additional price for this modifier'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'modifiers'
        ordering = ['name']
    
    def __str__(self):
        if self.price_adjustment > 0:
            return f"{self.name} (+Rs.{self.price_adjustment})"
        return self.name


class Combo(models.Model):
    """Combo meals"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    items = models.ManyToManyField(MenuItem, related_name='combos')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu/combos/', null=True, blank=True)
    
    class Meta:
        db_table = 'combos'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - Rs.{self.price}"


class Promotion(models.Model):
    """Promotions and offers"""
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    applicable_items = models.ManyToManyField(MenuItem, blank=True, related_name='promotions')
    
    class Meta:
        db_table = 'promotions'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
