import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maikai_pos.settings')
django.setup()

from billing.models import Payment
from django.utils import timezone
from django.db.models import Sum

today = timezone.now().date()

print(f"\n=== Payment Debug Info for {today} ===\n")

all_payments = Payment.objects.filter(status='completed')
print(f"Total completed payments: {all_payments.count()}")

today_payments = all_payments.filter(created_at__date=today)
print(f"\nPayments created today: {today_payments.count()}")

for p in today_payments:
    print(f"  - Payment #{p.payment_number}")
    print(f"    Amount: Rs.{p.amount}")
    print(f"    Created: {p.created_at}")
    print(f"    Completed: {p.completed_at}")
    print(f"    Created Date: {p.created_at.date()}")
    print(f"    Completed Date: {p.completed_at.date() if p.completed_at else 'NULL'}")
    print()

# Test the query we're using
revenue_query1 = Payment.objects.filter(
    status='completed',
    completed_at__date=today
)
print(f"\nQuery 1 (completed_at__date=today): {revenue_query1.count()} payments")
total1 = revenue_query1.aggregate(total=Sum('amount'))['total'] or 0
print(f"Total Revenue: Rs.{total1}")

# Alternative query
from django.db.models import Q
revenue_query2 = Payment.objects.filter(
    status='completed'
).filter(
    Q(completed_at__date=today) | 
    (Q(completed_at__isnull=True) & Q(created_at__date=today))
)
print(f"\nQuery 2 (with fallback): {revenue_query2.count()} payments")
total2 = revenue_query2.aggregate(total=Sum('amount'))['total'] or 0
print(f"Total Revenue: Rs.{total2}")

print("\n" + "="*50 + "\n")
