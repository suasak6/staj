from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import requests

from pathlib import Path


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from route_optimizer import (
    optimize_route,
    calculate_route_distance
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_connection():
    return sqlite3.connect("route_database.db")


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/employees")
def create_employee(
    name: str,
    district: str,
    latitude: float,
    longitude: float
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO employees (name, district, latitude, longitude)
        VALUES (?, ?, ?, ?)
    """, (name, district, latitude, longitude))

    connection.commit()

    employee_id = cursor.lastrowid

    connection.close()

    return {
        "message": "Çalışan başarıyla eklendi!",
        "employee_id": employee_id
    }

@app.get("/employees")
def get_employees():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, district, latitude, longitude
        FROM employees
    """)

    employees = cursor.fetchall()

    connection.close()

    return [
        {
            "id": employee[0],
            "name": employee[1],
            "district": employee[2],
            "latitude": employee[3],
            "longitude": employee[4]
        }
        for employee in employees
    ]

@app.post("/services")
def create_service(
    name: str,
    district: str,
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
    capacity: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO services (
            name,
            district,
            start_latitude,
            start_longitude,
            end_latitude,
            end_longitude,
            capacity
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        district,
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude,
        capacity
    ))

    connection.commit()

    service_id = cursor.lastrowid

    connection.close()

    return {
        "message": "Servis başarıyla eklendi!",
        "service_id": service_id
    }

@app.get("/services")
def get_services():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            district,
            start_latitude,
            start_longitude,
            end_latitude,
            end_longitude,
            capacity
        FROM services
    """)

    services = cursor.fetchall()

    connection.close()

    return [
        {
            "id": service[0],
            "name": service[1],
            "district": service[2],
            "start_latitude": service[3],
            "start_longitude": service[4],
            "end_latitude": service[5],
            "end_longitude": service[6],
            "capacity": service[7]
        }
        for service in services
    ]

@app.post("/employees/{employee_id}/assign-service")
def assign_employee_to_service(employee_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    # Çalışanı bul
    cursor.execute("""
        SELECT id, name, district
        FROM employees
        WHERE id = ?
    """, (employee_id,))

    employee = cursor.fetchone()

    if employee is None:
        connection.close()
        return {
            "message": "Çalışan bulunamadı."
        }

    employee_id = employee[0]
    employee_name = employee[1]
    employee_district = employee[2]

    # Aynı ilçedeki servisleri bul
    cursor.execute("""
        SELECT id, name, capacity
        FROM services
        WHERE district = ?
    """, (employee_district,))

    services = cursor.fetchall()

    if not services:
        connection.close()
        return {
            "message": f"{employee_district} ilçesinde uygun servis bulunamadı."
        }

    # Servisleri tek tek kontrol et
    for service in services:
        service_id = service[0]
        service_name = service[1]
        service_capacity = service[2]

        # Bu servise atanmış kaç çalışan var?
        cursor.execute("""
            SELECT COUNT(*)
            FROM employees
            WHERE service_id = ?
        """, (service_id,))

        employee_count = cursor.fetchone()[0]

        # Kapasite uygunsa çalışanı ata
        if employee_count < service_capacity:
            cursor.execute("""
                UPDATE employees
                SET service_id = ?
                WHERE id = ?
            """, (service_id, employee_id))

            connection.commit()
            connection.close()

            return {
                "message": "Çalışan servise başarıyla atandı.",
                "employee_id": employee_id,
                "employee_name": employee_name,
                "service_id": service_id,
                "service_name": service_name
            }

    connection.close()

    return {
        "message": "Uygun kapasiteye sahip servis bulunamadı."
    }

@app.post("/employees/assign-all")
def assign_all_employees():

    connection = get_connection()
    cursor = connection.cursor()

    # Önce bütün çalışanların mevcut servis atamalarını sıfırla
    cursor.execute("""
        UPDATE employees
        SET service_id = NULL
    """)

    # Bütün çalışanları tekrar getir
    cursor.execute("""
        SELECT id, name, district
        FROM employees
        ORDER BY id
    """)

    employees = cursor.fetchall()

    assigned_employees = []
    unassigned_employees = []

    for employee in employees:
        employee_id = employee[0]
        employee_name = employee[1]
        employee_district = employee[2]

        # Çalışanın ilçesindeki servisleri bul
        cursor.execute("""
            SELECT id, name, capacity
            FROM services
            WHERE district = ?
        """, (employee_district,))

        services = cursor.fetchall()

        assigned = False

        for service in services:
            service_id = service[0]
            service_name = service[1]
            service_capacity = service[2]

            # Serviste kaç çalışan var?
            cursor.execute("""
                SELECT COUNT(*)
                FROM employees
                WHERE service_id = ?
            """, (service_id,))

            employee_count = cursor.fetchone()[0]

            # Kapasite varsa ata
            if employee_count < service_capacity:

                cursor.execute("""
                    UPDATE employees
                    SET service_id = ?
                    WHERE id = ?
                """, (service_id, employee_id))

                assigned_employees.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "service_id": service_id,
                    "service_name": service_name
                })

                assigned = True
                break

        if not assigned:
            unassigned_employees.append({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "district": employee_district
            })

    connection.commit()
    connection.close()

    return {
        "message": "Çalışan dağıtımı tamamlandı.",
        "assigned_employees": assigned_employees,
        "unassigned_employees": unassigned_employees
    }

@app.get("/services/{service_id}/employees")
def get_service_employees(service_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    # Önce servisin var olup olmadığını kontrol et
    cursor.execute("""
        SELECT id, name, district
        FROM services
        WHERE id = ?
    """, (service_id,))

    service = cursor.fetchone()

    if service is None:
        connection.close()

        return {
            "message": "Servis bulunamadı."
        }

    # Bu servise atanmış çalışanları getir
    cursor.execute("""
        SELECT
            id,
            name,
            district,
            latitude,
            longitude
        FROM employees
        WHERE service_id = ?
    """, (service_id,))

    employees = cursor.fetchall()

    connection.close()

    return {
        "service": {
            "id": service[0],
            "name": service[1],
            "district": service[2]
        },
        "employees": [
            {
                "id": employee[0],
                "name": employee[1],
                "district": employee[2],
                "latitude": employee[3],
                "longitude": employee[4]
            }
            for employee in employees
        ]
    }

@app.get("/distance")
def calculate_distance(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float
):
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start_longitude},{start_latitude};"
        f"{end_longitude},{end_latitude}"
        f"?overview=false"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return {
            "message": "Mesafe hesaplanamadı."
        }

    data = response.json()

    route = data["routes"][0]

    distance_km = route["distance"] / 1000
    duration_minutes = route["duration"] / 60

    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": round(duration_minutes, 2)
    }

@app.get("/services/{service_id}/distance-matrix")
def get_distance_matrix(service_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    # Servisi kontrol et
    cursor.execute("""
        SELECT id, name, start_latitude, start_longitude
        FROM services
        WHERE id = ?
    """, (service_id,))

    service = cursor.fetchone()

    if service is None:
        connection.close()

        return {
            "message": "Servis bulunamadı."
        }

    # Servise atanmış çalışanları getir
    cursor.execute("""
        SELECT id, name, latitude, longitude
        FROM employees
        WHERE service_id = ?
    """, (service_id,))

    employees = cursor.fetchall()

    connection.close()

    if not employees:
        return {
            "message": "Bu servise atanmış çalışan bulunmuyor."
        }

    # Servis + çalışan noktalarını oluştur
    locations = [
        {
            "id": service[0],
            "name": service[1],
            "latitude": service[2],
            "longitude": service[3],
            "type": "service"
        }
    ]

    for employee in employees:
        locations.append({
            "id": employee[0],
            "name": employee[1],
            "latitude": employee[2],
            "longitude": employee[3],
            "type": "employee"
        })

    # OSRM için koordinatları oluştur
    coordinates = ";".join(
        f"{location['longitude']},{location['latitude']}"
        for location in locations
    )

    url = (
        f"https://router.project-osrm.org/table/v1/driving/"
        f"{coordinates}"
        f"?annotations=distance,duration"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return {
            "message": "Mesafe matrisi oluşturulamadı."
        }

    data = response.json()





    # Metreyi kilometreye çevir
    distance_matrix = [
        [
            distance / 1000
            for distance in row
        ]
        for row in data["distances"]
    ]

    return {
        "service": {
            "id": service[0],
            "name": service[1]
        },
        "locations": locations,
        "distance_matrix_km": distance_matrix
    }

@app.get("/services/{service_id}/optimal-route")
def get_optimal_route(service_id: int):

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT
        id,
        name,
        start_latitude,
        start_longitude,
        end_latitude,
        end_longitude
    FROM services
    WHERE id = ?
""", (service_id,))

    service = cursor.fetchone()

    if service is None:
        connection.close()

        return {
            "message": "Servis bulunamadı."
        }

    # Servise atanmış çalışanları getir
    cursor.execute("""
        SELECT id, name, latitude, longitude
        FROM employees
        WHERE service_id = ?
    """, (service_id,))

    employees = cursor.fetchall()

    connection.close()

    if not employees:
        return {
            "message": "Bu servise atanmış çalışan bulunmuyor."
        }

    # Servis bilgileri
    service_name = service[1]

    start_latitude = service[2]
    start_longitude = service[3]

    end_latitude = service[4]
    end_longitude = service[5]


    # Servis + çalışan noktaları
    locations = [
 # Başlangıç noktası
        {
            "id": service[0],
            "name": service_name,
            "latitude": start_latitude,
            "longitude": start_longitude,
            "type": "service_start"
        }
    ]


        # Çalışanları ekle
    for employee in employees:
        locations.append({
            "id": employee[0],
            "name": employee[1],
            "latitude": employee[2],
            "longitude": employee[3],
            "type": "employee"
        })

        # Bitiş noktası SADECE BİR KEZ ve EN SONA eklenir
        locations.append({
            "id": service[0],
            "name": f"{service_name} Bitiş",
            "latitude": end_latitude,
            "longitude": end_longitude,
            "type": "service_end"
        })


    # OSRM mesafe matrisi
    coordinates = ";".join(
        f"{location['longitude']},{location['latitude']}"
        for location in locations
    )

    url = (
        f"https://router.project-osrm.org/table/v1/driving/"
        f"{coordinates}"
        f"?annotations=distance"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return {
            "message": "Mesafe matrisi alınamadı."
        }

    data = response.json()

    # Metre → kilometre
    distance_matrix = [
        [
            distance / 1000
            for distance in row
        ]
        for row in data["distances"]
    ]

    route, total_distance = optimize_route(
    distance_matrix
    )
    # İyileştirilmiş rotanın toplam mesafesini tekrar hesapla
    total_distance = calculate_route_distance(
        route,
        distance_matrix
    )

    # Route indexlerini gerçek çalışan bilgilerine çevir
    ordered_locations = []


    for index in route:
        ordered_locations.append(locations[index])


    route_coordinates = ";".join(
        f"{location['longitude']},{location['latitude']}"
        for location in ordered_locations
    )

    route_url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{route_coordinates}"
        f"?overview=full&geometries=geojson"
    )

    route_response = requests.get(route_url)

    if route_response.status_code != 200:
        return {
            "message": "Rota çizgisi alınamadı."
        }

    route_data = route_response.json()

    geometry = route_data["routes"][0]["geometry"]


    return {
        "service": {
            "id": service[0],
            "name": service[1]
        },
        "route": ordered_locations,
        "total_distance_km": round(total_distance, 2),
        "geometry": geometry
    }

@app.post("/assign-employees")
def assign_employees_to_services():

    connection = get_connection()
    cursor = connection.cursor()

    # Önce bütün çalışanların mevcut servis atamasını temizle
    cursor.execute("""
        UPDATE employees
        SET service_id = NULL
    """)

    # Çalışanları getir
    cursor.execute("""
        SELECT id, name, district
        FROM employees
        ORDER BY id
    """)

    employees = cursor.fetchall()

    assigned = []
    unassigned = []

    for employee in employees:

        employee_id = employee[0]
        employee_name = employee[1]
        employee_district = employee[2]

        # Çalışanın ilçesindeki servisleri getir
        cursor.execute("""
            SELECT id, name, capacity
            FROM services
            WHERE district = ?
            ORDER BY id
        """, (employee_district,))

        services = cursor.fetchall()

        assigned_service = None

        # Servisleri kontrol et
        for service in services:

            service_id = service[0]
            service_name = service[1]
            capacity = service[2]

            # Bu serviste kaç çalışan var?
            cursor.execute("""
                SELECT COUNT(*)
                FROM employees
                WHERE service_id = ?
            """, (service_id,))

            current_employee_count = cursor.fetchone()[0]

            # Kapasite uygunsa çalışanı ata
            if current_employee_count < capacity:

                cursor.execute("""
                    UPDATE employees
                    SET service_id = ?
                    WHERE id = ?
                """, (service_id, employee_id))

                assigned_service = {
                    "service_id": service_id,
                    "service_name": service_name
                }

                break

        # Atama sonucu
        if assigned_service:

            assigned.append({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "district": employee_district,
                "service": assigned_service
            })

        else:

            unassigned.append({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "district": employee_district,
                "reason": "Uygun servis veya boş kapasite bulunamadı."
            })

    connection.commit()
    connection.close()

    return {
        "assigned": assigned,
        "unassigned": unassigned
    }