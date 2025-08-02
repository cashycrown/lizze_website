from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
     path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('404/', views.page_404, name='page_404'),
    path('contact/', views.contact, name='contact'),
    path('services-detail/', views.servicesDetails, name='services-detail'),
    path('create-booking/', views.create_booking, name='create_booking'),
    path('booking-success/<str:reference>/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path("confirm/<uuid:token>/", views.send_customer_confirmation, name="send_customer_confirmation")

  ]
