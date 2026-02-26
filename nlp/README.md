pip install -r requirements.txt
python -m app.main

настроение сообщения
curl -X POST http://127.0.0.1:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "текст"}'