-- 1. Очистка старых данных (чтобы не было дубликатов при повторном запуске)
DELETE FROM logistics_route;
DELETE FROM logistics_vehicle;

-- 3. Создание Машин (Таблица logistics_vehicle)
INSERT INTO logistics_vehicle (id, plate_number, status, marker_color, driver_id)
VALUES 
(1, '70 A 123 AA', 'MOVING', '#f97316', 101), -- Оранжевый
(2, '01 Z 888 ZZ', 'MOVING', '#3b82f6', 102), -- Синий
(3, '30 X 555 YY', 'IDLE', '#22c55e', 103);   -- Зеленый

-- 4. Создание Маршрутов (Таблица logistics_route)
-- В поле path_geojson вставляем JSON строку с координатами (Ташкент)

-- Маршрут 1: Круговой (Оранжевый грузовик)
INSERT INTO logistics_route (id, created_at, path_geojson, estimated_time, is_active, vehicle_id)
VALUES (
    1, 
    '2025-12-06 10:00:00', 
    '{"type": "LineString", "coordinates": [[41.2995, 69.2401], [41.3020, 69.2450], [41.3050, 69.2420], [41.3040, 69.2380], [41.2995, 69.2401]]}', 
    45, 
    1, -- true
    1
);

-- Маршрут 2: Длинный прямой (Синий грузовик)
INSERT INTO logistics_route (id, created_at, path_geojson, estimated_time, is_active, vehicle_id)
VALUES (
    2, 
    '2025-12-06 10:05:00', 
    '{"type": "LineString", "coordinates": [[41.2800, 69.2200], [41.2850, 69.2250], [41.2900, 69.2300], [41.2950, 69.2350], [41.3000, 69.2400], [41.2800, 69.2200]]}', 
    120, 
    1, -- true
    2
);

-- Маршрут 3: Короткий (Зеленый грузовик, почти стоит)
INSERT INTO logistics_route (id, created_at, path_geojson, estimated_time, is_active, vehicle_id)
VALUES (
    3, 
    '2025-12-06 10:10:00', 
    '{"type": "LineString", "coordinates": [[41.3100, 69.2500], [41.3120, 69.2520], [41.3100, 69.2500]]}', 
    10, 
    1, -- true
    3
);