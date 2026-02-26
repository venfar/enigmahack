from transformers import pipeline

classifier = pipeline("sentiment-analysis", 
                      model="blanchefort/rubert-base-cased-sentiment")

test_texts = [
    "Газоанализатор сломался через день после покупки! Это просто ужас!",
    "Спасибо за быструю замену прибора, всё работает отлично",
    "Подскажите, пожалуйста, когда будет калибровка датчиков?"
]

for text in test_texts:
    result = classifier(text)
    print(f"Текст: {text}")
    print(f"Результат: {result[0]}\n")