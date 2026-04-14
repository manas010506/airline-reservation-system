from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home'),

    # Auth
    path('register/',views.register_view,name='register'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),

    # Flights
    path('search/',views.search_flights,name='search_flights'),

    # Booking
    path('book/<int:flight_id>/',views.book_flight,name='book_flight'),
    path('book-round-trip/<int:outbound_id>/<int:return_id>/',views.book_round_trip,name='book_round_trip'),
    path('confirm/<int:booking_id>/',views.booking_confirm,name='booking_confirm'),
    path('my-bookings/',views.my_bookings,name='my_bookings'),
    path('cancel/<int:booking_id>/',views.cancel_booking,name='cancel_booking'),
]