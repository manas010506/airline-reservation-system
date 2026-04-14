from django.contrib import admin
from .models import Airport, Aircraft, Flight, Seat, Passenger, Booking, Payment

admin.site.register(Airport)
admin.site.register(Aircraft)
admin.site.register(Flight)
admin.site.register(Seat)
admin.site.register(Passenger)
admin.site.register(Booking)
admin.site.register(Payment)