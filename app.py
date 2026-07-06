import os
import time
import json
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import math
import re
from collections import Counter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Инициализация геокодера
geolocator = Nominatim(user_agent="chishmy_school_bus_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# ============================================================
# БАЗА ШКОЛ ЧИШМИНСКОГО РАЙОНА
# Координаты можно уточнить на Яндекс.Картах или Google Maps
# ============================================================
SCHOOLS_BY_CITY = {
    # Посёлок Чишмы
    "чишмы": [
        {"name": "Школа №1 п. Чишмы", "lat": 54.587323, "lon": 55.382960, "address": "ул. Ленина, 39"},
        {"name": "Школа №2 п. Чишмы", "lat": 54.576120, "lon": 55.372459, "address": "Колхозная улица, 24"},
        {"name": "Школа №3 п. Чишмы", "lat": 54.588521, "lon": 55.374893, "address": "улица Кирова, 5"},
        {"name": "Школа №4 п. Чишмы", "lat": 54.577237, "lon": 55.340605, "address": "улица Мира, 21"},
        {"name": "Школа №5 п. Чишмы", "lat": 54.593523, "lon": 55.402877, "address": "улица Ленина, 101А"},
    ],
    
    # Село Алкино-2
    "алкино-2": [
        {"name": "Школа с. Алкино-2", "lat": 54.6562, "lon": 55.5863, "address": "ул. Школьная, 1"},
    ],
    "алкино": [
        {"name": "Школа с. Алкино-2", "lat": 54.6562, "lon": 55.5863, "address": "ул. Школьная, 1"},
    ],
    
    # Село Аминево
    "аминево": [
        {"name": "Школа с. Аминево", "lat": 54.5534, "lon": 55.4189, "address": "ул. Центральная, 3"},
    ],
    
    # Село Арсланово
    "арсланово": [
        {"name": "Школа с. Арсланово", "lat": 54.6321, "lon": 55.3678, "address": "ул. Школьная, 2"},
    ],
    
    # Село Биккулово
    "биккулово": [
        {"name": "Школа с. Биккулово", "lat": 54.5597, "lon": 55.3192, "address": "ул. Молодёжная, 7"},
    ],
    
    # Село Дмитриевка
    "дмитриевка": [
        {"name": "Школа с. Дмитриевка", "lat": 54.6189, "lon": 55.4356, "address": "ул. Советская, 12"},
    ],
    
    # Село Еремеево
    "еремеево": [
        {"name": "Школа с. Еремеево", "lat": 54.5715, "lon": 55.3327, "address": "ул. Новая, 5"},
    ],
    
    # Село Кара-Якупово
    "кара-якупово": [
        {"name": "Школа с. Кара-Якупово", "lat": 54.5468, "lon": 55.4532, "address": "ул. Школьная, 1"},
    ],
    
    # Село Сафарово
    "сафарово": [
        {"name": "Школа с. Сафарово", "lat": 54.5834, "lon": 55.4291, "address": "ул. Центральная, 8"},
    ],
    
    # Село Шингак-Куль
    "шингак-куль": [
        {"name": "Школа с. Шингак-Куль", "lat": 54.5268, "lon": 55.3672, "address": "ул. Школьная, 4"},
    ],
    "шингаккуль": [
        {"name": "Школа с. Шингак-Куль", "lat": 54.5268, "lon": 55.3672, "address": "ул. Школьная, 4"},
    ],
    
    # Село Ябалаклы
    "ябалаклы": [
        {"name": "Школа с. Ябалаклы", "lat": 54.5893, "lon": 55.2798, "address": "ул. Молодёжная, 3"},
    ],
    
    # Село Ибрагимово
    "ибрагимово": [
        {"name": "Школа с. Ибрагимово", "lat": 54.5987, "lon": 55.4563, "address": "ул. Ленина, 10"},
    ],
    
    # Село Уразбахты
    "уразбахты": [
        {"name": "Школа с. Уразбахты", "lat": 54.5645, "lon": 55.2991, "address": "ул. Школьная, 6"},
    ],
    
    # Село Бахчи
    "бахчи": [
        {"name": "Школа с. Бахчи", "lat": 54.5212, "lon": 55.3893, "address": "ул. Центральная, 15"},
    ],
    
    # Село Кляшево
    "кляшево": [
        {"name": "Школа с. Кляшево", "lat": 54.5547, "lon": 55.4965, "address": "ул. Школьная, 3"},
    ],
    
    # Село Удряк
    "удряк": [
        {"name": "Школа с. Удряк", "lat": 54.5376, "lon": 55.2341, "address": "ул. Новая, 2"},
    ],
    
    # Деревня Верхние Чишмы (Чишмы Верхние)
    "верхние чишмы": [
        {"name": "Школа д. Верхние Чишмы", "lat": 54.5978, "lon": 55.4012, "address": "ул. Садовая, 5"},
    ],
    
    # Село Нижние Чишмы
    "нижние чишмы": [
        {"name": "Школа с. Нижние Чишмы", "lat": 54.5856, "lon": 55.3745, "address": "ул. Речная, 8"},
    ],
}

# Расширенный список для поиска "Чишминский район" как общий ключ
# Сюда попадают все школы района
CHISHMY_DISTRICT_KEYWORDS = [
    "чишминский", "чишмы", "чишминского", "р-н чишминский"
]

def extract_city_from_address(address):
    """
    Извлекает название населённого пункта из адреса через геокодирование.
    """
    try:
        location = geocode(address, addressdetails=True, timeout=10)
        if location and location.raw.get('address'):
            addr = location.raw['address']
            
            # Для сельской местности ищем: village, town, city, hamlet
            city = (addr.get('city') or 
                   addr.get('town') or 
                   addr.get('village') or 
                   addr.get('hamlet') or
                   addr.get('municipality') or 
                   addr.get('county'))
            
            if city:
                return city.lower()
            
            # Запасной вариант из display_name
            display_name = location.raw.get('display_name', '')
            parts = [p.strip() for p in display_name.split(',')]
            if len(parts) >= 2:
                # В сельской местности название нас.пункта часто второе
                candidate = parts[0].lower() if parts[0] else None
                if candidate and not any(kw in candidate for kw in ['россия', 'башкортостан', 'республика']):
                    return candidate
    except Exception as e:
        print(f"Ошибка определения города для '{address}': {e}")
    return None

def extract_city_simple(address):
    """
    Извлекает населённый пункт из текста адреса.
    Поддерживает форматы:
    - "с. Алкино-2, ул. Школьная"
    - "п. Чишмы, ул. Ленина"
    - "д. Верхние Чишмы"
    - "Чишминский р-н, с. Сафарово"
    """
    # Убираем индекс и страну
    address = re.sub(r'\d{6}.*$', '', address)
    address = re.sub(r'(россия|башкортостан|республика\s+башкортостан)', '', address, flags=re.IGNORECASE)
    
    # Шаблоны для нас. пунктов
    patterns = [
        # с. Название, село Название
        r'(?:с\.|село)\s*([А-ЯЁ][а-яё\-0-9]+(?:\s+[А-ЯЁ][а-яё\-0-9]+)*)',
        # п. Название, посёлок Название, пгт Название
        r'(?:п\.|пос\.|посёлок|поселок|пгт\.?)\s*([А-ЯЁ][а-яё\-0-9]+(?:\s+[А-ЯЁ][а-яё\-0-9]+)*)',
        # д. Название, деревня Название
        r'(?:д\.|дер\.|деревня)\s*([А-ЯЁ][а-яё\-0-9]+(?:\s+[А-ЯЁ][а-яё\-0-9]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, address, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    
    # Если адрес начинается просто с названия: "Чишмы, ул. Ленина"
    parts = address.split(',')
    first_part = parts[0].strip()
    
    # Убираем возможные префиксы
    for prefix in ['г.', 'город', 'п.', 'пос.', 'с.', 'д.', 'р-н', 'район']:
        if first_part.lower().startswith(prefix):
            first_part = first_part[len(prefix):].strip()
    
    if first_part and len(first_part) > 1:
        return first_part.lower()
    
    return None

def is_chishmy_district(address):
    """
    Проверяет, относится ли адрес к Чишминскому району.
    """
    address_lower = address.lower()
    
    # Ключевые слова Чишминского района
    chishmy_keywords = [
        'чишминский', 'чишмы', 'чишм.', 'алкино', 'аминево', 'арсланово',
        'биккулово', 'дмитриевка', 'еремеево', 'кара-якупово', 'сафарово',
        'шингак-куль', 'шингаккуль', 'ябалаклы', 'ибрагимово', 'уразбахты',
        'бахчи', 'кляшево', 'удряк', 'верхние чишмы', 'нижние чишмы'
    ]
    
    for keyword in chishmy_keywords:
        if keyword in address_lower:
            return True
    
    return False

def determine_main_settlement(addresses):
    """
    Определяет основной населённый пункт по списку адресов.
    Возвращает (название_нас_пункта, все_нас_пункты).
    """
    settlements = []
    all_found = set()
    
    for addr in addresses[:15]:
        # Сначала пробуем простой метод (быстрее)
        city = extract_city_simple(addr)
        if city:
            settlements.append(city)
            all_found.add(city)
        
        # Проверяем принадлежность к Чишминскому району
        if not is_chishmy_district(addr):
            # Если адрес не из Чишминского района, пробуем геокодирование
            city = extract_city_from_address(addr)
            if city:
                settlements.append(city)
                all_found.add(city)
    
    if not settlements:
        return None, set()
    
    # Самый частый нас. пункт
    counter = Counter(settlements)
    main = counter.most_common(1)[0][0]
    
    return main, all_found

def find_schools_for_settlements(main_settlement, all_settlements):
    """
    Находит школы для указанных населённых пунктов.
    Ищет и в конкретных ключах, и в общем списке Чишминского района.
    """
    found_schools = []
    seen_schools = set()
    
    # Все нас. пункты для поиска
    search_terms = list(all_settlements)
    if main_settlement:
        search_terms.insert(0, main_settlement)
    
    for term in search_terms:
        term_lower = term.lower().strip()
        
        # Прямой поиск
        if term_lower in SCHOOLS_BY_CITY:
            for school in SCHOOLS_BY_CITY[term_lower]:
                key = f"{school['lat']}_{school['lon']}"
                if key not in seen_schools:
                    seen_schools.add(key)
                    found_schools.append(school)
        
        # Частичный поиск
        for city_key in SCHOOLS_BY_CITY:
            if city_key in term_lower or term_lower in city_key:
                for school in SCHOOLS_BY_CITY[city_key]:
                    key = f"{school['lat']}_{school['lon']}"
                    if key not in seen_schools:
                        seen_schools.add(key)
                        found_schools.append(school)
    
    # Если ничего не нашли, но адреса в Чишминском районе - выдаём все школы района
    if not found_schools:
        for city_key, schools in SCHOOLS_BY_CITY.items():
            for school in schools:
                key = f"{school['lat']}_{school['lon']}"
                if key not in seen_schools:
                    seen_schools.add(key)
                    found_schools.append(school)
    
    return found_schools

def solve_tsp_duration(duration_matrix, start=0):
    """Решение TSP на основе матрицы длительностей."""
    size = len(duration_matrix)
    if size <= 2:
        return list(range(size))
    
    visited = [False] * size
    order = [start]
    visited[start] = True
    cur = start
    
    for _ in range(size-1):
        next_idx = None
        min_d = float('inf')
        for i in range(size):
            if not visited[i] and duration_matrix[cur][i] < min_d:
                min_d = duration_matrix[cur][i]
                next_idx = i
        if next_idx is None:
            break
        order.append(next_idx)
        visited[next_idx] = True
        cur = next_idx
    
    # 2-opt улучшение
    improved = True
    while improved:
        improved = False
        for i in range(1, size-2):
            for j in range(i+1, size-2):
                a, b = order[i-1], order[i]
                c, d = order[j], order[j+1]
                if duration_matrix[a][b] + duration_matrix[c][d] > \
                   duration_matrix[a][c] + duration_matrix[b][d]:
                    order[i:j+1] = reversed(order[i:j+1])
                    improved = True
        if not improved:
            break
    
    return order

def geocode_address(address):
    """Геокодирование одного адреса, возвращает (lat, lon) или None."""
    try:
        # Добавляем уточнение для Чишминского района
        if not any(region in address.lower() for region in ['башкортостан', 'чишминский']):
            search_address = f"{address}, Чишминский район, Башкортостан"
        else:
            search_address = address
            
        location = geocode(search_address, timeout=10)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Ошибка геокодирования '{address}': {e}")
    return None

def haversine(lat1, lon1, lat2, lon2):
    """Расстояние между точками в км."""
    R = 6371
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Обработка Excel файла и геокодирование адресов."""
    if 'file' not in request.files:
        return jsonify({"error": "Файл не найден"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({"error": "Поддерживаются только файлы Excel (.xlsx, .xls)"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath)
        df.columns = [c.strip() for c in df.columns]
        addr_col = next((c for c in df.columns if c.lower() in ['адрес', 'address']), None)
        name_col = next((c for c in df.columns if c.lower() in ['имя', 'name', 'фио']), None)
        phone_col = next((c for c in df.columns if c.lower() in ['телефон', 'phone', 'тел']), None)

        if not addr_col:
            return jsonify({"error": "Не найден столбец 'Адрес'"}), 400

        students = []
        addresses_only = []
        geocoded_count = 0
        failed_addresses = []
        
        for idx, row in df.iterrows():
            address = str(row[addr_col]).strip()
            if not address or address == 'nan':
                continue
            addresses_only.append(address)
            name = str(row[name_col]).strip() if name_col and pd.notna(row[name_col]) else ""
            phone = str(row[phone_col]).strip() if phone_col and pd.notna(row[phone_col]) else ""

            coords = geocode_address(address)
            if coords:
                students.append({
                    "id": idx,
                    "address": address,
                    "name": name,
                    "phone": phone,
                    "lat": coords[0],
                    "lon": coords[1]
                })
                geocoded_count += 1
            else:
                failed_addresses.append(address)
                print(f"Не удалось геокодировать адрес: {address}")

        # Определяем населённые пункты
        main_settlement, all_settlements = determine_main_settlement(addresses_only)
        
        # Находим школы
        nearby_schools = find_schools_for_settlements(main_settlement, all_settlements)
        
        # Если школы не найдены, но есть ученики - ищем ближайшие по расстоянию
        if not nearby_schools and students:
            all_schools = []
            for city_schools in SCHOOLS_BY_CITY.values():
                all_schools.extend(city_schools)
            
            if all_schools:
                avg_lat = sum(s['lat'] for s in students) / len(students)
                avg_lon = sum(s['lon'] for s in students) / len(students)
                
                # Уменьшенный радиус для сельской местности - 15 км
                radius_km = 15.0
                for school in all_schools:
                    d = haversine(avg_lat, avg_lon, school['lat'], school['lon'])
                    if d <= radius_km:
                        nearby_schools.append(school)

        # Убираем дубликаты школ
        seen = set()
        unique_schools = []
        for school in nearby_schools:
            key = (school['lat'], school['lon'])
            if key not in seen:
                seen.add(key)
                unique_schools.append(school)

        # Формируем сообщение о результате
        message = f"✅ Загружено: {len(students)} учеников"
        if main_settlement:
            message += f" | Нас. пункт: {main_settlement.title()}"
        if failed_addresses:
            message += f" | ⚠️ Не найдено: {len(failed_addresses)} адресов"

        return jsonify({
            "students": students,
            "schools": unique_schools,
            "detected_city": main_settlement,
            "all_settlements": list(all_settlements),
            "geocoded_count": geocoded_count,
            "failed_count": len(failed_addresses),
            "message": message
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/optimize', methods=['POST'])
def optimize_route():
    """Расчёт оптимального маршрута с помощью OSRM."""
    data = request.get_json()
    school = data.get('school')
    students = data.get('students')

    if not school or not students:
        return jsonify({"error": "Не указана школа или ученики"}), 400

    school_coord = [school['lat'], school['lon']]
    all_coords = [school_coord] + [[s['lat'], s['lon']] for s in students] + [school_coord]

    coords_param = ";".join([f"{lon},{lat}" for lat, lon in all_coords])
    osrm_table_url = f"http://router.project-osrm.org/table/v1/driving/{coords_param}"
    params = {"annotations": "duration"}
    
    try:
        resp = requests.get(osrm_table_url, params=params, timeout=30)
        resp.raise_for_status()
        table_data = resp.json()
        durations = table_data.get('durations')
        if not durations:
            raise ValueError("Пустая матрица длительностей")
    except Exception as e:
        return jsonify({"error": f"Ошибка запроса OSRM: {str(e)}"}), 500

    n = len(all_coords)
    INF = 1e9
    for i in range(n):
        for j in range(n):
            if durations[i][j] is None or (durations[i][j] == 0 and i != j):
                durations[i][j] = INF

    m = n - 1
    order = solve_tsp_duration(durations[:m][:m], start=0)
    route_indices = order + [0]
    ordered_coords = [all_coords[i] for i in route_indices]

    return jsonify({
        "route": ordered_coords,
        "stop_count": len(students),
        "total_points": len(route_indices)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)