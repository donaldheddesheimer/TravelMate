from django.urls import path
from . import views

app_name = 'packing'

urlpatterns = [
    path('<int:trip_id>/', views.packing_list_view, name='list'),
    path('<int:trip_id>/generate/', views.generate_packing_list, name='generate'),
    path('item/<int:item_id>/update/', views.update_packing_item, name='update_item'),
    path('<int:trip_id>/add/', views.add_custom_item, name='add_item'),
]