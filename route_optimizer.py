def nearest_neighbor(distance_matrix):
    """
    Nearest Neighbor algoritması.

    0 = servis başlangıç noktası
    1, 2, 3... = çalışanlar
    """

    number_of_locations = len(distance_matrix)

    # Servisten başlıyoruz
    current_location = 0

    # Başlangıç noktası rotaya ekleniyor
    route = [0]

    # Henüz ziyaret edilmeyen noktalar
    unvisited = set(range(1, number_of_locations))

    total_distance = 0

    while unvisited:

        nearest_location = None
        nearest_distance = float("inf")

        # Bulunduğumuz noktadan
        # en yakın çalışanı bul
        for location in unvisited:

            distance = distance_matrix[current_location][location]

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_location = location

        # En yakın çalışanı rotaya ekle
        route.append(nearest_location)

        total_distance += nearest_distance

        # Artık bu çalışan ziyaret edildi
        unvisited.remove(nearest_location)

        # Yeni bulunduğumuz nokta
        current_location = nearest_location



    return route, total_distance

def two_opt(route, distance_matrix):

    best_route = route[:]
    best_distance = calculate_route_distance(
        best_route,
        distance_matrix
    )

    improved = True

    while improved:

        improved = False

        for i in range(1, len(best_route) - 1):

            for j in range(i + 1, len(best_route) + 1):

                new_route = (
                    best_route[:i]
                    + best_route[i:j][::-1]
                    + best_route[j:]
                )

                new_distance = calculate_route_distance(
                    new_route,
                    distance_matrix
                )

                if new_distance < best_distance:

                    best_route = new_route
                    best_distance = new_distance
                    improved = True

    return best_route

def calculate_route_distance(route, distance_matrix):

    total_distance = 0

    for i in range(len(route) - 1):

        current = route[i]
        next_location = route[i + 1]

        total_distance += distance_matrix[
            current
        ][
            next_location
        ]

    return total_distance

def nearest_neighbor_with_first(
    distance_matrix,
    first_employee
):

    number_of_locations = len(distance_matrix)

    route = [0, first_employee]

    unvisited = set(
        range(1, number_of_locations)
    )

    unvisited.remove(first_employee)

    current_location = first_employee

    while unvisited:

        nearest_location = min(
            unvisited,
            key=lambda location:
                distance_matrix[
                    current_location
                ][
                    location
                ]
        )

        route.append(nearest_location)

        unvisited.remove(nearest_location)

        current_location = nearest_location

    return route

def optimize_route(distance_matrix):
    """
    Index yapısı:

    0 = servis başlangıç noktası
    1, 2, 3... = çalışanlar
    son index = servis bitiş noktası

    Rota:
    START -> çalışanlar -> END

    START ve END sabittir.
    """

    number_of_locations = len(distance_matrix)

    # START + END bile yoksa
    if number_of_locations == 0:
        return [], 0

    # Sadece START varsa
    if number_of_locations == 1:
        return [0], 0

    # Son nokta END
    end_index = number_of_locations - 1

    # START ve END arasında çalışan yoksa
    if number_of_locations == 2:
        return [0, end_index], distance_matrix[0][end_index]

    # Çalışan sayısı:
    # START ve END çıkarılıyor
    number_of_employees = number_of_locations - 2


    # ==================================================
    # 15 ÇALIŞANA KADAR EXACT OPTİMİZASYON
    # ==================================================

    if number_of_employees <= 15:

        dp = {}
        parent = {}

        # İlk çalışan seçenekleri
        for employee in range(1, end_index):

            mask = 1 << (employee - 1)

            dp[(mask, employee)] = (
                distance_matrix[0][employee]
            )

            parent[(mask, employee)] = 0


        # Çalışan kombinasyonlarını dene
        for mask in range(
            1,
            1 << number_of_employees
        ):

            for last in range(
                1,
                end_index
            ):

                bit_last = 1 << (last - 1)

                if not (mask & bit_last):
                    continue

                state = (mask, last)

                if state not in dp:
                    continue

                current_distance = dp[state]


                # Henüz ziyaret edilmemiş çalışan
                for next_employee in range(
                    1,
                    end_index
                ):

                    bit = 1 << (
                        next_employee - 1
                    )

                    if mask & bit:
                        continue

                    new_mask = mask | bit

                    new_distance = (
                        current_distance
                        + distance_matrix[
                            last
                        ][
                            next_employee
                        ]
                    )

                    new_state = (
                        new_mask,
                        next_employee
                    )

                    if (
                        new_state not in dp
                        or new_distance
                        < dp[new_state]
                    ):

                        dp[new_state] = (
                            new_distance
                        )

                        parent[new_state] = last


        # Bütün çalışanlar ziyaret edildi
        full_mask = (
            1 << number_of_employees
        ) - 1


        # Son çalışandan END noktasına
        # gitme mesafesini de hesaba kat
        best_last = None
        best_distance = float("inf")

        for employee in range(
            1,
            end_index
        ):

            state = (
                full_mask,
                employee
            )

            if state not in dp:
                continue

            total_distance = (
                dp[state]
                + distance_matrix[
                    employee
                ][
                    end_index
                ]
            )

            if total_distance < best_distance:

                best_distance = total_distance
                best_last = employee


        # Rotayı geriye doğru oluştur
        reverse_route = []

        mask = full_mask
        current = best_last

        while current != 0:

            reverse_route.append(current)

            previous = parent[
                (mask, current)
            ]

            mask = (
                mask
                & ~(1 << (current - 1))
            )

            current = previous


        # START + çalışanlar + END
        route = (
            [0]
            + reverse_route[::-1]
            + [end_index]
        )

        return route, best_distance


    # ==================================================
    # 15'TEN FAZLA ÇALIŞAN İÇİN
    # NEAREST NEIGHBOR
    # END NOKTASI SABİT
    # ==================================================

    route = [0]

    current_location = 0

    # END dahil değil
    unvisited = set(
        range(1, end_index)
    )

    while unvisited:

        nearest_location = min(
            unvisited,
            key=lambda location:
                distance_matrix[
                    current_location
                ][
                    location
                ]
        )

        route.append(nearest_location)

        unvisited.remove(
            nearest_location
        )

        current_location = (
            nearest_location
        )


    # END her zaman en sona
    route.append(end_index)


    # Endpointleri sabit tutan 2-opt
    improved = True

    while improved:

        improved = False

        best_distance = (
            calculate_route_distance(
                route,
                distance_matrix
            )
        )

        # 0 = START değişmeyecek
        # son = END değişmeyecek
        for i in range(
            1,
            len(route) - 2
        ):

            for j in range(
                i + 1,
                len(route)
            ):

                new_route = (
                    route[:i]
                    + route[i:j][::-1]
                    + route[j:]
                )

                new_distance = (
                    calculate_route_distance(
                        new_route,
                        distance_matrix
                    )
                )

                if (
                    new_distance
                    < best_distance
                ):

                    route = new_route
                    best_distance = (
                        new_distance
                    )

                    improved = True
                    break

            if improved:
                break


    total_distance = (
        calculate_route_distance(
            route,
            distance_matrix
        )
    )

    return route, total_distance