from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with roles"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('waiter', 'Waiter'),
        ('chef', 'Chef'),
        ('delivery', 'Delivery'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='waiter')
    phone = models.CharField(max_length=15, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active_duty = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='staff/profiles/', null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_display_name(self):
        return self.get_full_name() or self.username


class Attendance(models.Model):
    """Track staff attendance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance'
        ordering = ['-check_in']
    
    def __str__(self):
        return f"{self.user} - {self.check_in.date()}"
    
    @property
    def duration(self):
        if self.check_out:
            return self.check_out - self.check_in
        return None


class Shift(models.Model):
    """Shift management"""
    SHIFT_TYPES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
    ]
    
    name = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    assigned_users = models.ManyToManyField(User, related_name='shifts', blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'shifts'
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class TipDistribution(models.Model):
    """Track tip distribution among staff"""
    date = models.DateField(auto_now_add=True)
    total_tips = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tips')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'tip_distributions'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.user} - {self.amount} on {self.date}"
