from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.menu_list, name='menu_list'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('item/<int:item_id>/', views.item_detail, name='menu_item_detail'),
    path('item/create/', views.menu_item_create, name='menu_item_create'),
    path('item/<int:item_id>/update/', views.menu_item_update, name='menu_item_update'),
    path('item/<int:item_id>/delete/', views.menu_item_delete, name='menu_item_delete'),
]
