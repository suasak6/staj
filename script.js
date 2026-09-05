// =====================================
// HARİTA
// =====================================

const map = L.map("map").setView(
    [41.0082, 28.9784],
    11
);
const mapContainer = document.getElementById("map");

const resizeObserver = new ResizeObserver(() => {
    map.invalidateSize();
});

resizeObserver.observe(mapContainer);

window.addEventListener("resize", () => {
    setTimeout(() => {
        map.invalidateSize();
    }, 100);
});

window.addEventListener("load", () => {
    setTimeout(() => {
        map.invalidateSize();
    }, 300);
});

window.addEventListener("resize", function () {
    setTimeout(function () {
        map.invalidateSize();
    }, 200);
});

window.addEventListener("load", function () {
    setTimeout(function () {
        map.invalidateSize();
    }, 300);
});


// OpenStreetMap

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution:
            "&copy; OpenStreetMap contributors"
    }
).addTo(map);


// =====================================
// DEĞİŞKENLER
// =====================================

let routeLine = null;

let stopMarkers = [];

let allServices = [];


// =====================================
// SERVİSLERİ GETİR
// =====================================

fetch("/services")

    .then(response => response.json())

    .then(services => {

        allServices = services;

        const select =
            document.getElementById(
                "serviceSelect"
            );


        services.forEach(service => {

            // Dropdown

            const option =
                document.createElement(
                    "option"
                );

            option.value = service.id;

            option.textContent =
                `${service.name} - ${service.district}`;

            select.appendChild(option);


            // Servis başlangıç ikonu

            const busIcon =
                L.divIcon({

                    className: "bus-icon",

                    html: "🚌",

                    iconSize: [40, 40],

                    iconAnchor: [20, 20]

                });


            const marker =
                L.marker(
                    [
                        service.start_latitude,
                        service.start_longitude
                    ],
                    {
                        icon: busIcon
                    }
                )
                .addTo(map);


            marker.bindPopup(`
                <b>${service.name}</b>
                <br>
                İlçe: ${service.district}
                <br>
                Kapasite: ${service.capacity}
            `);

        });

    })

    .catch(error => {

        console.error(
            "Servisler alınamadı:",
            error
        );

    });


// =====================================
// SERVİS SEÇİMİ
// =====================================

document
    .getElementById("serviceSelect")
    .addEventListener(
        "change",
        function () {

            const serviceId =
                this.value;


            if (!serviceId) {

                clearRoute();

                return;

            }


            const selectedService =
                allServices.find(
                    service =>
                        Number(service.id)
                        === Number(serviceId)
                );


            showServiceInfo(
                selectedService
            );


            loadOptimalRoute(
                serviceId
            );

        }
    );


// =====================================
// SERVİS BİLGİ KARTI
// =====================================

function showServiceInfo(service) {

    if (!service) {
        return;
    }


    document
        .getElementById(
            "selectedServiceCard"
        )
        .innerHTML = `

            <h3 class="service-title">
                ${service.name}
            </h3>

            <div class="service-detail">
                <span>İlçe</span>
                <strong>
                    ${service.district}
                </strong>
            </div>

            <div class="service-detail">
                <span>Kapasite</span>
                <strong>
                    ${service.capacity}
                </strong>
            </div>

        `;
}


// =====================================
// OPTİMAL ROTA
// =====================================

function loadOptimalRoute(serviceId) {

    document
        .getElementById(
            "routeInfo"
        )
        .textContent =
        "Rota hesaplanıyor...";


    fetch(
        `/services/${serviceId}/optimal-route`
    )

        .then(response => {

            if (!response.ok) {

                throw new Error(
                    "Rota alınamadı."
                );

            }

            return response.json();

        })

        .then(data => {

            // Önce eski rotayı temizle

            clearRouteLayers();


            if (
                !data.route
                || !data.geometry
            ) {

                throw new Error(
                    data.message
                    || "Rota verisi bulunamadı."
                );

            }


            let stopNumber = 1;

            let employeeCount = 0;


            // =====================================
            // DURAK MARKERLARI
            // =====================================

            data.route.forEach(
                location => {


                    // START

                    if (
                        location.type
                        === "service_start"
                        ||
                        location.type
                        === "service"
                    ) {

                        const startIcon =
                            L.divIcon({

                                className:
                                    "start-icon",

                                html: "S",

                                iconSize:
                                    [32, 32],

                                iconAnchor:
                                    [16, 16]

                            });


                        const startMarker =
                            L.marker(
                                [
                                    location.latitude,
                                    location.longitude
                                ],
                                {
                                    icon:
                                        startIcon
                                }
                            )
                            .addTo(map)
                            .bindPopup(`
                                <b>Başlangıç</b>
                                <br>
                                ${location.name}
                            `);


                        stopMarkers.push(
                            startMarker
                        );

                    }


                    // ÇALIŞAN

                    if (
                        location.type
                        === "employee"
                    ) {

                        employeeCount++;


                        const stopIcon =
                            L.divIcon({

                                className:
                                    "stop-icon",

                                html:
                                    stopNumber,

                                iconSize:
                                    [30, 30],

                                iconAnchor:
                                    [15, 15]

                            });


                        const stopMarker =
                            L.marker(
                                [
                                    location.latitude,
                                    location.longitude
                                ],
                                {
                                    icon:
                                        stopIcon
                                }
                            )
                            .addTo(map)
                            .bindPopup(`
                                <b>
                                    ${stopNumber}. Durak
                                </b>
                                <br>
                                ${location.name}
                            `);


                        stopMarkers.push(
                            stopMarker
                        );


                        stopNumber++;

                    }


                    // END

                    if (
                        location.type
                        === "service_end"
                    ) {

                        const endIcon =
                            L.divIcon({

                                className:
                                    "end-icon",

                                html: "E",

                                iconSize:
                                    [32, 32],

                                iconAnchor:
                                    [16, 16]

                            });


                        const endMarker =
                            L.marker(
                                [
                                    location.latitude,
                                    location.longitude
                                ],
                                {
                                    icon:
                                        endIcon
                                }
                            )
                            .addTo(map)
                            .bindPopup(`
                                <b>Bitiş</b>
                                <br>
                                ${location.name}
                            `);


                        stopMarkers.push(
                            endMarker
                        );

                    }

                }
            );


            // =====================================
            // OSRM GEOMETRY
            // =====================================

            const coordinates =
                data.geometry.coordinates;


            const latLngs =
                coordinates.map(
                    coordinate => [

                        coordinate[1],

                        coordinate[0]

                    ]
                );


            // =====================================
            // ROTA ÇİZGİSİ
            // =====================================

            routeLine =
                L.polyline(
                    latLngs,
                    {
                        weight: 5,
                        opacity: 0.85
                    }
                )
                .addTo(map);


            // Rotanın tamamına zoom

            map.fitBounds(
                routeLine.getBounds(),
                {
                    padding:
                        [40, 40]
                }
            );


            // =====================================
            // BİLGİLER
            // =====================================

            const distance =
                Number(
                    data.total_distance_km
                ).toFixed(2);


            document
                .getElementById(
                    "distanceValue"
                )
                .textContent =
                `${distance} km`;


            document
                .getElementById(
                    "stopCount"
                )
                .textContent =
                employeeCount;


            document
                .getElementById(
                    "routeInfo"
                )
                .innerHTML = `

                    <strong>
                        ${employeeCount}
                        durak
                    </strong>

                    &nbsp;•&nbsp;

                    ${distance} km

                `;

        })

        .catch(error => {

            console.error(
                "Rota alınamadı:",
                error
            );


            document
                .getElementById(
                    "routeInfo"
                )
                .textContent =
                "Rota oluşturulamadı.";

        });

}


// =====================================
// ESKİ ROTAYI TEMİZLE
// =====================================

function clearRouteLayers() {

    if (routeLine) {

        map.removeLayer(
            routeLine
        );

        routeLine = null;

    }


    stopMarkers.forEach(
        marker => {

            map.removeLayer(
                marker
            );

        }
    );


    stopMarkers = [];

}


function clearRoute() {

    clearRouteLayers();


    document
        .getElementById(
            "distanceValue"
        )
        .textContent = "-";


    document
        .getElementById(
            "stopCount"
        )
        .textContent = "-";


    document
        .getElementById(
            "routeInfo"
        )
        .textContent =
        "Bir servis seçin";

}


// =====================================
// ÇALIŞANLARI SERVİSLERE ATA
// =====================================

document
    .getElementById(
        "assignEmployeesButton"
    )
    .addEventListener(
        "click",
        function () {

            const button = this;


            button.disabled = true;

            button.textContent =
                "Dağıtılıyor...";


            fetch(
                "/employees/assign-all",
                {
                    method: "POST"
                }
            )

                .then(
                    response =>
                        response.json()
                )

                .then(data => {

                    const assignedCount =
                        data.assigned_employees
                            ?.length || 0;


                    const unassignedCount =
                        data.unassigned_employees
                            ?.length || 0;


                    document
                        .getElementById(
                            "statusMessage"
                        )
                        .textContent =
                        `${assignedCount} çalışan atandı, ${unassignedCount} çalışan atanamadı.`;


                    alert(
                        `${assignedCount} çalışan servislere atandı.\n`
                        +
                        `${unassignedCount} çalışan atanamadı.`
                    );

                })

                .catch(error => {

                    console.error(
                        "Çalışan dağıtım hatası:",
                        error
                    );


                    document
                        .getElementById(
                            "statusMessage"
                        )
                        .textContent =
                        "Çalışan dağıtımı başarısız.";

                })

                .finally(() => {

                    button.disabled =
                        false;

                    button.innerHTML =
                        "<span>↻</span> Çalışanları Servislere Ata";

                });

        }
    );