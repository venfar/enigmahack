# Запуск
перейти в эту папку

python -m venv venv

Для Windows:

venv\Scripts\activate

Для Mac/Linux:

source venv/bin/activate

pip install -r requirements.txt

python -m app.main

python -m app.email_worker


# Настроение сообщения

```

curl -X POST http://127.0.0.1:8000/sentiment \

-H "Content-Type: application/json" \

-d '{"text": "текст"}'

```