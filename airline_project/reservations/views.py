from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Flight, Booking, Payment, Passenger, Seat, Airport

def home(request):
    airports = Airport.objects.all()
    return render(request, 'reservations/home.html',{'airports': airports})

def register_view(request):
    
    if request.method == 'POST':
        first_name  = request.POST['first_name']
        last_name   = request.POST['last_name']
        email       = request.POST['email']
        password    = request.POST['password']
        phone       = request.POST['phone']
        passport_no = request.POST['passport_no']
        dob         = request.POST['dob']

        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return redirect('register')

        user = User.objects.create_user(
            username   = email,
            email      = email,
            password   = password,
            first_name = first_name,
            last_name  = last_name,
        )

        Passenger.objects.create(
            user        = user,
            phone       = phone,
            passport_no = passport_no,
            dob         = dob,
        )

        messages.success(request, 'Account created! Please log in.')
        return redirect('login')

    return render(request, 'reservations/register.html')

def login_view(request):
    if request.method == 'POST':
        email    = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, username=email, password=password)

        if user is not None:                    # ← only login if authenticated
            login(request, user)
            next_url = request.GET.get('next')  # ← redirect back to book page
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'reservations/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def search_flights(request):
    flights = None
    return_flights = None
    trip_type = 'ONE_WAY'
    airports = Airport.objects.all()

    if request.method == 'POST':
        source      = request.POST.get('source')
        destination = request.POST.get('destination')
        date        = request.POST.get('date')
        trip_type   = request.POST.get('trip_type', 'ONE_WAY')
        return_date = request.POST.get('return_date')

        flights = Flight.objects.filter(
            source_airport__airport_code = source,
            dest_airport__airport_code   = destination,
            departure_time__date         = date,
            status                       = 'SCHEDULED'
        ).select_related('aircraft', 'source_airport', 'dest_airport')

        if trip_type == 'RETURN' and return_date:
            return_flights = Flight.objects.filter(
                source_airport__airport_code = destination,
                dest_airport__airport_code   = source,
                departure_time__date         = return_date,
                status                       = 'SCHEDULED'
            ).select_related('aircraft', 'source_airport', 'dest_airport')

            if not return_flights.exists():
                messages.info(request, 'No return flights found for the selected return date.')

        if not flights.exists():
            messages.info(request, 'No outbound flights found for this route and date.')

    return render(request, 'reservations/search_flights.html', {
        'flights':  flights,
        'return_flights': return_flights,
        'trip_type': trip_type,
        'airports': airports,
    })

@login_required(login_url='login')  
def book_flight(request, flight_id):
    
    flight    = get_object_or_404(Flight, id=flight_id)
    passenger = get_object_or_404(Passenger, user=request.user)

    available_seats = Seat.objects.filter(
        aircraft     = flight.aircraft,
        is_available = True,
    )
    
    from decimal import Decimal
    for seat in available_seats:
        if seat.seat_class == 'BUSINESS':
            seat.fare = flight.base_fare * Decimal('2.0')
        elif seat.seat_class == 'FIRST':
            seat.fare = flight.base_fare * Decimal('3.0')
        else:
            seat.fare = flight.base_fare

    if request.method == 'POST':
        seat_ids       = request.POST.getlist('seat_id')
        payment_method = request.POST['payment_method']

        if not seat_ids:
            messages.error(request, 'Please select at least one seat.')
            return redirect('book_flight', flight_id=flight_id)

        from django.db import transaction
        try:
            with transaction.atomic():
                booked_bookings = []
                # Pessimistic locking: locks the rows until transaction is fully completed
                seats = Seat.objects.select_for_update().filter(id__in=seat_ids)
                
                if len(seats) != len(seat_ids):
                    raise ValueError('Some selected seats could not be found.')
                
                # Validation check inside the protective lock
                for seat in seats:
                    if not seat.is_available:
                        raise ValueError(f'Sorry, seat {seat.seat_number} was just booked by someone else. Please choose another.')

                # Process bookings safely knowing our lock guarantees no double-booking
                for seat in seats:
                    booking = Booking.objects.create(
                        passenger=passenger, flight=flight, seat=seat, status='CONFIRMED'
                    )
                    seat_price = flight.base_fare
                    if seat.seat_class == 'BUSINESS': seat_price *= Decimal('2.0')
                    elif seat.seat_class == 'FIRST':  seat_price *= Decimal('3.0')
                    Payment.objects.create(
                        booking=booking, amount=seat_price, method=payment_method, status='SUCCESS'
                    )
                    seat.is_available = False
                    seat.save()
                    booked_bookings.append(booking)
                    
            if len(booked_bookings) == 1:
                messages.success(request, f'Booking confirmed! Your booking ID is #{booked_bookings[0].pk}') # type: ignore
                return redirect('booking_confirm', booking_id=booked_bookings[0].pk) # type: ignore
            else:
                messages.success(request, f'Successfully booked {len(booked_bookings)} seats!')
                return redirect('my_bookings')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('book_flight', flight_id=flight_id)

    return render(request, 'reservations/book_flight.html', {
        'flight':          flight,
        'available_seats': available_seats,
        'payment_methods': Payment.METHOD_CHOICES,
    })

@login_required(login_url='login')  
def book_round_trip(request, outbound_id, return_id):
    outbound_flight = get_object_or_404(Flight, id=outbound_id)
    return_flight   = get_object_or_404(Flight, id=return_id)
    passenger       = get_object_or_404(Passenger, user=request.user)

    outbound_seats = Seat.objects.filter(aircraft=outbound_flight.aircraft, is_available=True)
    return_seats   = Seat.objects.filter(aircraft=return_flight.aircraft, is_available=True)

    from decimal import Decimal
    for seat in outbound_seats:
        if seat.seat_class == 'BUSINESS': seat.fare = outbound_flight.base_fare * Decimal('2.0')
        elif seat.seat_class == 'FIRST':  seat.fare = outbound_flight.base_fare * Decimal('3.0')
        else:                             seat.fare = outbound_flight.base_fare

    for seat in return_seats:
        if seat.seat_class == 'BUSINESS': seat.fare = return_flight.base_fare * Decimal('2.0')
        elif seat.seat_class == 'FIRST':  seat.fare = return_flight.base_fare * Decimal('3.0')
        else:                             seat.fare = return_flight.base_fare

    if request.method == 'POST':
        outbound_seat_ids = request.POST.getlist('outbound_seat_id')
        return_seat_ids   = request.POST.getlist('return_seat_id')
        payment_method    = request.POST.get('payment_method')

        if not outbound_seat_ids or not return_seat_ids:
            messages.error(request, 'Please select at least one seat for both outbound and return flights.')
            return redirect('book_round_trip', outbound_id=outbound_id, return_id=return_id)

        if len(outbound_seat_ids) != len(return_seat_ids):
            messages.error(request, 'You must select the same number of seats for outbound and return flights.')
            return redirect('book_round_trip', outbound_id=outbound_id, return_id=return_id)

        from django.db import transaction

        try:
            with transaction.atomic():
                # Lock rows to safely manage concurrency
                outbound_seats_qs = Seat.objects.select_for_update().filter(id__in=outbound_seat_ids)
                return_seats_qs   = Seat.objects.select_for_update().filter(id__in=return_seat_ids)

                if len(outbound_seats_qs) != len(outbound_seat_ids) or len(return_seats_qs) != len(return_seat_ids):
                    raise ValueError('Some selected seats could not be found.')

                for seat in outbound_seats_qs:
                    if not seat.is_available: raise ValueError(f'Outbound seat {seat.seat_number} was just booked.')
                for seat in return_seats_qs:
                    if not seat.is_available: raise ValueError(f'Return seat {seat.seat_number} was just booked.')

                # Process Outbound
                for seat in outbound_seats_qs:
                    booking = Booking.objects.create(passenger=passenger, flight=outbound_flight, seat=seat, status='CONFIRMED')
                    seat_price = outbound_flight.base_fare
                    if seat.seat_class == 'BUSINESS': seat_price *= Decimal('2.0')
                    elif seat.seat_class == 'FIRST':  seat_price *= Decimal('3.0')
                    Payment.objects.create(booking=booking, amount=seat_price, method=payment_method, status='SUCCESS')
                    seat.is_available = False
                    seat.save()

                # Process Return
                for seat in return_seats_qs:
                    booking = Booking.objects.create(passenger=passenger, flight=return_flight, seat=seat, status='CONFIRMED')
                    seat_price = return_flight.base_fare
                    if seat.seat_class == 'BUSINESS': seat_price *= Decimal('2.0')
                    elif seat.seat_class == 'FIRST':  seat_price *= Decimal('3.0')
                    Payment.objects.create(booking=booking, amount=seat_price, method=payment_method, status='SUCCESS')
                    seat.is_available = False
                    seat.save()

            messages.success(request, f'Successfully booked a Round-Trip for {len(outbound_seat_ids)} passenger(s)!')
            return redirect('my_bookings')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('book_round_trip', outbound_id=outbound_id, return_id=return_id)

    return render(request, 'reservations/book_round_trip.html', {
        'outbound_flight': outbound_flight,
        'return_flight':   return_flight,
        'outbound_seats':  outbound_seats,
        'return_seats':    return_seats,
        'payment_methods': Payment.METHOD_CHOICES,
    })

@login_required(login_url='login')
def booking_confirm(request, booking_id):
    booking = get_object_or_404(
        Booking,
        pk = booking_id,
        passenger = get_object_or_404(Passenger, user=request.user)
    )
    return render(request, 'reservations/booking_confirm.html', {'booking': booking})



@login_required(login_url='login')
def my_bookings(request):
    passenger = get_object_or_404(Passenger, user=request.user)

    # Get all bookings, newest first
    # select_related fetches flight, seat, payment in one query (no N+1 problem)
    bookings = Booking.objects.filter(
        passenger=passenger
    ).select_related(
        'flight',
        'flight__source_airport',
        'flight__dest_airport',
        'seat',
        'payment',
    ).order_by('-booking_date')

    return render(request, 'reservations/my_bookings.html', {'bookings': bookings})



@login_required(login_url='login')
def cancel_booking(request, booking_id):
    passenger = get_object_or_404(Passenger, user=request.user)
    booking   = get_object_or_404(Booking, pk=booking_id, passenger=passenger)


    if booking.status != 'CONFIRMED':
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('my_bookings')


    if booking.flight.departure_time < timezone.now():
        messages.error(request, 'Cannot cancel a booking for a flight that has already departed.')
        return redirect('my_bookings')

    if request.method == 'POST':

        booking.status = 'CANCELLED'
        booking.save()


        if booking.seat:
            booking.seat.is_available = True
            booking.seat.save()


        if hasattr(booking, 'payment'):
            booking.payment.status = 'REFUNDED' # type: ignore
            booking.payment.save() # type: ignore

        messages.success(request, f'Booking #{booking.pk} has been cancelled and refunded.') # type: ignore
        return redirect('my_bookings')


    return render(request, 'reservations/cancel_confirm.html', {'booking': booking})



