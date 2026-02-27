CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE request_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INTEGER,
    request_text TEXT NOT NULL,
    response_text TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO users (username) VALUES 
('pro'),
('enigma_bot'),
('student'),
('user');

INSERT INTO request_history (user_id, request_text, response_text, status) VALUES
(1, 'Ubuntu', 'nginx', 'success'),
(1, 'Прокси', 'Сервер', 'success'),
(2, 'Сложный пароль', 'hK9!pL2_sA01x', 'success'),
(3, 'БД?', 'Тест', 'error'),
(4, 'Логи!', 'Генерация', 'success');

