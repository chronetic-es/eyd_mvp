-- ============================================================
-- EYD MVP — Espina y Delfín S.A.
-- Schema + seed data
-- ============================================================

-- Clean slate
DROP TABLE IF EXISTS llamadas CASCADE;
DROP TABLE IF EXISTS partes_trabajo CASCADE;
DROP TABLE IF EXISTS incidencia_direcciones CASCADE;
DROP TABLE IF EXISTS incidencias CASCADE;
DROP TABLE IF EXISTS expedientes_corte CASCADE;
DROP TABLE IF EXISTS historico_recibos CASCADE;
DROP TABLE IF EXISTS contadores CASCADE;
DROP TABLE IF EXISTS contratos CASCADE;
DROP TABLE IF EXISTS direcciones_suministro CASCADE;
DROP TABLE IF EXISTS entidades CASCADE;

DROP TYPE IF EXISTS estado_contrato;
DROP TYPE IF EXISTS estado_recibo;
DROP TYPE IF EXISTS forma_pago;
DROP TYPE IF EXISTS estado_expediente;
DROP TYPE IF EXISTS tipo_incidencia;
DROP TYPE IF EXISTS estado_incidencia;
DROP TYPE IF EXISTS estado_parte;
DROP TYPE IF EXISTS motivo_llamada;
DROP TYPE IF EXISTS estado_llamada;

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE estado_contrato AS ENUM ('Activo', 'Suspendido', 'Baja');
CREATE TYPE estado_recibo AS ENUM ('Pendiente', 'Pagado', 'Impagado', 'Devuelto');
CREATE TYPE forma_pago AS ENUM ('Efectivo', 'Transferencia', 'Domiciliado');
CREATE TYPE estado_expediente AS ENUM ('Pendiente', 'Notificado', 'Ejecutado', 'Cerrado');
CREATE TYPE tipo_incidencia AS ENUM ('Averia', 'Corte_programado', 'Corte_impago', 'Fuga');
CREATE TYPE estado_incidencia AS ENUM ('Abierta', 'En_progreso', 'Resuelta', 'Cerrada');
CREATE TYPE estado_parte AS ENUM ('Abierto', 'En_proceso', 'Cerrado');
CREATE TYPE motivo_llamada AS ENUM ('Sin_suministro', 'Fuga', 'Consulta_factura', 'Reclamacion', 'Informacion', 'Otro');
CREATE TYPE estado_llamada AS ENUM ('Completada', 'Escalada', 'Abandonada');

-- ============================================================
-- TABLES
-- ============================================================

-- 1. ENTIDADES — Subscriber / account holder
CREATE TABLE entidades (
    id          SERIAL PRIMARY KEY,
    nif         VARCHAR(20) NOT NULL UNIQUE,
    nombre      VARCHAR(100) NOT NULL,
    apellidos   VARCHAR(150) NOT NULL,
    telefono    VARCHAR(20) NOT NULL,
    dir_fiscal  VARCHAR(250) NOT NULL
);

CREATE INDEX idx_entidades_telefono ON entidades(telefono);
CREATE INDEX idx_entidades_nif ON entidades(nif);

-- 2. DIRECCIONES_SUMINISTRO — Physical supply addresses
CREATE TABLE direcciones_suministro (
    id          SERIAL PRIMARY KEY,
    calle       VARCHAR(200) NOT NULL,
    numero      VARCHAR(10),
    portal      VARCHAR(10),
    planta      VARCHAR(10),
    letra       VARCHAR(10),
    cod_postal  VARCHAR(10) NOT NULL,
    municipio   VARCHAR(100) NOT NULL
);

-- 3. CONTRATOS — One subscriber can have many contracts
CREATE TABLE contratos (
    id                      SERIAL PRIMARY KEY,
    numero_contrato         VARCHAR(20) NOT NULL UNIQUE,
    entidad_id              INT NOT NULL REFERENCES entidades(id),
    direccion_suministro_id INT NOT NULL REFERENCES direcciones_suministro(id),
    estado                  estado_contrato NOT NULL DEFAULT 'Activo',
    fecha_alta              DATE NOT NULL,
    fecha_baja              DATE,
    CONSTRAINT check_fechas_contrato CHECK (fecha_baja IS NULL OR fecha_baja >= fecha_alta)
);

CREATE INDEX idx_contratos_entidad ON contratos(entidad_id);
CREATE INDEX idx_contratos_direccion ON contratos(direccion_suministro_id);

-- 4. CONTADORES — Meter reading history
CREATE TABLE contadores (
    id              SERIAL PRIMARY KEY,
    contrato_id     INT NOT NULL REFERENCES contratos(id),
    num_serie       VARCHAR(30) NOT NULL,
    fecha_alta      DATE NOT NULL,
    fecha_baja      DATE,
    lectura_m3      DECIMAL(12,3) NOT NULL DEFAULT 0,
    fecha_lectura   DATE NOT NULL
);

CREATE INDEX idx_contadores_contrato ON contadores(contrato_id);

-- 5. HISTORICO_RECIBOS — Billing / payment history
CREATE TABLE historico_recibos (
    id                  SERIAL PRIMARY KEY,
    contrato_id         INT NOT NULL REFERENCES contratos(id),
    periodo             VARCHAR(20) NOT NULL,
    importe             DECIMAL(10,2) NOT NULL,
    estado              estado_recibo NOT NULL DEFAULT 'Pendiente',
    forma_pago          forma_pago NOT NULL DEFAULT 'Domiciliado',
    fecha_emision       DATE NOT NULL,
    fecha_vencimiento   DATE NOT NULL,
    CONSTRAINT check_importe_positivo CHECK (importe >= 0)
);

CREATE INDEX idx_recibos_contrato ON historico_recibos(contrato_id);
CREATE INDEX idx_recibos_estado ON historico_recibos(estado);

-- 6. EXPEDIENTES_CORTE — Service suspension management
CREATE TABLE expedientes_corte (
    id              SERIAL PRIMARY KEY,
    contrato_id     INT NOT NULL REFERENCES contratos(id),
    recibo_id       INT REFERENCES historico_recibos(id),
    fecha_apertura  DATE NOT NULL,
    fecha_corte     DATE,
    estado          estado_expediente NOT NULL DEFAULT 'Pendiente',
    importe_deuda   DECIMAL(10,2)
);

CREATE INDEX idx_expedientes_contrato ON expedientes_corte(contrato_id);

-- 7. INCIDENCIAS — System-wide incidents
CREATE TABLE incidencias (
    id                  SERIAL PRIMARY KEY,
    tipo                tipo_incidencia NOT NULL,
    fecha_inicio        DATE NOT NULL,
    hora_inicio         TIME NOT NULL,
    fecha_fin           DATE,
    hora_fin            TIME,
    fecha_fin_prevista  DATE,
    hora_fin_prevista   TIME,
    descripcion         TEXT NOT NULL
);

CREATE INDEX idx_incidencias_tipo ON incidencias(tipo);

-- 8. INCIDENCIA_DIRECCIONES — N:M incidents <-> supply addresses
CREATE TABLE incidencia_direcciones (
    id                      SERIAL PRIMARY KEY,
    incidencia_id           INT NOT NULL REFERENCES incidencias(id) ON DELETE CASCADE,
    direccion_suministro_id INT NOT NULL REFERENCES direcciones_suministro(id),
    UNIQUE(incidencia_id, direccion_suministro_id)
);

-- 9. PARTES_TRABAJO — Work orders / tickets
CREATE TABLE partes_trabajo (
    id              SERIAL PRIMARY KEY,
    numero_parte    VARCHAR(20) NOT NULL UNIQUE,
    direccion_suministro_id INT REFERENCES direcciones_suministro(id),
    incidencia_id   INT REFERENCES incidencias(id),
    fecha           DATE NOT NULL DEFAULT CURRENT_DATE,
    estado          estado_parte NOT NULL DEFAULT 'Abierto',
    descripcion     TEXT NOT NULL
);

CREATE INDEX idx_partes_incidencia ON partes_trabajo(incidencia_id);
CREATE INDEX idx_partes_estado ON partes_trabajo(estado);

-- 10. LLAMADAS — Call registry
CREATE TABLE llamadas (
    id                  SERIAL PRIMARY KEY,
    telefono            VARCHAR(20) NOT NULL,
    fecha_inicio        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin           TIMESTAMP,
    transcripcion       TEXT,
    resumen_ia          TEXT,
    motivo_detectado    motivo_llamada,
    human_handoff       BOOLEAN NOT NULL DEFAULT FALSE,
    estado              estado_llamada NOT NULL DEFAULT 'Completada'
);

CREATE INDEX idx_llamadas_telefono ON llamadas(telefono);
CREATE INDEX idx_llamadas_fecha ON llamadas(fecha_inicio);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Entidades (6 subscribers)
INSERT INTO entidades (id, nif, nombre, apellidos, telefono, dir_fiscal) VALUES
(1, '12345678A', 'Maria',   'Garcia Lopez',      '600111222', 'Calle Mayor 15, 1o A, 28001 Villanueva'),
(2, '23456789B', 'Jose',    'Rodriguez Perez',    '600333444', 'Av. Constitucion 42, 28002 Villanueva'),
(3, '34567890C', 'Ana',     'Martinez Ruiz',      '600555666', 'Plaza de Espana 3, 28001 Villanueva'),
(4, '45678901D', 'Carlos',  'Fernandez Diaz',     '600777888', 'Calle del Rio 8, 28002 Villanueva'),
(5, '56789012E', 'Lucia',   'Sanchez Torres',     '600999000', 'Camino del Molino 5, 28010 Aldeanueva'),
(6, '67890123F', 'Pedro',   'Gomez Navarro',      '601111222', 'Calle Nueva 10, 28001 Villanueva');

SELECT setval('entidades_id_seq', 6);

-- Direcciones de suministro (8 addresses)
INSERT INTO direcciones_suministro (id, calle, numero, portal, planta, letra, cod_postal, municipio) VALUES
(1, 'Calle Mayor',              '15', NULL,  '1', 'A', '28001', 'Villanueva'),
(2, 'Calle Mayor',              '15', NULL,  '2', 'B', '28001', 'Villanueva'),
(3, 'Avenida de la Constitucion','42', NULL, NULL, NULL, '28002', 'Villanueva'),
(4, 'Calle del Rio',            '8',  NULL, NULL, NULL, '28002', 'Villanueva'),
(5, 'Plaza de Espana',          '3',  NULL, NULL, '2',  '28001', 'Villanueva'),
(6, 'Calle Olivos',             '22', NULL, NULL, NULL, '28003', 'Villanueva'),
(7, 'Camino del Molino',        '5',  NULL, NULL, NULL, '28010', 'Aldeanueva'),
(8, 'Calle Nueva',              '10', NULL, NULL, NULL, '28001', 'Villanueva');

SELECT setval('direcciones_suministro_id_seq', 8);

-- Contratos (7 contracts)
INSERT INTO contratos (id, numero_contrato, entidad_id, direccion_suministro_id, estado, fecha_alta, fecha_baja) VALUES
(1, 'CTR-2020-001', 1, 1, 'Activo',     '2020-03-15', NULL),
(2, 'CTR-2021-002', 2, 3, 'Activo',     '2021-06-01', NULL),
(3, 'CTR-2019-003', 3, 5, 'Activo',     '2019-01-10', NULL),
(4, 'CTR-2022-004', 3, 6, 'Activo',     '2022-09-20', NULL),
(5, 'CTR-2023-005', 4, 4, 'Activo',     '2023-02-14', NULL),
(6, 'CTR-2018-006', 5, 7, 'Activo',     '2018-11-05', NULL),
(7, 'CTR-2020-008', 1, 2, 'Activo',     '2020-07-01', NULL);

SELECT setval('contratos_id_seq', 7);

-- Contadores — meter readings
INSERT INTO contadores (contrato_id, num_serie, fecha_alta, fecha_baja, lectura_m3, fecha_lectura) VALUES
(1, 'CNT-001-2020', '2020-03-15', NULL, 245.500, '2026-03-01'),
(1, 'CNT-001-2020', '2020-03-15', NULL, 230.100, '2025-12-01'),
(2, 'CNT-002-2021', '2021-06-01', NULL, 189.300, '2026-03-01'),
(2, 'CNT-002-2021', '2021-06-01', NULL, 175.800, '2025-12-01'),
(3, 'CNT-003-2019', '2019-01-10', NULL, 412.700, '2026-03-01'),
(4, 'CNT-004-2022', '2022-09-20', NULL, 98.200,  '2026-03-01'),
(5, 'CNT-005-2023', '2023-02-14', NULL, 67.400,  '2026-03-01'),
(6, 'CNT-006-2018', '2018-11-05', NULL, 520.900, '2026-03-01'),
(7, 'CNT-007-2020', '2020-07-01', NULL, 110.300, '2026-03-01');

-- Historico de recibos
-- Contract 1 (Maria) — all paid
INSERT INTO historico_recibos (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(1, '2025-T4', 85.30,  'Pagado', 'Domiciliado', '2025-12-01', '2025-12-31'),
(1, '2026-T1', 92.15,  'Pagado', 'Domiciliado', '2026-03-01', '2026-03-31');

-- Contract 2 (Jose) — has unpaid bills
INSERT INTO historico_recibos (id, contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(3, 2, '2025-T3', 78.40,  'Pagado',   'Domiciliado', '2025-09-01', '2025-09-30'),
(4, 2, '2025-T4', 95.60,  'Impagado', 'Domiciliado', '2025-12-01', '2025-12-31'),
(5, 2, '2026-T1', 102.30, 'Devuelto', 'Domiciliado', '2026-03-01', '2026-03-31');

SELECT setval('historico_recibos_id_seq', 5);

-- Contract 3 (Ana shop) — paid
INSERT INTO historico_recibos (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(3, '2025-T4', 210.50, 'Pagado', 'Transferencia', '2025-12-01', '2025-12-31'),
(3, '2026-T1', 195.80, 'Pagado', 'Transferencia', '2026-03-01', '2026-03-31');

-- Contract 4 (Ana house) — paid
INSERT INTO historico_recibos (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(4, '2026-T1', 72.40, 'Pagado', 'Domiciliado', '2026-03-01', '2026-03-31');

-- Contract 5 (Carlos) — paid
INSERT INTO historico_recibos (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(5, '2026-T1', 55.90, 'Pagado', 'Domiciliado', '2026-03-01', '2026-03-31');

-- Contract 6 (Lucia) — was impagado, now paid after restoration
INSERT INTO historico_recibos (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(6, '2025-T3', 68.20, 'Pagado',   'Efectivo',     '2025-09-01', '2025-09-30'),
(6, '2025-T4', 71.50, 'Pagado',   'Efectivo',     '2025-12-01', '2025-12-31');

-- Contract 7 (Maria 2nd apt) — paid
INSERT INTO historico_recibos (contrato_id, periodo, importe, estado, forma_pago, fecha_emision, fecha_vencimiento) VALUES
(7, '2026-T1', 64.70, 'Pagado', 'Domiciliado', '2026-03-01', '2026-03-31');

-- Expedientes de corte
-- Jose (contract 2) — active, notified due to unpaid bills
INSERT INTO expedientes_corte (id, contrato_id, recibo_id, fecha_apertura, fecha_corte, estado, importe_deuda) VALUES
(1, 2, 4, '2026-01-15', '2026-04-15', 'Notificado', 197.90);

-- Lucia (contract 6) — historical, was executed then closed after payment
INSERT INTO expedientes_corte (id, contrato_id, recibo_id, fecha_apertura, fecha_corte, estado, importe_deuda) VALUES
(2, 6, NULL, '2025-06-01', '2025-07-15', 'Cerrado', 0.00);

SELECT setval('expedientes_corte_id_seq', 2);

-- Incidencias
-- 1. Active leak in Zona Norte (affects addresses 3 and 4)
INSERT INTO incidencias (id, tipo, fecha_inicio, hora_inicio, fecha_fin, hora_fin, fecha_fin_prevista, hora_fin_prevista, descripcion) VALUES
(1, 'Fuga', '2026-06-01', '08:30', NULL, NULL, '2026-06-02', '18:00',
 'Fuga en red principal de la Calle del Rio. Afecta a suministro en Zona Norte.');

-- 2. Scheduled maintenance (affects address 6)
INSERT INTO incidencias (id, tipo, fecha_inicio, hora_inicio, fecha_fin, hora_fin, fecha_fin_prevista, hora_fin_prevista, descripcion) VALUES
(2, 'Corte_programado', '2026-06-09', '08:00', NULL, NULL, '2026-06-09', '14:00',
 'Mantenimiento programado de la red en Calle Olivos y alrededores.');

-- 3. Resolved breakdown (affected address 7)
INSERT INTO incidencias (id, tipo, fecha_inicio, hora_inicio, fecha_fin, hora_fin, fecha_fin_prevista, hora_fin_prevista, descripcion) VALUES
(3, 'Averia', '2026-05-20', '10:00', '2026-05-21', '16:30', '2026-05-21', '18:00',
 'Averia en bomba de la estacion de Aldeanueva. Servicio restaurado.');

SELECT setval('incidencias_id_seq', 3);

-- Incidencia-direcciones (N:M links)
INSERT INTO incidencia_direcciones (incidencia_id, direccion_suministro_id) VALUES
(1, 3),   -- Fuga affects Av. Constitucion 42 (Jose)
(1, 4),   -- Fuga affects Calle del Rio 8 (Carlos)
(2, 6),   -- Corte programado affects Calle Olivos 22 (Ana house)
(3, 7);   -- Averia affected Camino del Molino 5 (Lucia)

-- Partes de trabajo
INSERT INTO partes_trabajo (id, numero_parte, direccion_suministro_id, incidencia_id, fecha, estado, descripcion) VALUES
(1, 'PT-2026-0001', 4, 1, '2026-06-01', 'En_proceso', 'Reparacion de fuga en red principal Calle del Rio.'),
(2, 'PT-2026-0002', 7, 3, '2026-05-20', 'Cerrado', 'Reparacion bomba estacion Aldeanueva.');

SELECT setval('partes_trabajo_id_seq', 2);

-- Llamadas historicas
INSERT INTO llamadas (telefono, fecha_inicio, fecha_fin, resumen_ia, motivo_detectado, human_handoff, estado) VALUES
('600777888', '2026-06-01 09:15:00', '2026-06-01 09:22:00',
 'Abonado Carlos Fernandez reporta falta de agua en Calle del Rio 8. Se identifica fuga activa en la zona. Se informa del parte de trabajo PT-2026-0001.',
 'Sin_suministro', FALSE, 'Completada'),
('600555666', '2026-05-28 11:00:00', '2026-05-28 11:08:00',
 'Abonada Ana Martinez consulta sobre proximo recibo del contrato CTR-2022-004. Se informa que el recibo del periodo 2026-T1 esta pagado.',
 'Consulta_factura', FALSE, 'Completada');
