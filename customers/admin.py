from django.contrib import admin
from .models import Customer, LoyaltyProgram, LoyaltyTransaction, MarketingCampaign, CustomerFeedback


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'phone', 'email', 'loyalty_points', 'is_vip')
    list_filter = ('is_vip',)
    search_fields = ('first_name', 'last_name', 'phone', 'email')


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'points_per_currency', 'is_active')


@admin.register(MarketingCampaign)
class MarketingCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign_type', 'status', 'scheduled_date')
    list_filter = ('campaign_type', 'status')
