-- ============================================================
-- Señas Co — Esquema de base de datos (MySQL / MariaDB)
-- Compatible con XAMPP 8.x
-- ============================================================

CREATE DATABASE IF NOT EXISTS traductor_lsc
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE traductor_lsc;

-- ---------- Diccionario principal de señas ----------
DROP TABLE IF EXISTS senas;

CREATE TABLE senas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    palabra     VARCHAR(120) NOT NULL UNIQUE COLLATE utf8mb4_bin,
    gif_url     VARCHAR(255) NOT NULL,
    tipo        ENUM('letra', 'numero', 'palabra', 'frase') NOT NULL,
    categoria   VARCHAR(50)  NOT NULL DEFAULT 'general',
    descripcion VARCHAR(255) NULL,
    activo      TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tipo      (tipo),
    INDEX idx_categoria (categoria),
    INDEX idx_activo    (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- Usuarios (autenticación + 2FA + Google OAuth) ----------
CREATE TABLE IF NOT EXISTS usuarios (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    nombres            VARCHAR(80)  NOT NULL,
    apellidos          VARCHAR(80)  NOT NULL,
    email              VARCHAR(120) NOT NULL UNIQUE,
    password_hash      VARCHAR(255) NOT NULL,
    totp_secret        VARCHAR(64)  NULL,
    totp_enabled       TINYINT(1)   NOT NULL DEFAULT 0,
    recovery_file_hash VARCHAR(255) NULL,
    google_id          VARCHAR(64)  NULL,
    email_verified     TINYINT(1)   NOT NULL DEFAULT 0,
    created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email     (email),
    INDEX idx_google_id (google_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- Recovery codes (un solo uso) ----------
CREATE TABLE IF NOT EXISTS recovery_codes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT          NOT NULL,
    code_hash   VARCHAR(255) NOT NULL,
    usado       TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at     DATETIME     NULL,
    INDEX idx_usuario (usuario_id),
    CONSTRAINT fk_recovery_user
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- Reset password tokens ----------
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT          NOT NULL,
    token_hash  VARCHAR(255) NOT NULL,
    expira_en   DATETIME     NOT NULL,
    usado       TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuario_pwd (usuario_id),
    CONSTRAINT fk_pwdreset_user
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------- Historial de traducciones (auditoría y estadísticas) ----------
DROP TABLE IF EXISTS historial;

CREATE TABLE historial (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    texto_original TEXT         NOT NULL,
    tokens_json    TEXT         NOT NULL,
    total_senas    INT          NOT NULL DEFAULT 0,
    no_encontradas INT          NOT NULL DEFAULT 0,
    ip_cliente     VARCHAR(45)  NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
