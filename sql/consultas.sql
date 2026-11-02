-- Consultas de análisis de los tickets de soporte de SAASCANET (SQLite)
-- Cada consulta empieza con "-- name: <nombre>" para poder ejecutarla desde el notebook.
-- Tiempo de resolución en minutos: (julianday(resuelto) - julianday(registrado)) * 24 * 60

-- name: resumen_general
-- ¿Cuántos tickets hubo y qué tan rápido se resolvieron?
SELECT
    COUNT(*)                                                         AS total_tickets,
    SUM(estatus = 'Resuelto')                                        AS resueltos,
    SUM(estatus = 'No procede')                                      AS no_procede,
    MIN(DATE(registrado))                                            AS primer_dia,
    MAX(DATE(registrado))                                            AS ultimo_dia,
    ROUND(100.0 * SUM(estatus = 'Resuelto' AND (julianday(resuelto) - julianday(registrado)) * 1440 BETWEEN 0 AND 60)
          / SUM(estatus = 'Resuelto' AND julianday(resuelto) >= julianday(registrado)), 1)
                                                                     AS pct_resuelto_en_1h,
    ROUND(100.0 * SUM(DATE(resuelto) = DATE(registrado))
          / COUNT(*), 1)                                             AS pct_mismo_dia
FROM tickets;

-- name: tickets_por_area
-- ¿Qué áreas piden más soporte?
SELECT
    area,
    COUNT(*)                                                AS tickets,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM tickets), 1) AS pct_del_total,
    COUNT(DISTINCT usuario)                                 AS usuarios_distintos
FROM tickets
GROUP BY area
ORDER BY tickets DESC;

-- name: tickets_por_tema
-- ¿Qué tipo de problemas llegan y cuánto tardan en resolverse en promedio?
-- Los tiempos solo consideran tickets resueltos con fechas válidas.
-- Ojo: el promedio se infla con casos que tardan días; en el notebook se usa también la mediana.
WITH t AS (
    SELECT tema,
           CASE WHEN estatus = 'Resuelto' AND julianday(resuelto) >= julianday(registrado)
                THEN (julianday(resuelto) - julianday(registrado)) * 1440 END AS minutos
    FROM tickets
)
SELECT
    tema,
    COUNT(*)                                                    AS tickets,
    ROUND(AVG(minutos), 0)                                      AS minutos_promedio,
    ROUND(100.0 * SUM(minutos <= 60) / COUNT(minutos), 0)       AS pct_en_1h
FROM t
GROUP BY tema
ORDER BY tickets DESC;

-- name: tema_principal_por_area
-- Para cada área, su tema más frecuente (función de ventana ROW_NUMBER)
WITH conteo AS (
    SELECT area, tema, COUNT(*) AS tickets,
           ROW_NUMBER() OVER (PARTITION BY area ORDER BY COUNT(*) DESC, tema) AS rn
    FROM tickets
    GROUP BY area, tema
)
SELECT area, tema AS tema_principal, tickets
FROM conteo
WHERE rn = 1
ORDER BY tickets DESC;

-- name: categoria_otro_formulario
-- ¿Las categorías del formulario describen bien los problemas? Peso de la opción "Otro"
SELECT
    tipo_formulario,
    COUNT(*)                                                     AS tickets,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM tickets), 1)  AS pct_del_total
FROM tickets
GROUP BY tipo_formulario
ORDER BY tickets DESC;

-- name: problemas_recurrentes
-- Usuarios que reportan el mismo tema 3 veces o más: posible falla de fondo en su equipo
SELECT
    usuario,
    area,
    tema,
    COUNT(*)              AS veces,
    MIN(DATE(registrado)) AS primera_vez,
    MAX(DATE(registrado)) AS ultima_vez
FROM tickets
GROUP BY usuario, area, tema
HAVING COUNT(*) >= 3
ORDER BY veces DESC;

-- name: tickets_por_hora
-- ¿A qué hora llegan las solicitudes?
SELECT
    CAST(STRFTIME('%H', registrado) AS INTEGER) AS hora,
    COUNT(*)                                     AS tickets
FROM tickets
GROUP BY hora
ORDER BY hora;

-- name: tickets_por_dia
-- ¿Qué día de la semana se concentra la demanda? (1 = lunes)
SELECT
    CASE STRFTIME('%w', registrado)
        WHEN '1' THEN '1 Lunes' WHEN '2' THEN '2 Martes' WHEN '3' THEN '3 Miércoles'
        WHEN '4' THEN '4 Jueves' WHEN '5' THEN '5 Viernes' ELSE '6 Fin de semana' END AS dia,
    COUNT(*) AS tickets
FROM tickets
GROUP BY dia
ORDER BY dia;

-- name: calidad_fechas
-- Calidad de datos: tickets con fecha de resolución anterior a la de registro
SELECT folio, registrado, resuelto,
       ROUND((julianday(resuelto) - julianday(registrado)) * 1440, 1) AS minutos
FROM tickets
WHERE julianday(resuelto) < julianday(registrado);

-- name: folios_faltantes
-- Calidad de datos: huecos en la secuencia de folios (CTE recursiva)
WITH RECURSIVE numeros(n) AS (
    SELECT MIN(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM tickets
    UNION ALL
    SELECT n + 1 FROM numeros
    WHERE n < (SELECT MAX(CAST(SUBSTR(folio, 5) AS INTEGER)) FROM tickets)
)
SELECT PRINTF('GTR-%04d', n) AS folio_faltante
FROM numeros
WHERE n NOT IN (SELECT CAST(SUBSTR(folio, 5) AS INTEGER) FROM tickets);
