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
http://0.0.0.0:8000/api/v1/health
http://0.0.0.0:8000/api/v1/tickets
http://0.0.0.0:8000/api/v1/tickets/{email_id}
http://0.0.0.0:8000/api/v1/stats

```