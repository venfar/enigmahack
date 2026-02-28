SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE DATABASE IF NOT EXISTS enigma_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE enigma_db;

CREATE TABLE Facility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
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
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Gas_analyzer_type (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE Gas_analyzer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    type_id INT,
    FOREIGN KEY (type_id) REFERENCES Gas_analyzer_type(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ticket (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_id VARCHAR(100),                
    subject VARCHAR(255),                 
    body MEDIUMTEXT,                      
    
    facility_id INT,                      
    contact_id INT,                       
    
    sentiment VARCHAR(50),                
    sentiment_confidence FLOAT,          
    
    category_id INT,                      
    category_confidence FLOAT,            
    
    gaz_analyzer_id INT,                  
    
    response_subject VARCHAR(255),        
    generated_response MEDIUMTEXT,        
    response_method VARCHAR(50),         
    
    status VARCHAR(50) DEFAULT 'open',    
    
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
    processed_at TIMESTAMP NULL,                     
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (facility_id) REFERENCES Facility(id),
    FOREIGN KEY (contact_id) REFERENCES Contacts(id),
    FOREIGN KEY (category_id) REFERENCES Categories(id),
    FOREIGN KEY (gaz_analyzer_id) REFERENCES Gas_analyzer(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO Facility (name) VALUES ('ООО «ТестГаз»'), ('ХимТех'), ('Объект Альфа');
INSERT INTO Categories (name) VALUES ('документация'), ('калибровка'), ('техническое');
INSERT INTO Gas_analyzer_type (type) VALUES ('ДГС ЭРИС-230'), ('Стационарный');
INSERT INTO Gas_analyzer (serial_number, type_id) VALUES ('SN123456', 1);
INSERT INTO Contacts (full_name, email, phone) VALUES 
('Иванов Иван Иванович', 'test@testgaz.ru', '+7 (495) 123-45-67'),
('Danil Babikov', 'i.volkov@himtech.ru', '+7 (921) 222-33-44');

INSERT INTO ticket (
    email_id, subject, body, facility_id, contact_id, 
    sentiment, sentiment_confidence, category_id, category_confidence,
    gaz_analyzer_id, response_subject, generated_response, response_method, status
) VALUES 
(
    'test_001', 
    'Запрос документации', 
    'Требуется руководство по эксплуатации для версии с суффиксом W00', 
    1, 1, 
    'neutral', 0.85, 
    1, 0.92, 
    1, 
    'RE: test_001 | документация', 
    'Уважаемый(ая) Иванов Иван Иванович! Благодарим за обращение...', 
    'fallback', 
    'closed'
),
(
    '23', 
    'Обращение по калибровке', 
    'Приборы ЭРИС работают безупречно, калибровка проходит гладко...', 
    2, 2, 
    'positive', 0.9654, 
    2, 1.0, 
    NULL, 
    'RE: Обращение | калибровка', 
    'Здравствуйте, добрый учителок! Я понял вас с первого раза...', 
    'llm_qwen', 
    'processed'
);
