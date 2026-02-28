# test_models.py
from app.models.sentiment_model import SentimentAnalyzer
from app.models.classifier_model import Classifier
from app.models.summarizer_model import SummarizerModel
from enigmahack.nlp.app.services.parser import DeviceParser

print("="*60)
print("ЗАГРУЗКА МОДЕЛЕЙ")
print("="*60)

sentiment = SentimentAnalyzer()
classifier = Classifier()
summarizer = SummarizerModel()
parser = DeviceParser()

print()

print("="*60)
print("ТЕСТ")
print("="*60)

test_emails = [
    ("Не работает прибор", "Газоанализатор не включается, дисплей не горит"),
    ("Поверка оборудования", "Нужно сделать поверку прибора СН-415"),
    ("Документация", "Пришлите руководство по эксплуатации в PDF"),
    ("Подключение к RS-485", "Как подключить к Modbus? Нужна схема"),
    ("Вопрос по цене", "Сколько стоит газоанализатор СН-415?"),
]

for subject, text in test_emails:
    sentiment_result = sentiment.predict(text, subject)
    classifier_result = classifier.predict(text, subject) 
    summarizer_result = summarizer.summarize(text, subject)
    parser_result = parser.parse_all(text, subject, "user")

    print(f"   Тема: {subject}")
    print(f"   Текст: {text[:50]}...")
    print(f"   Тональность: {sentiment_result['sentiment']} ({sentiment_result['confidence']:.2%})")
    print(f"   Категория: {classifier_result['category']} ({classifier_result['confidence']:.2%})")
    print(f"   Метод: {classifier_result['method']}")
    print(f"   Суть вопроса: {summarizer_result['summary']}")
    print(f"   Метод: {summarizer_result['method']}")
    print("-"*70)