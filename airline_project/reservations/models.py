from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Airport(models.Model):
    airport_code = models.CharField(max_length=10,unique=True)
    airport_name = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.airport_code} — {self.city}"
    
class Aircraft(models.Model):
    model = models.CharField(max_length=50)
    total_seats = models.IntegerField()
    airline_name = models.CharField(max_length=50)

class Flight(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED',  'Scheduled'),
        ('DELAYED',    'Delayed'),
        ('CANCELLED',  'Cancelled'),
        ('COMPLETED',  'Completed'),
    ]

    flight_number    = models.CharField(max_length=20, unique=True)
    aircraft         = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    source_airport   = models.ForeignKey(Airport, on_delete=models.CASCADE,
                                         related_name='departing_flights')
    dest_airport     = models.ForeignKey(Airport, on_delete=models.CASCADE,
                                         related_name='arriving_flights')
    departure_time   = models.DateTimeField()
    arrival_time     = models.DateTimeField()   # ← make sure this line exists
    base_fare        = models.DecimalField(max_digits=10, decimal_places=2)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                        default='SCHEDULED')
    # arrival_time = models.DateTimeField()

    def __str__(self):
        return f"{self.flight_number}: {self.source_airport.airport_code} → {self.dest_airport.airport_code}"
    
class Seat(models.Model):

    CLASS_CHOICES = [
        ('ECONOMY',   'Economy'),
        ('BUSINESS',  'Business'),
        ('FIRST',     'First Class'),
    ]

    aircraft     = models.ForeignKey(Aircraft, on_delete=models.CASCADE,related_name='seats')
    seat_number  = models.CharField(max_length=5)   # e.g. "12A"
    seat_class   = models.CharField(max_length=20, choices=CLASS_CHOICES,default='ECONOMY')
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('aircraft', 'seat_number')  # no duplicate seats per aircraft

    def __str__(self):
        return f"{self.seat_number} ({self.seat_class}) — {self.aircraft}"

class Passenger(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    phone       = models.CharField(max_length=15)
    passport_no = models.CharField(max_length=20, unique=True)
    dob         = models.DateField()

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.email})"

class Booking(models.Model):

    STATUS_CHOICES = [
        ('CONFIRMED',  'Confirmed'),
        ('CANCELLED',  'Cancelled'),
        ('PENDING',    'Pending'),
    ]

    # booking_id = models.AutoField(primary_key=True)
    passenger    = models.ForeignKey(Passenger, on_delete=models.CASCADE,related_name='bookings')
    flight       = models.ForeignKey(Flight, on_delete=models.CASCADE,related_name='bookings')
    seat         = models.ForeignKey(Seat, on_delete=models.PROTECT, null=True,related_name='bookings')
    booking_date = models.DateTimeField(auto_now_add=True)  # auto-set on creation
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,default='PENDING')

    def __str__(self):
        return f"Booking #{self.id} — {self.passenger} on {self.flight}"

class Payment(models.Model):

    METHOD_CHOICES = [
        ('CREDIT_CARD',  'Credit Card'),
        ('DEBIT_CARD',   'Debit Card'),
        ('UPI',          'UPI'),
        ('NET_BANKING',  'Net Banking'),
    ]

    STATUS_CHOICES = [
        ('SUCCESS',  'Success'),
        ('FAILED',   'Failed'),
        ('PENDING',  'Pending'),
        ('REFUNDED', 'Refunded'),
    ]

    # id:int
    booking      = models.OneToOneField(Booking, on_delete=models.CASCADE,
                                        related_name='payment')
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    method       = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default='PENDING')
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} — ₹{self.amount} [{self.status}]" # type: ignore


