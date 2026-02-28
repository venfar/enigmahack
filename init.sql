SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE DATABASE IF NOT EXISTS enigma_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE enigma_db;

CREATE TABLE IF NOT EXISTS Facility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Sentiment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Gas_analyzer_type (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Gas_analyzer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    type_id INT,
    FOREIGN KEY (type_id) REFERENCES Gas_analyzer_type(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS ticket (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_id VARCHAR(100),
    subject VARCHAR(255),
    body MEDIUMTEXT,
    facility_id INT,
    contact_id INT,
    sentiment_id INT,
    sentiment_confidence FLOAT,
    category_id INT,
    category_confidence FLOAT,
    gaz_analyzer_id INT,
    generated_response MEDIUMTEXT,
    response_method VARCHAR(50),
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES Facility(id),
    FOREIGN KEY (contact_id) REFERENCES Contacts(id),
    FOREIGN KEY (sentiment_id) REFERENCES Sentiment(id),
    FOREIGN KEY (category_id) REFERENCES Categories(id),
    FOREIGN KEY (gaz_analyzer_id) REFERENCES Gas_analyzer(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO Sentiment (id, name) VALUES (1, 'negative'), (2, 'neutral'), (3, 'positive');
INSERT IGNORE INTO Categories (id, name) VALUES (1, 'документация'), (2, 'калибровка'), (3, 'техподдержка');
INSERT IGNORE INTO Gas_analyzer_type (id, type) VALUES (1, 'ДГС ЭРИС-230'), (2, 'ПКГ ЭРИС-411'), (3, 'Стационарный');

INSERT IGNORE INTO Facility (id, name) VALUES (1, 'ООО «ТестГаз»'), (2, 'ЗАО «ХимТех»'), (3, 'ПАО «ГазПром»');

INSERT IGNORE INTO Contacts (id, full_name, email, phone) VALUES 
(1, 'Иванов Иван Иванович', 'test@testgaz.ru', '+7 (495) 123-45-67'),
(2, 'Волков Игорь Александрович', 'i.volkov@himtech.ru', '+7 (921) 222-33-44'),
(3, 'Петров Петр Петрович', 'petrov@gazprom.ru', '+7 (800) 555-35-35');

INSERT IGNORE INTO Gas_analyzer (id, serial_number, type_id) VALUES (1, 'SN123456', 1), (2, 'SN789012', 2);

INSERT INTO ticket (
    email_id, subject, body, facility_id, contact_id, 
    sentiment_id, sentiment_confidence, category_id, category_confidence,
    gaz_analyzer_id, generated_response, response_method, status
) VALUES (
    'test_001', 
    'Запрос документации', 
    'Требуется руководство по эксплуатации для версии с суффиксом W00. Просьба выслать на почту.', 
    1, 1, 
    2, 0.85, 
    1, 0.92, 
    1, 
    'Уважаемый Иван Иванович! Направляем вам запрашиваемую документацию...', 
    'fallback', 
    'closed'
);

INSERT INTO ticket (
    email_id, subject, body, facility_id, contact_id, 
    sentiment_id, sentiment_confidence, category_id, category_confidence,
    gaz_analyzer_id, generated_response, response_method, status
) VALUES (
    '23', 
    'Отзыв по калибровке', 
    'Приборы ЭРИС работают безупречно, калибровка проходит гладко. Хотим обновить парк приборов.', 
    2, 2, 
    3, 0.98, 
    2, 1.0, 
    NULL, 
    'Здравствуйте, Игорь Александрович! Рады слышать, что наше оборудование вам помогает...', 
    'llm_qwen', 
    'processed'
);

INSERT INTO ticket (
    email_id, subject, body, facility_id, contact_id, 
    sentiment_id, sentiment_confidence, category_id, category_confidence,
    gaz_analyzer_id, generated_response, response_method, status
) VALUES (
    'err_404', 
    'Ошибка датчика', 
    'Датчик на объекте ГазПром перестал подавать сигнал после скачка напряжения.', 
    3, 3, 
    1, 0.91, 
    3, 0.88, 
    2, 
    'Уважаемый Петр Петрович! Технический специалист свяжется с вами в течение часа...', 
    'llm_qwen', 
    'open'
);
