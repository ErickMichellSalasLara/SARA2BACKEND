-- =============================================================
-- S.A.R.A. - Sistema de Administración de Recursos y Accesos
-- Base de datos MySQL 8.0 - instalación sobre la base seleccionada
-- Congruente con la interfaz React actual
--
-- Reglas institucionales incluidas:
--   * 4 cubículos: América, Oceanía, Europa y Asia
--   * Horario de servicio y reservas: 07:30 a 16:00
--   * Duración máxima de reserva: 90 minutos
--   * Tolerancia: 15 minutos
--   * Dominio institucional: @utr.edu.mx
-- =============================================================

SET NAMES utf8mb4;
SET time_zone = '-06:00';

-- Este archivo instala el esquema en la base de datos YA seleccionada por la conexión.
-- No elimina ni crea una base. Úsalo únicamente sobre una base vacía.


-- =============================================================
-- 1. CATÁLOGOS Y AUTENTICACIÓN
-- =============================================================

CREATE TABLE roles (
  id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(60) NOT NULL,
  description VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  enrollment VARCHAR(30) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role_id TINYINT UNSIGNED NOT NULL,
  status ENUM('active', 'inactive', 'blocked', 'pending') NOT NULL DEFAULT 'active',
  email_verified_at DATETIME NULL,
  last_login_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_role
    FOREIGN KEY (role_id) REFERENCES roles(id),
  INDEX idx_users_role_status (role_id, status),
  INDEX idx_users_name (full_name)
) ENGINE=InnoDB;

CREATE TABLE auth_sessions (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  refresh_token_hash CHAR(64) NOT NULL UNIQUE,
  ip_address VARCHAR(45) NULL,
  user_agent VARCHAR(500) NULL,
  expires_at DATETIME NOT NULL,
  revoked_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_auth_sessions_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_auth_sessions_user_active (user_id, revoked_at, expires_at)
) ENGINE=InnoDB;

CREATE TABLE password_reset_tokens (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  token_hash CHAR(64) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  used_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_password_reset_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_password_reset_expiration (expires_at, used_at)
) ENGINE=InnoDB;

-- =============================================================
-- 2. CONFIGURACIÓN INSTITUCIONAL Y CALENDARIO
-- =============================================================

CREATE TABLE system_settings (
  setting_key VARCHAR(80) PRIMARY KEY,
  setting_value VARCHAR(500) NOT NULL,
  value_type ENUM('string', 'integer', 'decimal', 'boolean', 'time', 'json') NOT NULL,
  description VARCHAR(255) NULL,
  updated_by BIGINT UNSIGNED NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_system_settings_user
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE service_schedules (
  id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  day_of_week TINYINT UNSIGNED NOT NULL,
  day_name VARCHAR(20) NOT NULL,
  opening_time TIME NULL,
  closing_time TIME NULL,
  is_open BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT uq_service_schedule_day UNIQUE (day_of_week),
  CONSTRAINT chk_service_schedule_day CHECK (day_of_week BETWEEN 1 AND 7),
  CONSTRAINT chk_service_schedule_hours CHECK (
    (is_open = FALSE AND opening_time IS NULL AND closing_time IS NULL)
    OR
    (is_open = TRUE AND opening_time IS NOT NULL AND closing_time IS NOT NULL AND opening_time < closing_time)
  )
) ENGINE=InnoDB;

CREATE TABLE holidays (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  holiday_date DATE NOT NULL UNIQUE,
  name VARCHAR(150) NOT NULL,
  description VARCHAR(500) NULL,
  is_closed BOOLEAN NOT NULL DEFAULT TRUE,
  special_opening_time TIME NULL,
  special_closing_time TIME NULL,
  created_by BIGINT UNSIGNED NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_holidays_creator
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT chk_holiday_special_hours CHECK (
    (is_closed = TRUE AND special_opening_time IS NULL AND special_closing_time IS NULL)
    OR
    (is_closed = FALSE AND special_opening_time IS NOT NULL AND special_closing_time IS NOT NULL
      AND special_opening_time < special_closing_time)
  )
) ENGINE=InnoDB;

-- =============================================================
-- 3. CUBÍCULOS, RESERVAS Y MANTENIMIENTO
-- =============================================================

CREATE TABLE cubicles (
  id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(50) NOT NULL UNIQUE,
  location VARCHAR(100) NOT NULL DEFAULT 'Planta baja',
  capacity TINYINT UNSIGNED NOT NULL DEFAULT 8,
  operational_status ENUM('available', 'maintenance', 'disabled') NOT NULL DEFAULT 'available',
  description VARCHAR(500) NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT chk_cubicle_capacity CHECK (capacity > 0)
) ENGINE=InnoDB;

CREATE TABLE reservations (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  cubicle_id TINYINT UNSIGNED NOT NULL,
  reservation_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  status ENUM(
    'pending',
    'confirmed',
    'active',
    'completed',
    'cancelled',
    'expired',
    'no_show'
  ) NOT NULL DEFAULT 'confirmed',
  purpose VARCHAR(250) NULL,
  number_of_people TINYINT UNSIGNED NOT NULL DEFAULT 1,
  source ENUM('student', 'admin', 'google_calendar', 'system') NOT NULL DEFAULT 'student',
  external_event_id VARCHAR(255) NULL UNIQUE,
  created_by BIGINT UNSIGNED NULL,
  cancelled_by BIGINT UNSIGNED NULL,
  cancellation_reason VARCHAR(500) NULL,
  cancelled_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_reservations_user
    FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_reservations_cubicle
    FOREIGN KEY (cubicle_id) REFERENCES cubicles(id),
  CONSTRAINT fk_reservations_creator
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_reservations_canceller
    FOREIGN KEY (cancelled_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT chk_reservation_people CHECK (number_of_people > 0),
  CONSTRAINT chk_reservation_time_order CHECK (start_time < end_time),
  INDEX idx_reservations_cubicle_date_time (cubicle_id, reservation_date, start_time, end_time),
  INDEX idx_reservations_user_date (user_id, reservation_date),
  INDEX idx_reservations_status_date (status, reservation_date)
) ENGINE=InnoDB;

CREATE TABLE cubicle_maintenance (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  cubicle_id TINYINT UNSIGNED NOT NULL,
  reason VARCHAR(150) NOT NULL,
  description VARCHAR(500) NULL,
  start_datetime DATETIME NOT NULL,
  end_datetime DATETIME NOT NULL,
  status ENUM('scheduled', 'active', 'completed', 'cancelled') NOT NULL DEFAULT 'scheduled',
  reported_by BIGINT UNSIGNED NULL,
  resolved_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_maintenance_cubicle
    FOREIGN KEY (cubicle_id) REFERENCES cubicles(id),
  CONSTRAINT fk_maintenance_reporter
    FOREIGN KEY (reported_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT chk_maintenance_time_order CHECK (start_datetime < end_datetime),
  INDEX idx_maintenance_cubicle_period (cubicle_id, start_datetime, end_datetime, status)
) ENGINE=InnoDB;

-- =============================================================
-- 4. ACCESOS, CREDENCIALES Y DISPOSITIVOS
-- =============================================================

CREATE TABLE devices (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  device_code VARCHAR(60) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  device_type ENUM('rfid_reader', 'occupancy_sensor', 'controller', 'other') NOT NULL,
  location VARCHAR(150) NULL,
  status ENUM('online', 'offline', 'maintenance', 'disabled') NOT NULL DEFAULT 'offline',
  ip_address VARCHAR(45) NULL,
  last_seen_at DATETIME NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE access_cards (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  card_uid VARCHAR(100) NOT NULL UNIQUE,
  status ENUM('active', 'inactive', 'lost', 'revoked') NOT NULL DEFAULT 'active',
  assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  revoked_at DATETIME NULL,
  last_used_at DATETIME NULL,
  CONSTRAINT fk_access_cards_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_access_cards_user_status (user_id, status)
) ENGINE=InnoDB;

CREATE TABLE access_records (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NULL,
  card_uid_snapshot VARCHAR(100) NULL,
  movement ENUM('entry', 'exit') NOT NULL,
  result ENUM('granted', 'denied') NOT NULL,
  device_id BIGINT UNSIGNED NOT NULL,
  reason VARCHAR(250) NULL,
  occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_access_records_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_access_records_device
    FOREIGN KEY (device_id) REFERENCES devices(id),
  INDEX idx_access_records_occurred (occurred_at),
  INDEX idx_access_records_user_occurred (user_id, occurred_at),
  INDEX idx_access_records_result (result, occurred_at)
) ENGINE=InnoDB;

-- =============================================================
-- 5. MATERIALES Y PRÉSTAMOS
-- =============================================================

CREATE TABLE materials (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  resource_code VARCHAR(30) NOT NULL UNIQUE,
  title VARCHAR(200) NOT NULL,
  author VARCHAR(150) NULL,
  isbn VARCHAR(20) NULL UNIQUE,
  category VARCHAR(100) NULL,
  status ENUM('available', 'loaned', 'maintenance', 'lost', 'disabled') NOT NULL DEFAULT 'available',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_materials_title (title),
  INDEX idx_materials_status (status)
) ENGINE=InnoDB;

CREATE TABLE loans (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  material_id BIGINT UNSIGNED NOT NULL,
  loan_date DATE NOT NULL,
  due_date DATE NOT NULL,
  return_date DATE NULL,
  status ENUM('active', 'overdue', 'renewed', 'returned', 'lost', 'cancelled') NOT NULL DEFAULT 'active',
  renewal_count TINYINT UNSIGNED NOT NULL DEFAULT 0,
  registered_by BIGINT UNSIGNED NULL,
  notes VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_loans_user
    FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_loans_material
    FOREIGN KEY (material_id) REFERENCES materials(id),
  CONSTRAINT fk_loans_registrar
    FOREIGN KEY (registered_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT chk_loan_dates CHECK (due_date >= loan_date),
  CONSTRAINT chk_loan_renewals CHECK (renewal_count <= 3),
  INDEX idx_loans_user_status (user_id, status),
  INDEX idx_loans_due_status (due_date, status)
) ENGINE=InnoDB;

-- =============================================================
-- 6. AUDITORÍA Y ALERTAS
-- =============================================================

CREATE TABLE audit_logs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  actor_user_id BIGINT UNSIGNED NULL,
  action VARCHAR(100) NOT NULL,
  module VARCHAR(80) NOT NULL,
  entity_type VARCHAR(80) NULL,
  entity_id VARCHAR(80) NULL,
  record_label VARCHAR(200) NULL,
  previous_values JSON NULL,
  new_values JSON NULL,
  ip_address VARCHAR(45) NULL,
  user_agent VARCHAR(500) NULL,
  occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_audit_actor
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_audit_module_date (module, occurred_at),
  INDEX idx_audit_actor_date (actor_user_id, occurred_at)
) ENGINE=InnoDB;

CREATE TABLE system_alerts (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  level ENUM('info', 'warning', 'danger', 'success') NOT NULL,
  title VARCHAR(150) NOT NULL,
  description VARCHAR(500) NOT NULL,
  module VARCHAR(80) NULL,
  entity_type VARCHAR(80) NULL,
  entity_id VARCHAR(80) NULL,
  target_role_code VARCHAR(30) NULL,
  is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
  resolved_by BIGINT UNSIGNED NULL,
  resolved_at DATETIME NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_alert_resolver
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_alerts_active (is_resolved, level, created_at)
) ENGINE=InnoDB;

-- =============================================================
-- 7. VALIDACIONES DE NEGOCIO
-- =============================================================

DELIMITER $$

CREATE TRIGGER trg_users_validate_email_bi
BEFORE INSERT ON users
FOR EACH ROW
BEGIN
  SET NEW.email = LOWER(TRIM(NEW.email));
  SET NEW.enrollment = UPPER(TRIM(NEW.enrollment));

  IF RIGHT(NEW.email, 11) <> '@utr.edu.mx' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El correo debe pertenecer al dominio @utr.edu.mx.';
  END IF;
END$$

CREATE TRIGGER trg_users_validate_email_bu
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
  SET NEW.email = LOWER(TRIM(NEW.email));
  SET NEW.enrollment = UPPER(TRIM(NEW.enrollment));

  IF RIGHT(NEW.email, 11) <> '@utr.edu.mx' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El correo debe pertenecer al dominio @utr.edu.mx.';
  END IF;
END$$

CREATE PROCEDURE sp_validate_reservation(
  IN p_reservation_id BIGINT UNSIGNED,
  IN p_user_id BIGINT UNSIGNED,
  IN p_cubicle_id TINYINT UNSIGNED,
  IN p_reservation_date DATE,
  IN p_start_time TIME,
  IN p_end_time TIME,
  IN p_status VARCHAR(20),
  IN p_number_of_people TINYINT UNSIGNED
)
validation: BEGIN
  DECLARE v_service_start TIME;
  DECLARE v_service_end TIME;
  DECLARE v_max_minutes INT;
  DECLARE v_count INT DEFAULT 0;
  DECLARE v_capacity INT;
  DECLARE v_cubicle_status VARCHAR(20);
  DECLARE v_cubicle_active BOOLEAN;
  DECLARE v_user_status VARCHAR(20);

  IF p_status IN ('cancelled', 'expired', 'completed') THEN
    LEAVE validation;
  END IF;

  IF p_reservation_date < CURDATE()
     OR (p_reservation_date = CURDATE() AND p_start_time <= CURTIME()) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'No se permiten reservas en fechas u horarios pasados.';
  END IF;

  SELECT CAST(setting_value AS TIME)
    INTO v_service_start
  FROM system_settings
  WHERE setting_key = 'service_start_time';

  SELECT CAST(setting_value AS TIME)
    INTO v_service_end
  FROM system_settings
  WHERE setting_key = 'service_end_time';

  SELECT CAST(setting_value AS UNSIGNED)
    INTO v_max_minutes
  FROM system_settings
  WHERE setting_key = 'maximum_reservation_minutes';

  IF p_start_time < v_service_start OR p_end_time > v_service_end THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Las reservas solo están permitidas de 07:30 a 16:00.';
  END IF;

  IF p_start_time >= p_end_time THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La hora final debe ser posterior a la hora inicial.';
  END IF;

  IF TIMESTAMPDIFF(
      MINUTE,
      TIMESTAMP(p_reservation_date, p_start_time),
      TIMESTAMP(p_reservation_date, p_end_time)
    ) > v_max_minutes THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La reserva excede la duración máxima permitida.';
  END IF;

  SELECT COUNT(*)
    INTO v_count
  FROM service_schedules
  WHERE day_of_week = WEEKDAY(p_reservation_date) + 1
    AND is_open = TRUE
    AND p_start_time >= opening_time
    AND p_end_time <= closing_time;

  IF v_count = 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El sistema no presta servicio en el día u horario seleccionado.';
  END IF;

  SELECT COUNT(*)
    INTO v_count
  FROM holidays
  WHERE holiday_date = p_reservation_date
    AND is_closed = TRUE;

  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'No se permiten reservas durante un día de cierre institucional.';
  END IF;

  SELECT status
    INTO v_user_status
  FROM users
  WHERE id = p_user_id;

  IF v_user_status <> 'active' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El usuario no tiene una cuenta activa.';
  END IF;

  SELECT capacity, operational_status, is_active
    INTO v_capacity, v_cubicle_status, v_cubicle_active
  FROM cubicles
  WHERE id = p_cubicle_id;

  IF v_cubicle_active = FALSE OR v_cubicle_status <> 'available' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El cubículo no se encuentra disponible para reservar.';
  END IF;

  IF p_number_of_people > v_capacity THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El número de personas excede la capacidad del cubículo.';
  END IF;

  SELECT COUNT(*)
    INTO v_count
  FROM reservations r
  WHERE r.cubicle_id = p_cubicle_id
    AND r.reservation_date = p_reservation_date
    AND r.status IN ('pending', 'confirmed', 'active')
    AND r.id <> COALESCE(p_reservation_id, 0)
    AND p_start_time < r.end_time
    AND p_end_time > r.start_time;

  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El cubículo ya tiene una reserva que se traslapa con ese horario.';
  END IF;

  SELECT COUNT(*)
    INTO v_count
  FROM cubicle_maintenance m
  WHERE m.cubicle_id = p_cubicle_id
    AND m.status IN ('scheduled', 'active')
    AND TIMESTAMP(p_reservation_date, p_start_time) < m.end_datetime
    AND TIMESTAMP(p_reservation_date, p_end_time) > m.start_datetime;

  IF v_count > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El cubículo tiene mantenimiento programado en ese horario.';
  END IF;
END validation$$

CREATE TRIGGER trg_reservations_validate_bi
BEFORE INSERT ON reservations
FOR EACH ROW
BEGIN
  CALL sp_validate_reservation(
    0,
    NEW.user_id,
    NEW.cubicle_id,
    NEW.reservation_date,
    NEW.start_time,
    NEW.end_time,
    NEW.status,
    NEW.number_of_people
  );
END$$

CREATE TRIGGER trg_reservations_validate_bu
BEFORE UPDATE ON reservations
FOR EACH ROW
BEGIN
  CALL sp_validate_reservation(
    NEW.id,
    NEW.user_id,
    NEW.cubicle_id,
    NEW.reservation_date,
    NEW.start_time,
    NEW.end_time,
    NEW.status,
    NEW.number_of_people
  );
END$$

CREATE TRIGGER trg_loans_validate_bi
BEFORE INSERT ON loans
FOR EACH ROW
BEGIN
  DECLARE v_user_status VARCHAR(20);
  DECLARE v_material_status VARCHAR(20);

  SELECT status INTO v_user_status
  FROM users
  WHERE id = NEW.user_id;

  IF v_user_status <> 'active' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El usuario no tiene una cuenta activa.';
  END IF;

  SELECT status INTO v_material_status
  FROM materials
  WHERE id = NEW.material_id;

  IF v_material_status <> 'available' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'El recurso no se encuentra disponible.';
  END IF;

  IF NEW.due_date < NEW.loan_date THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'La fecha límite no puede ser anterior a la fecha de préstamo.';
  END IF;
END$$

CREATE TRIGGER trg_loans_material_ai
AFTER INSERT ON loans
FOR EACH ROW
BEGIN
  IF NEW.status IN ('active', 'overdue', 'renewed') THEN
    UPDATE materials
    SET status = 'loaned'
    WHERE id = NEW.material_id;
  END IF;
END$$

CREATE TRIGGER trg_loans_material_au
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
  IF NEW.status = 'returned' AND OLD.status <> 'returned' THEN
    UPDATE materials
    SET status = 'available'
    WHERE id = NEW.material_id;
  ELSEIF NEW.status IN ('active', 'overdue', 'renewed') THEN
    UPDATE materials
    SET status = 'loaned'
    WHERE id = NEW.material_id;
  END IF;
END$$

DELIMITER ;

-- =============================================================
-- 8. VISTAS PARA LOS ENDPOINTS DE LA PÁGINA
-- =============================================================

CREATE OR REPLACE VIEW vw_cubicle_status AS
SELECT
  c.id,
  c.code,
  c.name,
  c.location,
  c.capacity,
  CASE
    WHEN c.is_active = FALSE OR c.operational_status = 'disabled' THEN 'disabled'
    WHEN c.operational_status = 'maintenance'
      OR EXISTS (
        SELECT 1
        FROM cubicle_maintenance m
        WHERE m.cubicle_id = c.id
          AND m.status IN ('scheduled', 'active')
          AND NOW() BETWEEN m.start_datetime AND m.end_datetime
      ) THEN 'maintenance'
    WHEN EXISTS (
      SELECT 1
      FROM reservations r
      WHERE r.cubicle_id = c.id
        AND r.reservation_date = CURDATE()
        AND r.status = 'active'
        AND CURTIME() >= r.start_time
        AND CURTIME() < r.end_time
    ) THEN 'occupied'
    WHEN EXISTS (
      SELECT 1
      FROM reservations r
      WHERE r.cubicle_id = c.id
        AND r.reservation_date = CURDATE()
        AND r.status IN ('pending', 'confirmed')
        AND CURTIME() >= r.start_time
        AND CURTIME() < r.end_time
    ) THEN 'reserved'
    ELSE 'available'
  END AS status,
  (
    SELECT CONCAT(TIME_FORMAT(r.start_time, '%H:%i'), ' - ', TIME_FORMAT(r.end_time, '%H:%i'))
    FROM reservations r
    WHERE r.cubicle_id = c.id
      AND r.reservation_date = CURDATE()
      AND r.status IN ('pending', 'confirmed', 'active')
      AND CURTIME() >= r.start_time
      AND CURTIME() < r.end_time
    ORDER BY r.start_time
    LIMIT 1
  ) AS current_schedule,
  (
    SELECT CONCAT(
      DATE_FORMAT(r.reservation_date, '%Y-%m-%d'), ' ',
      TIME_FORMAT(r.start_time, '%H:%i'), ' - ',
      TIME_FORMAT(r.end_time, '%H:%i')
    )
    FROM reservations r
    WHERE r.cubicle_id = c.id
      AND r.status IN ('pending', 'confirmed')
      AND TIMESTAMP(r.reservation_date, r.start_time) > NOW()
    ORDER BY r.reservation_date, r.start_time
    LIMIT 1
  ) AS next_reservation
FROM cubicles c;

CREATE OR REPLACE VIEW vw_loans_effective AS
SELECT
  l.id,
  l.user_id,
  u.full_name AS user_name,
  u.enrollment,
  l.material_id,
  m.resource_code,
  m.title AS resource,
  l.loan_date,
  l.due_date,
  l.return_date,
  CASE
    WHEN l.status IN ('active', 'renewed') AND l.due_date < CURDATE() THEN 'overdue'
    ELSE l.status
  END AS status,
  l.renewal_count
FROM loans l
JOIN users u ON u.id = l.user_id
JOIN materials m ON m.id = l.material_id;

CREATE OR REPLACE VIEW vw_calendar_events AS
SELECT
  CONCAT('reservation-', r.id) AS event_id,
  CONCAT('Reserva: ', c.name, ' - ', u.full_name) AS title,
  TIMESTAMP(r.reservation_date, r.start_time) AS start_datetime,
  TIMESTAMP(r.reservation_date, r.end_time) AS end_datetime,
  r.status,
  c.id AS cubicle_id,
  u.id AS user_id
FROM reservations r
JOIN cubicles c ON c.id = r.cubicle_id
JOIN users u ON u.id = r.user_id
WHERE r.status IN ('pending', 'confirmed', 'active');

CREATE OR REPLACE VIEW vw_access_records AS
SELECT
  ar.id,
  ar.occurred_at,
  COALESCE(u.full_name, 'Usuario desconocido') AS user_name,
  COALESCE(u.enrollment, 'Sin identificar') AS enrollment,
  ar.movement,
  d.name AS reader,
  ar.result,
  ar.reason
FROM access_records ar
LEFT JOIN users u ON u.id = ar.user_id
JOIN devices d ON d.id = ar.device_id;

CREATE OR REPLACE VIEW vw_audit_records AS
SELECT
  a.id,
  COALESCE(u.full_name, 'Sistema') AS administrator,
  a.action,
  a.module,
  a.record_label,
  a.occurred_at,
  a.ip_address
FROM audit_logs a
LEFT JOIN users u ON u.id = a.actor_user_id;

-- =============================================================
-- 9. DATOS INICIALES CONGRUENTES CON LA INTERFAZ
-- =============================================================

INSERT INTO roles (id, code, name, description) VALUES
  (1, 'student', 'Estudiante', 'Consulta cubículos y realiza reservaciones.'),
  (2, 'teacher', 'Docente', 'Usuario académico con acceso institucional.'),
  (3, 'librarian', 'Bibliotecario', 'Administra préstamos y recursos literarios.'),
  (4, 'admin', 'Administrador', 'Administra todos los módulos de S.A.R.A.');

-- Las contraseñas se almacenan como PBKDF2-SHA256, nunca en texto plano.
-- Cuentas de demostración:
--   admin@utr.edu.mx  / Admin123
--   alumno@utr.edu.mx / Alumno123
-- Los demás usuarios de ejemplo tienen hashes aleatorios y no son cuentas de acceso documentadas.
INSERT INTO users (
  id, full_name, email, enrollment, password_hash, role_id, status, email_verified_at
) VALUES
  (1, 'Administrador S.A.R.A.', 'admin@utr.edu.mx', 'ADM-DEMO',
   'pbkdf2_sha256$600000$kLHqq43rXBzIRAO9Cq2Nzw$2aLmlOjVYQCm77HTvR23KJcGpdF_TdHO_q4VZu5W4Gk',
   4, 'active', NOW()),
  (2, 'Alumno de prueba', 'alumno@utr.edu.mx', 'UTR-DEMO',
   'pbkdf2_sha256$600000$PowJ9A5rRU1Oart2hx9Bcg$sMXFeQFZtXYTaEoCrdLGuT4xUsB2htqAc6JjfgleIgs',
   1, 'active', NOW()),
  (3, 'Ana López', 'ana.lopez@utr.edu.mx', 'UTR230145',
   'pbkdf2_sha256$600000$BhRsbAO4elgRlRZe4yN1IA$0rbY6SOs8RK6dxa46xd9Y7UDvaYL6YrCQxnixPgC080',
   1, 'active', NOW()),
  (4, 'Carlos Ruiz', 'carlos.ruiz@utr.edu.mx', 'UTR220418',
   'pbkdf2_sha256$600000$DZTcyOgkwFfHuO3i-pQbEA$39HkKt0eNswPSgYCZ5MzY0pM6K09c77Jvy2oCLc8Sk4',
   1, 'active', NOW()),
  (5, 'Mónica Silva', 'monica.silva@utr.edu.mx', 'ADM001',
   'pbkdf2_sha256$600000$PIQ8ujeN024RiA5-aLaApQ$NzNcfLEpMWBEN4vHvryhQ7L5w_p1-u3LS7MpnyudgWo',
   4, 'active', NOW()),
  (6, 'José Lara', 'jose.lara@utr.edu.mx', 'UTR210270',
   'pbkdf2_sha256$600000$ij-5dve2EtroABnrUO4i0g$DVAEZa0g2zcUuMNr13OjTY4HEjX87Ef1HLTC9Gm2Y7M',
   1, 'inactive', NOW()),
  (7, 'Laura Díaz', 'laura.diaz@utr.edu.mx', 'UTR240083',
   'pbkdf2_sha256$600000$LV_k98v-7t5laBZZaICiLQ$USDbDiqoIKf10EFfnahUZs5i2rgbAvEX8-SZub6BshM',
   1, 'active', NOW()),
  (8, 'Miguel Lara', 'miguel.lara@utr.edu.mx', 'UTR230512',
   'pbkdf2_sha256$600000$iWaWqpPB7yeO7FyGSbHW5Q$Io4hcCCR3zQSPvd_v4mWLZbAkuG8qSZvuPZ8L6JTlaM',
   1, 'active', NOW()),
  (9, 'Luis Torres', 'luis.torres@utr.edu.mx', 'UTR220301',
   'pbkdf2_sha256$600000$dMd-ZKYF9x-UR5CuOLDTTA$6SvUCMj5WeWgwrgau7wrlq0tUHkaNXyklFuIqAerkfs',
   1, 'active', NOW()),
  (10, 'María Soto', 'maria.soto@utr.edu.mx', 'UTR230077',
   'pbkdf2_sha256$600000$Hbn4eJPENN4YZSzImUT4CA$bo0yHWBN6izig-KbwnxYGmqVNCqE7s3GstZ9QwCE4Vo',
   1, 'active', NOW()),
  (11, 'José Herrera', 'jose.herrera@utr.edu.mx', 'ADM002',
   'pbkdf2_sha256$600000$gcFJOPtNAgGq0dB9pFbq1g$9Bi-lKdt02jITIMW8Sthh2GmHInev4IMZu6RUOS22uQ',
   4, 'active', NOW());

INSERT INTO system_settings (
  setting_key, setting_value, value_type, description, updated_by
) VALUES
  ('system_name', 'S.A.R.A.', 'string', 'Nombre mostrado por la plataforma.', 1),
  ('allowed_email_domain', '@utr.edu.mx', 'string', 'Dominio institucional autorizado.', 1),
  ('service_start_time', '07:30:00', 'time', 'Hora de inicio del servicio.', 1),
  ('service_end_time', '16:00:00', 'time', 'Hora de cierre del servicio.', 1),
  ('reservation_interval_minutes', '30', 'integer', 'Intervalos disponibles para reservar.', 1),
  ('maximum_reservation_minutes', '90', 'integer', 'Duración máxima de cada reserva.', 1),
  ('reservation_tolerance_minutes', '15', 'integer', 'Tolerancia antes de marcar inasistencia.', 1),
  ('default_loan_days', '7', 'integer', 'Duración predeterminada de préstamos.', 1),
  ('email_notifications', 'true', 'boolean', 'Activa notificaciones por correo.', 1),
  ('denied_access_alerts', 'true', 'boolean', 'Activa alertas de accesos denegados.', 1),
  ('overdue_loan_alerts', 'true', 'boolean', 'Activa alertas de préstamos vencidos.', 1);

INSERT INTO service_schedules (
  day_of_week, day_name, opening_time, closing_time, is_open
) VALUES
  (1, 'Lunes',    '07:30:00', '16:00:00', TRUE),
  (2, 'Martes',   '07:30:00', '16:00:00', TRUE),
  (3, 'Miércoles','07:30:00', '16:00:00', TRUE),
  (4, 'Jueves',   '07:30:00', '16:00:00', TRUE),
  (5, 'Viernes',  '07:30:00', '16:00:00', TRUE),
  (6, 'Sábado',   NULL, NULL, FALSE),
  (7, 'Domingo',  NULL, NULL, FALSE);

INSERT INTO cubicles (
  id, code, name, location, capacity, operational_status, description
) VALUES
  (1, 'CUB-AMERICA', 'América', 'Planta baja', 8, 'maintenance', 'Cubículo de trabajo colaborativo.'),
  (2, 'CUB-OCEANIA', 'Oceanía', 'Planta baja', 8, 'available', 'Cubículo de trabajo colaborativo.'),
  (3, 'CUB-EUROPA',  'Europa',  'Planta baja', 8, 'available', 'Cubículo de trabajo colaborativo.'),
  (4, 'CUB-ASIA',    'Asia',    'Planta baja', 8, 'available', 'Cubículo de trabajo colaborativo.');

INSERT INTO devices (
  id, device_code, name, device_type, location, status, ip_address, last_seen_at
) VALUES
  (1, 'ESP32-ENTRADA-01', 'Puerta principal', 'rfid_reader', 'Entrada principal', 'online', '192.168.1.50', NOW()),
  (2, 'ESP32-NORTE-01', 'Lector norte', 'rfid_reader', 'Acceso norte', 'online', '192.168.1.51', NOW());

INSERT INTO access_cards (user_id, card_uid, status) VALUES
  (3, '04A8F21C', 'active'),
  (4, '047BC902', 'active'),
  (7, '0455DA10', 'active'),
  (8, '04F921B8', 'active');

-- Se usa el siguiente día laboral para que las reservas de demostración nunca queden en el pasado.
SET @demo_date = CASE DAYOFWEEK(CURDATE())
  WHEN 1 THEN DATE_ADD(CURDATE(), INTERVAL 1 DAY)
  WHEN 6 THEN DATE_ADD(CURDATE(), INTERVAL 3 DAY)
  WHEN 7 THEN DATE_ADD(CURDATE(), INTERVAL 2 DAY)
  ELSE DATE_ADD(CURDATE(), INTERVAL 1 DAY)
END;

INSERT INTO reservations (
  user_id, cubicle_id, reservation_date, start_time, end_time,
  status, purpose, number_of_people, source, created_by
) VALUES
  (3, 4, @demo_date, '12:00:00', '13:30:00', 'confirmed', 'Trabajo académico', 4, 'admin', 5),
  (4, 3, @demo_date, '13:30:00', '14:30:00', 'confirmed', 'Proyecto en equipo', 5, 'admin', 5),
  (7, 2, @demo_date, '14:30:00', '15:30:00', 'confirmed', 'Sesión de estudio', 3, 'student', 7);

INSERT INTO cubicle_maintenance (
  cubicle_id, reason, description, start_datetime, end_datetime, status, reported_by
) VALUES
  (
    1,
    'Revisión eléctrica',
    'Cubículo temporalmente fuera de servicio.',
    TIMESTAMP(@demo_date, '07:30:00'),
    TIMESTAMP(@demo_date, '16:00:00'),
    'scheduled',
    5
  );

INSERT INTO access_records (
  user_id, card_uid_snapshot, movement, result, device_id, reason, occurred_at
) VALUES
  (3, '04A8F21C', 'entry', 'granted', 1, NULL, DATE_SUB(NOW(), INTERVAL 5 MINUTE)),
  (4, '047BC902', 'exit',  'granted', 1, NULL, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
  (NULL, 'UID-DESCONOCIDO', 'entry', 'denied', 2, 'Credencial no registrada', DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
  (7, '0455DA10', 'entry', 'granted', 1, NULL, DATE_SUB(NOW(), INTERVAL 20 MINUTE)),
  (8, '04F921B8', 'exit',  'granted', 1, NULL, DATE_SUB(NOW(), INTERVAL 25 MINUTE));

INSERT INTO materials (
  id, resource_code, title, author, category, status
) VALUES
  (1, 'LIB-341', 'Programación en Python', 'Varios autores', 'Programación', 'available'),
  (2, 'LIB-112', 'Diseño UX', 'Varios autores', 'Diseño', 'available'),
  (3, 'LIB-283', 'Redes de computadoras', 'Varios autores', 'Redes', 'available'),
  (4, 'LIB-118', 'Fundamentos de bases de datos', 'Varios autores', 'Bases de datos', 'available');

INSERT INTO loans (
  user_id, material_id, loan_date, due_date, return_date,
  status, renewal_count, registered_by
) VALUES
  (3, 1, DATE_SUB(CURDATE(), INTERVAL 7 DAY), CURDATE(), NULL, 'active', 0, 11),
  (9, 2, DATE_SUB(CURDATE(), INTERVAL 14 DAY), DATE_SUB(CURDATE(), INTERVAL 7 DAY), NULL, 'overdue', 0, 11),
  (10, 3, DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 2 DAY), NULL, 'active', 0, 11),
  (8, 4, DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_SUB(CURDATE(), INTERVAL 3 DAY), DATE_SUB(CURDATE(), INTERVAL 2 DAY), 'returned', 0, 11);

INSERT INTO audit_logs (
  actor_user_id, action, module, entity_type, entity_id, record_label,
  previous_values, new_values, ip_address, occurred_at
) VALUES
  (5, 'Creó una reserva', 'Reservas', 'reservation', '2', 'Europa',
   NULL, JSON_OBJECT('status', 'confirmed'), '192.168.1.40', DATE_SUB(NOW(), INTERVAL 12 MINUTE)),
  (5, 'Desactivó un usuario', 'Usuarios', 'user', '6', 'UTR210270',
   JSON_OBJECT('status', 'active'), JSON_OBJECT('status', 'inactive'), '192.168.1.40', DATE_SUB(NOW(), INTERVAL 45 MINUTE)),
  (11, 'Registró una devolución', 'Préstamos', 'loan', '4', 'LIB-118',
   JSON_OBJECT('status', 'active'), JSON_OBJECT('status', 'returned'), '192.168.1.42', DATE_SUB(NOW(), INTERVAL 90 MINUTE)),
  (11, 'Modificó la configuración', 'Configuración', 'setting', 'reservation_tolerance_minutes', 'Tiempo de tolerancia',
   JSON_OBJECT('value', 10), JSON_OBJECT('value', 15), '192.168.1.42', DATE_SUB(NOW(), INTERVAL 1 DAY));

INSERT INTO system_alerts (
  level, title, description, module, entity_type, entity_id, target_role_code, created_at
) VALUES
  ('danger', 'Préstamos vencidos', 'Existen préstamos que superaron la fecha de devolución.', 'Préstamos', 'loan', '2', 'admin', NOW()),
  ('warning', 'Cubículo en mantenimiento', 'El cubículo América está temporalmente fuera de servicio.', 'Reservas', 'cubicle', '1', 'admin', NOW()),
  ('info', 'Reserva próxima', 'Oceanía tiene una reservación próxima dentro del horario de servicio.', 'Reservas', 'reservation', '3', 'admin', NOW());

INSERT INTO holidays (
  holiday_date, name, description, is_closed, created_by
) VALUES
  ('2026-09-16', 'Día de la Independencia', 'Cierre institucional.', TRUE, 1),
  ('2026-11-16', 'Suspensión de labores', 'Cierre institucional.', TRUE, 1),
  ('2026-12-25', 'Navidad', 'Cierre institucional.', TRUE, 1);

-- =============================================================
-- 10. CONSULTAS DE COMPROBACIÓN
-- =============================================================

SELECT 'Base de datos S.A.R.A. creada correctamente.' AS result;
SELECT id, name, operational_status FROM cubicles ORDER BY id;
SELECT setting_key, setting_value FROM system_settings
WHERE setting_key IN ('service_start_time', 'service_end_time', 'maximum_reservation_minutes');
SELECT * FROM vw_cubicle_status ORDER BY id;
