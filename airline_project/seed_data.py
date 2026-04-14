import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airline_project.settings')
django.setup()

from reservations.models import Airport, Aircraft, Flight, Seat
from datetime import datetime, timedelta
from django.utils import timezone

# Clear old data
Seat.objects.all().delete()
Flight.objects.all().delete()
Aircraft.objects.all().delete()
Airport.objects.all().delete()
print("Old data cleared.")

# Airports
airports_data = [
    ('BOM', 'Chhatrapati Shivaji Maharaj International', 'Mumbai',     'India'),
    ('DEL', 'Indira Gandhi International',               'Delhi',      'India'),
    ('BLR', 'Kempegowda International',                  'Bangalore',  'India'),
    ('MAA', 'Chennai International',                     'Chennai',    'India'),
    ('CCU', 'Netaji Subhas Chandra Bose International',  'Kolkata',    'India'),
    ('HYD', 'Rajiv Gandhi International',                'Hyderabad',  'India'),
    ('PNQ', 'Pune Airport',                              'Pune',       'India'),
    ('AMD', 'Sardar Vallabhbhai Patel International',    'Ahmedabad',  'India'),
    ('GOI', 'Goa International',                         'Goa',        'India'),
    ('JAI', 'Jaipur International',                      'Jaipur',     'India'),
    ('LKO', 'Chaudhary Charan Singh International',      'Lucknow',    'India'),
    ('NAG', 'Dr. Babasaheb Ambedkar International',      'Nagpur',     'India'),
    ('COK', 'Cochin International',                      'Kochi',      'India'),
    ('TRV', 'Trivandrum International',                  'Trivandrum', 'India'),
    ('IXC', 'Chandigarh International',                  'Chandigarh', 'India'),
    ('PAT', 'Jay Prakash Narayan International',         'Patna',      'India'),
    ('BHO', 'Raja Bhoj Airport',                         'Bhopal',     'India'),
    ('SXR', 'Sheikh ul Alam International',              'Srinagar',   'India'),
    ('GAU', 'Lokpriya Gopinath Bordoloi International',  'Guwahati',   'India'),
    ('VNS', 'Lal Bahadur Shastri International',         'Varanasi',   'India'),
]

airports = {}
for code, name, city, country in airports_data:
    a = Airport.objects.create(airport_code=code, airport_name=name, city=city, country=country)
    airports[code] = a
print(f"{len(airports)} airports created.")

# Aircraft
aircraft_data = [
    ('Boeing 737-800',  180, 'Air India'),
    ('Airbus A320',     160, 'IndiGo'),
    ('Boeing 777-300',  300, 'Air India'),
    ('Airbus A321',     185, 'SpiceJet'),
    ('Boeing 737 MAX',  175, 'Vistara'),
    ('Airbus A320neo',  165, 'GoAir'),
]

aircraft = {}
for model, seats, airline in aircraft_data:
    ac = Aircraft.objects.create(model=model, total_seats=seats, airline_name=airline)
    aircraft[f"{airline}_{model}"] = ac
print(f"{len(aircraft)} aircraft created.")

# Seats
def create_seats(ac):
    seats = []
    for row in range(1, 3):
        for col in ['A', 'B', 'C', 'D']:
            seats.append(Seat(aircraft=ac, seat_number=f'{row}{col}', seat_class='FIRST', is_available=True))
    for row in range(3, 7):
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            seats.append(Seat(aircraft=ac, seat_number=f'{row}{col}', seat_class='BUSINESS', is_available=True))
    for row in range(7, 31):
        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            seats.append(Seat(aircraft=ac, seat_number=f'{row}{col}', seat_class='ECONOMY', is_available=True))
    Seat.objects.bulk_create(seats)

for ac in aircraft.values():
    create_seats(ac)
print("Seats created for all aircraft.")

# Flights
def make_flight(number, ac, src, dst, dep_hour, dep_min, duration_hrs, fare):
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = 0
    for day in range(1, 31):
        dep = today + timedelta(days=day)
        dep = dep.replace(hour=dep_hour, minute=dep_min)
        arr = dep + timedelta(hours=duration_hrs)
        Flight.objects.create(
            flight_number=f'{number}-{day:02d}',
            aircraft=ac,
            source_airport=airports[src],
            dest_airport=airports[dst],
            departure_time=dep,
            arrival_time=arr,
            base_fare=fare,
            status='SCHEDULED'
        )
        count += 1
    return count

ac_AI_737  = aircraft['Air India_Boeing 737-800']
ac_6E_A320 = aircraft['IndiGo_Airbus A320']
ac_AI_777  = aircraft['Air India_Boeing 777-300']
ac_SG_A321 = aircraft['SpiceJet_Airbus A321']
ac_UK_737  = aircraft['Vistara_Boeing 737 MAX']
ac_G8_A320 = aircraft['GoAir_Airbus A320neo']

total = 0
total += make_flight('AI-101', ac_AI_737,  'BOM', 'DEL', 6,  0,  2.0, 4500)
total += make_flight('AI-102', ac_AI_737,  'DEL', 'BOM', 9,  0,  2.0, 4500)
total += make_flight('6E-201', ac_6E_A320, 'BOM', 'DEL', 8,  0,  2.0, 3200)
total += make_flight('6E-202', ac_6E_A320, 'DEL', 'BOM', 18, 0,  2.0, 3200)
total += make_flight('SG-301', ac_SG_A321, 'BOM', 'DEL', 12, 30, 2.0, 2800)
total += make_flight('SG-302', ac_SG_A321, 'DEL', 'BOM', 20, 0,  2.0, 2800)
total += make_flight('AI-111', ac_AI_737,  'BOM', 'BLR', 7,  0,  1.5, 3800)
total += make_flight('AI-112', ac_AI_737,  'BLR', 'BOM', 10, 0,  1.5, 3800)
total += make_flight('6E-211', ac_6E_A320, 'BOM', 'BLR', 14, 0,  1.5, 2600)
total += make_flight('6E-212', ac_6E_A320, 'BLR', 'BOM', 17, 0,  1.5, 2600)
total += make_flight('AI-121', ac_AI_737,  'BOM', 'MAA', 6,  30, 2.0, 4000)
total += make_flight('AI-122', ac_AI_737,  'MAA', 'BOM', 11, 0,  2.0, 4000)
total += make_flight('UK-401', ac_UK_737,  'BOM', 'MAA', 15, 0,  2.0, 3500)
total += make_flight('UK-402', ac_UK_737,  'MAA', 'BOM', 19, 0,  2.0, 3500)
total += make_flight('6E-221', ac_6E_A320, 'BOM', 'HYD', 7,  0,  1.5, 2900)
total += make_flight('6E-222', ac_6E_A320, 'HYD', 'BOM', 10, 30, 1.5, 2900)
total += make_flight('SG-311', ac_SG_A321, 'BOM', 'HYD', 16, 0,  1.5, 2400)
total += make_flight('SG-312', ac_SG_A321, 'HYD', 'BOM', 20, 0,  1.5, 2400)
total += make_flight('AI-131', ac_AI_777,  'BOM', 'CCU', 6,  0,  3.0, 5500)
total += make_flight('AI-132', ac_AI_777,  'CCU', 'BOM', 11, 0,  3.0, 5500)
total += make_flight('6E-231', ac_6E_A320, 'BOM', 'GOI', 8,  0,  1.0, 1800)
total += make_flight('6E-232', ac_6E_A320, 'GOI', 'BOM', 10, 30, 1.0, 1800)
total += make_flight('SG-321', ac_SG_A321, 'BOM', 'GOI', 14, 0,  1.0, 1500)
total += make_flight('SG-322', ac_SG_A321, 'GOI', 'BOM', 16, 30, 1.0, 1500)
total += make_flight('AI-141', ac_AI_737,  'DEL', 'BLR', 6,  0,  3.0, 5000)
total += make_flight('AI-142', ac_AI_737,  'BLR', 'DEL', 11, 0,  3.0, 5000)
total += make_flight('6E-241', ac_6E_A320, 'DEL', 'BLR', 9,  0,  3.0, 3500)
total += make_flight('6E-242', ac_6E_A320, 'BLR', 'DEL', 14, 0,  3.0, 3500)
total += make_flight('UK-411', ac_UK_737,  'DEL', 'MAA', 7,  0,  2.5, 4800)
total += make_flight('UK-412', ac_UK_737,  'MAA', 'DEL', 11, 30, 2.5, 4800)
total += make_flight('AI-151', ac_AI_737,  'DEL', 'HYD', 8,  0,  2.0, 4200)
total += make_flight('AI-152', ac_AI_737,  'HYD', 'DEL', 12, 0,  2.0, 4200)
total += make_flight('AI-161', ac_AI_777,  'DEL', 'CCU', 7,  0,  2.5, 4900)
total += make_flight('AI-162', ac_AI_777,  'CCU', 'DEL', 11, 30, 2.5, 4900)
total += make_flight('6E-261', ac_6E_A320, 'DEL', 'CCU', 14, 0,  2.5, 3300)
total += make_flight('6E-262', ac_6E_A320, 'CCU', 'DEL', 18, 0,  2.5, 3300)
total += make_flight('6E-271', ac_6E_A320, 'DEL', 'JAI', 8,  0,  0.75,1500)
total += make_flight('6E-272', ac_6E_A320, 'JAI', 'DEL', 10, 0,  0.75,1500)
total += make_flight('AI-171', ac_AI_737,  'DEL', 'SXR', 7,  0,  1.5, 3800)
total += make_flight('AI-172', ac_AI_737,  'SXR', 'DEL', 10, 0,  1.5, 3800)
total += make_flight('6E-281', ac_6E_A320, 'BLR', 'MAA', 8,  0,  1.0, 1600)
total += make_flight('6E-282', ac_6E_A320, 'MAA', 'BLR', 10, 30, 1.0, 1600)
total += make_flight('G8-501', ac_G8_A320, 'BLR', 'HYD', 7,  0,  1.0, 1700)
total += make_flight('G8-502', ac_G8_A320, 'HYD', 'BLR', 10, 0,  1.0, 1700)
total += make_flight('AI-181', ac_AI_737,  'CCU', 'GAU', 8,  0,  1.0, 2500)
total += make_flight('AI-182', ac_AI_737,  'GAU', 'CCU', 11, 0,  1.0, 2500)
total += make_flight('6E-291', ac_6E_A320, 'BOM', 'AMD', 7,  0,  1.0, 1800)
total += make_flight('6E-292', ac_6E_A320, 'AMD', 'BOM', 9,  30, 1.0, 1800)
total += make_flight('SG-331', ac_SG_A321, 'BOM', 'PNQ', 7,  0,  0.5, 1200)
total += make_flight('SG-332', ac_SG_A321, 'PNQ', 'BOM', 9,  0,  0.5, 1200)
total += make_flight('AI-191', ac_AI_737,  'DEL', 'LKO', 8,  0,  1.0, 2200)
total += make_flight('AI-192', ac_AI_737,  'LKO', 'DEL', 10, 30, 1.0, 2200)
total += make_flight('UK-421', ac_UK_737,  'DEL', 'VNS', 9,  0,  1.5, 2800)
total += make_flight('UK-422', ac_UK_737,  'VNS', 'DEL', 12, 0,  1.5, 2800)
total += make_flight('AI-201', ac_AI_737,  'BOM', 'COK', 7,  0,  2.0, 3600)
total += make_flight('AI-202', ac_AI_737,  'COK', 'BOM', 11, 0,  2.0, 3600)

print(f"\n✅ All done!")
print(f"  Airports : {Airport.objects.count()}")
print(f"  Aircraft : {Aircraft.objects.count()}")
print(f"  Flights  : {Flight.objects.count()}")
print(f"  Seats    : {Seat.objects.count()}")