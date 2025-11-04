from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def generate_bill(request, order_id):
    return render(request, 'billing/generate_bill.html')


@login_required
def process_payment(request, bill_id):
    return render(request, 'billing/process_payment.html')


@login_required
def generate_receipt(request, bill_id):
    return render(request, 'billing/receipt.html')
