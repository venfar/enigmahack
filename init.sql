SET NAMES utf8mb4;
ALTER DATABASE enigma_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE Facility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Gas_analyzer_type (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Gas_analyzer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) NOT NULL,
    type_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES Gas_analyzer_type(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ticket (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(255),
    body TEXT,
    facility_id INT,
    contact_id INT,
    sentiment VARCHAR(50),
    category_id INT,
    generated_response TEXT,
    response_sent_at TIMESTAMP NULL,
    status VARCHAR(50) DEFAULT 'open',
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES Facility(id),
    FOREIGN KEY (contact_id) REFERENCES Contacts(id),
    FOREIGN KEY (category_id) REFERENCES Categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Facility (name) VALUES 
('Объект Альфа'), 
('Цех №2'), 
('Склад готовой продукции');

INSERT INTO Contacts (full_name, email, phone) VALUES 
('Иван Иванов', 'ivan@enigma.ru', '+79001112233'),
('Петр Петров', 'petr@enigma.ru', '+79004445566');

INSERT INTO Categories (name, description) VALUES 
('Техническое', 'Проблемы с оборудованием и датчиками'),
('Безопасность', 'Вопросы пожарной и газовой безопасности');

INSERT INTO Gas_analyzer_type (type) VALUES 
('Стационарный'), 
('Переносной');

INSERT INTO ticket (subject, body, facility_id, contact_id, sentiment, category_id, status) 
VALUES 
('Утечка газа', 'Зафиксировано превышение нормы CH4 в северном крыле.', 1, 1, 'negative', 1, 'open'),
('Проверка связи', 'Плановое тестирование системы оповещения.', 2, 2, 'neutral', 2, 'closed'),
('Ошибка датчика', 'Датчик №402 выдает некорректные значения температуры.', 1, 1, 'negative', 1, 'in_progress');
