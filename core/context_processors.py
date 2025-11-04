from django.conf import settings


def business_info(request):
    """Add business information to template context"""
    return {
        'BUSINESS_NAME': settings.BUSINESS_NAME,
        'BUSINESS_ADDRESS': settings.BUSINESS_ADDRESS,
        'BUSINESS_PHONE': settings.BUSINESS_PHONE,
        'BUSINESS_EMAIL': settings.BUSINESS_EMAIL,
        'TAX_RATE': settings.TAX_RATE,
        'SERVICE_CHARGE_RATE': settings.SERVICE_CHARGE_RATE,
        'TAX_RATE_PERCENT': int(settings.TAX_RATE * 100),
        'SERVICE_CHARGE_RATE_PERCENT': int(settings.SERVICE_CHARGE_RATE * 100),
    }
