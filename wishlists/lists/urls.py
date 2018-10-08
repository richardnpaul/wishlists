from django.urls import path

from . import views

urlpatterns = [
    path('new/', views.new_list, name='new_list'),

    # Wishlist lists
    path('lists/', views.view_my_lists, name='view_my_lists'),
    path('lists/<int:user_id>/', views.view_users_lists, name='view_users_lists'),

    # Users
    path('users/', views.view_users, name='view_users'),

    # Wishlist Items
    path('<uuid:wishlist_uuid>/', views.view_list, name='view_list'),
    path('<uuid:wishlist_uuid>/edit/', views.edit_list, name='edit_list'),

    # Items
    path('item/<uuid:item_uuid>/', views.view_list_item,
         name='view_list_item'),
    path('item/<uuid:item_uuid>/buy/', views.buy_list_item,
         name='buy_list_item'),
    path('item/<uuid:item_uuid>/return/', views.return_list_item,
         name='return_list_item'),
    path('items/', views.view_all_bought_items, name='bought_items'),

    #path('<uuid:wishlist_uuid>/share/', views.share_list, name='share_list'),
]