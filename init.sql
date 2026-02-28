
CREATE TABLE Facility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Contacts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE ticket (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(255),
    body TEXT,
    facility_id INT,
    contact_id INT,
    sentiment VARCHAR(50),
    category_id INT,
    generated_response TEXT,
    status VARCHAR(50),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (facility_id) REFERENCES Facility(id),
    FOREIGN KEY (contact_id) REFERENCES Contacts(id),
    FOREIGN KEY (category_id) REFERENCES Categories(id)
);

INSERT INTO Facility (name) VALUES ('Объект Альфа'), ('Цех №2');
INSERT INTO Contacts (full_name, email) VALUES ('Иван Иванов', 'ivan@test.ru');
INSERT INTO Categories (name, description) VALUES ('Техническое', 'Проблемы с оборудованием');

INSERT INTO ticket (subject, body, facility_id, contact_id, sentiment, category_id, status) 
VALUES ('Утечка газа', 'Зафиксировано превышение нормы CH4', 1, 1, 'negative', 1, 'open');
