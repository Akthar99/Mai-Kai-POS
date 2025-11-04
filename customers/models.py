from django.db import models


class Customer(models.Model):
    """Customer information"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    
    date_of_birth = models.DateField(null=True, blank=True)
    anniversary_date = models.DateField(null=True, blank=True)
    
    is_vip = models.BooleanField(default=False)
    loyalty_points = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    visit_count = models.IntegerField(default=0)
    
    preferences = models.TextField(blank=True, help_text='Food preferences, allergies, etc.')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class LoyaltyProgram(models.Model):
    """Loyalty program configuration"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    points_per_currency = models.IntegerField(default=1, help_text='Points earned per currency unit spent')
    points_to_currency = models.DecimalField(max_digits=10, decimal_places=2, help_text='Currency value per point')
    min_redemption_points = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'loyalty_programs'
    
    def __str__(self):
        return self.name


class LoyaltyTransaction(models.Model):
    """Loyalty points transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('earn', 'Earned'),
        ('redeem', 'Redeemed'),
        ('adjust', 'Adjustment'),
        ('expire', 'Expired'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='loyalty_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'loyalty_transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer} - {self.points} points {self.get_transaction_type_display()}"


class MarketingCampaign(models.Model):
    """Marketing campaigns"""
    CAMPAIGN_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    
    target_customers = models.ManyToManyField(Customer, related_name='campaigns')
    
    scheduled_date = models.DateTimeField(null=True, blank=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'marketing_campaigns'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class CustomerFeedback(models.Model):
    """Customer feedback and ratings"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='feedback')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='feedback')
    
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    food_quality = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    service_quality = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    ambience = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'customer_feedback'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer} - {self.rating} stars"
