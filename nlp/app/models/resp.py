from typing import List, Dict, Optional
from datetime import datetime
from transformers import pipeline
from app.core.config import settings
from app.core.logger import log
from app.models.base.knowledge_base import KNOWLEDGE_BASE, GENERATION_PROMPT


class ResponseGenerator:
    """
    Генератор ответов на основе LLM (Qwen)
    """
    
    def __init__(self):
        self.model_name = settings.response_name
        self.device = settings.device
        self.max_length = settings.max_length

        self.knowledge_base = KNOWLEDGE_BASE
        self.generation_model = None
        self._load_model()
        log.info("ResponseGenerator инициализирован (LLM Qwen)")
    
    def _load_model(self):
        """Загрузка Qwen модели для генерации"""
        try:
            log.info("Загрузка Qwen модели...")
            
            self.generation_model = pipeline(
                "text-generation",
                model=self.model_name,
                device=-1 if self.device == "cpu" else 0,
                max_new_tokens=self.max_length,

                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2
            )
            
            log.success("Qwen модель загружена")
        except Exception as e:
            log.error(f"Ошибка загрузки Qwen модели: {e}")
            log.info("Будет использоваться fallback-генерация")
            self.generation_model = None
    
    def _build_context(self, category: str) -> str:
        """Построение контекста из базы знаний по категории"""
        context_parts = []
        
        context_parts.append(f"Компания: {self.knowledge_base['company']['name']}")
        context_parts.append(f"Сайт: {self.knowledge_base['company']['website']}")

        if category == "документация":
            doc = self.knowledge_base["documentation"]
            context_parts.append(f"\nДокументация: {doc['description']}")
            context_parts.append(f"Включает: {', '.join(doc['includes'])}")
            
        elif category == "калибровка":
            cal = self.knowledge_base["calibration"]
            context_parts.append(f"\nПоверка: интервал {cal['interval']}")
            context_parts.append(f"Партнёры: {', '.join(cal['partners'])}")
            
        elif category == "подключение":
            conn = self.knowledge_base["connection"]
            context_parts.append(f"\nИнтерфейсы: {', '.join(conn['interfaces'])}")
            context_parts.append(f"Modbus настройки: {conn['modbus_settings']}")
            
        elif category == "неисправность":
            solutions = [s for s in self.knowledge_base["solutions"] if s["category"] == "неисправность"]
            for sol in solutions[:3]:
                context_parts.append(f"\nПроблема: {sol['problem']}")
                context_parts.append(f"Решение: {sol['solution']}")
        
        elif category == "dgs_ble":
            dgs = self.knowledge_base["dgs_ble"]
            context_parts.append(f"\nDGS BLE: {dgs['description']}")
            context_parts.append(f"Требуемые данные: {', '.join(dgs['required_data'])}")
            context_parts.append(f"Срок обработки: {dgs['processing_time']}")
        
        query_lower = ""
        for sol in self.knowledge_base["solutions"]:
            if category in sol.get("category", ""):
                context_parts.append(f"\nПохожая проблема: {sol['problem']}")
                context_parts.append(f"Решение: {sol['solution']}")
        
        return "\n".join(context_parts)
    
    def _generate_with_llm(self, prompt: str) -> str:
        """Генерация ответа через LLM"""
        if not self.generation_model:
            return None
        
        try:
            result = self.generation_model(prompt)
            generated_text = result[0]['generated_text']

            if "Составь ответ на русском языке:" in generated_text:
                response = generated_text.split("Составь ответ на русском языке:")[-1].strip()
            else:
                response = generated_text.strip()
            
            return response
            
        except Exception as e:
            log.error(f"Ошибка генерации LLM: {e}")
            return None
    
    def _generate_fallback(self, record: Dict) -> str:
        """
        Гарантированно рабочий fallback для запросов документации
        """
        fio = str(record.get("fio") or "Уважаемый клиент").split()[0]  # Только имя
        description = str(record.get("description") or "")
        device_hint = str(record.get("device_type") or "")
        
        # Поиск в KB
        doc_info = self._search_documentation(description, device_hint)
        
        # Заголовок
        response = f"Уважаемый(ая) {fio}!\n\n"
        
        # Тело ответа
        if doc_info.get("unknown_device"):
            response += f"""По запросу документации для "{device_hint}":

К сожалению, в нашей базе знаний не найдено оборудования с названием "{device_hint}". 
Возможно, имеется в виду одна из следующих моделей ЭРИС:
"""
            # Предложить похожие устройства
            products = self.knowledge_base.get("products", {})
            suggestions = [p.get("name") for k, p in products.items() 
                         if "ir" in k or "ch4" in str(p.get("detectable_gases", "")).lower()]
            for sug in suggestions[:3]:
                response += f"• {sug}\n"
            response += "\n"
        else:
            response += f"""Актуальные руководства по эксплуатации, паспорта изделий и перечни запасных частей (ЗИП) 
доступны в открытом доступе в библиотеке файлов:

🔗 {doc_info.get("url") or "https://eriskip.com/ru/files-library"}

В разделе доступны:
• Руководства по эксплуатации (РЭ) и паспорта
• Перечни запасных частей с рекомендуемыми сроками замены
• Методики поверки, сертификаты, 3D-модели
"""
        
        # Если запрошено конкретное — предложить уточнение
        if "газконтроль" in description.lower() or "01" in description:
            response += """
❗ Обратите внимание: оборудование с названием "Газконтроль-01" не входит 
в линейку продукции ООО «ЭРИС». Возможно, требуется документация на:
• ДГС ЭРИС-210 IR (метан CH4)
• ДГС ЭРИС-230 IR
• Advant IR

Для точного подбора документации укажите, пожалуйста, заводской номер прибора 
или пришлите фото шильдика.
"""
        
        # Контакты — ОДИН раз, в конце
        company = self.knowledge_base.get("company", {})
        support = company.get("support", {})
        response += f"""
─────────────────────────────
📞 Техподдержка: {support.get("phone", "8-800-55-00-715")}
📧 Email: {support.get("email", "service@eriskip.ru")}
🌐 Каталог: {company.get("products_url", "https://eriskip.com/ru/products")}

С уважением,
Служба технической поддержки ООО «ЭРИС»
"""
        return response
    
    def generate(self, record) -> dict:
        log.info("Генерация ответа (LLM Qwen)...")
    
        category = record.get('category') or "другое"
        context = self._build_context(category)
        
        prompt = GENERATION_PROMPT.format(
            context=context,
            fio=record.get('fio') or "Клиент",
            object_name=record.get('object_name') or "не указано",
            phone=record.get('phone') or "не указан",
            email=record.get('email') or "не указан",
            device_type=record.get('device_type') or "прибор ЭРИС",
            category=category,
            sentiment=record.get('sentiment') or "neutral",
            description=record.get('description') or "вопрос"
        )
        
        generated_response = None
        method = "fallback"
        
        if self.generation_model:
            log.info("  Генерация через Qwen LLM...")
            generated_response = self._generate_with_llm(prompt)
            if generated_response and len(generated_response) > 50:
                method = "llm_qwen"
                log.success("   Ответ сгенерирован Qwen LLM")
        
        if not generated_response or len(generated_response) < 50:
            log.info("  Fallback генерация на основе контекста...")
            generated_response = self._generate_fallback(record)
            method = "fallback"
        
        subject = f"RE: {getattr(record, 'email_id', 'Обращение')} | {record.get('category') or 'Вопрос'}"
        
        log.success(f"Ответ сгенерирован (метод: {method})")
        
        return {
            'subject': subject,
            'body': generated_response,
            'category': record.get('category') or "другое",
            'method': method,
            'generated_at': datetime.now().isoformat(),
        }
    
    def __call__(self, record) -> dict:
        return self.generate(record)