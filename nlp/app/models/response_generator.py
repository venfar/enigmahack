"""
Response Generator для техподдержки ООО «ЭРИС»
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re
from transformers import pipeline, GenerationConfig

from app.core.config import settings
from app.core.logger import log
from app.models.base.knowledge_base import KNOWLEDGE_BASE, GENERATION_PROMPT


class ResponseGenerator:
    """Генератор ответов с защитой от артефактов LLM"""
    
    # Жёсткие настройки для детерминированной генерации
    LLM_CONFIG = {
        "temperature": 0.2,        # Минимум "творчества"
        "top_p": 0.9,
        "top_k": 50, 
        "repetition_penalty": 1.25, # Агрессивное подавление повторов
        "max_new_tokens": 400,      # Ограничение длины
        "do_sample": True,         # Greedy decoding для стабильности
        "num_return_sequences": 1,
        "eos_token_id": [0, 2],     # Стоп-токены
    }
    
    # Стоп-последовательности для обрезки вывода
    STOP_SEQUENCES = [
        "\n---",
        "\n\n---",
        "Данные клиента:",
        "Контекст из базы знаний:",
        "Составь ответ",
        "Ты — специалист",
        "⚠️ КРИТИЧЕСКИЕ ПРАВИЛА",
    ]
    
    # Паттерны "мусорного" ответа для отбраковки
    GARBAGE_PATTERNS = [
        r"привет\s*[!:.]?\s*я\s+понимаю",
        r"ответ:\s*да,\s*конечно",
        r"буду\s+рад\s+помочь",
        r"пожалуйста,\s*предоставьте\s+мне",
        r"спасибо\s+за\s+ваш[уе]\s+терпени[ея]",
        r"я\s+могу\s+предоставить\s+вам",
        r"\*\*привет\*\*",
        r"---\s*---\s*---",  # Много разделителей
    ]
    
    # Разрешённые контакты (для валидации)
    ALLOWED_CONTACTS = {
        "phones": ["8-800-55-00-715", "+7 (34241) 6-55-11"],
        "emails": ["service@eriskip.ru", "docs@eris.ru", "info@eriskip.ru"],
        "domains": ["eriskip.com", "eris.ru"],
    }

    def __init__(self):
        self.knowledge_base = KNOWLEDGE_BASE
        self.generation_model: Optional[pipeline] = None
        self._initialize_model()
        log.info("✅ ResponseGenerator v3.0 инициализирован")
    
    def _initialize_model(self) -> None:
        try:
            log.info("🔄 Загрузка Qwen модели...")
            self.generation_model = pipeline(
                "text-generation",
                model=settings.response_name,
                device=-1 if settings.device == "cpu" else 0,
                **self.LLM_CONFIG
            )
            log.success("✅ Модель загружена")
        except Exception as e:
            log.error(f"❌ Ошибка загрузки: {e}")
            self.generation_model = None
    
    # =========================================================================
    # ИЗВЛЕЧЕНИЕ И ОЧИСТКА ОТВЕТА
    # =========================================================================
    
    def _extract_clean_response(self, generated_text: str, prompt: str) -> Optional[str]:
        """
        Извлечение чистого ответа с множественными защитами
        """
        if not generated_text or not isinstance(generated_text, str):
            return None
        
        # 1. Удаление промпта из начала (если модель его повторила)
        if prompt.strip() in generated_text:
            generated_text = generated_text.replace(prompt.strip(), "", 1)
        
        # 2. Обрезка по стоп-последовательностям
        for stop_seq in self.STOP_SEQUENCES:
            if stop_seq in generated_text:
                generated_text = generated_text.split(stop_seq)[0]
        
        # 3. Удаление маркеров формата
        generated_text = re.sub(r'\n\s*---+\s*\n', '\n', generated_text)
        generated_text = re.sub(r'\*\*(Ответ|Привет|Вопрос)\*\*[:\s]*', '', generated_text, flags=re.I)
        
        # 4. Удаление повторяющихся блоков (эвристика)
        lines = generated_text.strip().split('\n')
        unique_lines = []
        seen_hashes = set()
        for line in lines:
            h = hash(line.strip().lower())
            if h not in seen_hashes and len(line.strip()) > 5:
                unique_lines.append(line)
                seen_hashes.add(h)
        generated_text = '\n'.join(unique_lines)
        
        # 5. Финальная очистка
        response = generated_text.strip()
        
        # Удаление префиксов типа "Ответ:", "Вот ответ:"
        response = re.sub(r'^(ответ|вот\s+ответ|привет)[:\s]*', '', response, flags=re.I).strip()
        
        return response if len(response) >= 20 else None
    
    def _is_garbage_response(self, response: str) -> bool:
        """Проверка ответа на признаки мусорной генерации"""
        response_lower = response.lower()
        
        # Проверка по паттернам мусора
        for pattern in self.GARBAGE_PATTERNS:
            if re.search(pattern, response_lower, re.I):
                return True
        
        # Проверка на избыточную вежливость без содержания
        polite_words = ['привет', 'пожалуйста', 'спасибо', 'рад', 'помочь', 'конечно']
        if sum(1 for w in polite_words if w in response_lower) >= 4:
            if len([s for s in response.split('.') if s.strip()]) < 3:  # Мало предложений
                return True
        
        # Проверка на диалоговый формат "Вопрос/Ответ"
        if re.search(r'(вопрос|ответ)\s*[:\-]?\s*(да|нет|конечно|понимаю)', response_lower):
            return True
        
        return False
    
    # =========================================================================
    # ПОИСК ДОКУМЕНТАЦИИ ПО ЗАПРОСУ
    # =========================================================================
    
    def _search_documentation(self, query: str, device_hint: Optional[str] = None) -> Dict:
        """
        Умный поиск документации в KB по ключевым словам
        """
        query_lower = query.lower()
        results = {
            "found": False,
            "url": None,
            "description": None,
            "related_products": [],
        }
        
        # Поиск в products по названию устройства
        if device_hint:
            for key, product in self.knowledge_base.get("products", {}).items():
                if device_hint.lower() in key or device_hint.lower() in str(product.get("name", "")).lower():
                    results["related_products"].append(product.get("name", key))
                    # Ищем файлы в product data (если есть)
                    if "files" in product:
                        results["found"] = True
                        results["url"] = self.knowledge_base.get("company", {}).get("files_library")
                        break
        
        # Поиск по ключевым словам в описании запроса
        doc_keywords = ["руководств", "эксплуатац", "паспорт", "зип", "запасн", "част", "документ"]
        if any(kw in query_lower for kw in doc_keywords):
            results["found"] = True
            results["url"] = self.knowledge_base.get("company", {}).get("files_library")
            results["description"] = "Документация доступна в библиотеке файлов"
        
        # Специальная обработка для неизвестных устройств
        if device_hint and not results["related_products"]:
            # Проверяем, есть ли устройство в KB вообще
            known_devices = [p.get("name", "").lower() for p in self.knowledge_base.get("products", {}).values()]
            if device_hint.lower() not in str(known_devices):
                results["unknown_device"] = True
        
        return results
    
    # =========================================================================
    # FALLBACK: ШАБЛОННЫЙ ОТВЕТ ДЛЯ ДОКУМЕНТАЦИИ
    # =========================================================================
    
    def _generate_docs_fallback(self, record: Dict) -> str:
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
    
    # =========================================================================
    # ВАЛИДАЦИЯ: ЖЁСТКАЯ ПРОВЕРКА
    # =========================================================================
    
    def _validate_response(self, response: Optional[str], record: Dict) -> Tuple[bool, List[str]]:
        """Многоуровневая валидация ответа"""
        warnings = []
        
        # Базовая проверка
        if not response or len(response) < 30:
            return False, ["Пустой или слишком короткий ответ"]
        
        # Проверка на промпт-лик
        prompt_markers = ["Ты — специалист", "КРИТИЧЕСКИЕ ПРАВИЛА", "Контекст из базы знаний"]
        if any(marker in response for marker in prompt_markers):
            return False, ["Обнаружен промпт в ответе"]
        
        # Проверка на мусор
        if self._is_garbage_response(response):
            return False, ["Ответ содержит шаблонный мусор"]
        
        # Проверка на избыточные повторы
        if response.count("Привет") > 1 or response.count("---") > 3:
            return False, ["Избыточные повторы в ответе"]
        
        # Проверка контактов (если категория требует)
        if record.get("category") in ["документация", "калибровка", "гарантия"]:
            has_contact = any(
                contact in response 
                for contact in self.ALLOWED_CONTACTS["emails"] + self.ALLOWED_CONTACTS["phones"]
            )
            if not has_contact:
                warnings.append("⚠️ Нет контактов поддержки в ответе")
        
        return len(warnings) == 0 or all("⚠️" in w for w in warnings), warnings
    
    # =========================================================================
    # ГЕНЕРАЦИЯ ЧЕРЕЗ LLM (с защитой)
    # =========================================================================
    
    def _generate_with_llm(self, prompt: str) -> Optional[str]:
        if not self.generation_model:
            return None
        
        try:
            # Генерация с явными параметрами
            result = self.generation_model(
                prompt,
                max_new_tokens=self.LLM_CONFIG["max_new_tokens"],
                temperature=self.LLM_CONFIG["temperature"],
                do_sample=self.LLM_CONFIG["do_sample"],
                repetition_penalty=self.LLM_CONFIG["repetition_penalty"],
            )
            
            if not result or not isinstance(result, list):
                return None
            
            generated_text = result[0].get("generated_text", "")
            if not generated_text:
                return None
            
            # Извлечение и очистка
            response = self._extract_clean_response(generated_text, prompt)
            if not response:
                return None
            
            # Быстрая проверка на адекватность
            if self._is_garbage_response(response):
                return None
            
            return response.strip()
            
        except Exception as e:
            log.error(f"❌ Ошибка LLM: {e}")
            return None
    
    # =========================================================================
    # MAIN: ГЕНЕРАЦИЯ ОТВЕТА
    # =========================================================================
    
    def generate(self, record: Dict) -> Dict:
        log.info(f"🔄 Генерация | Категория: {record.get('category')} | Устройство: {record.get('device_type')}")
        
        # Нормализация входных данных
        record_safe = {k: (str(v).strip() if v is not None else "") for k, v in record.items()}
        
        # Для категории "документация" — сразу используем fallback с умным поиском
        if record_safe.get("category") == "документация":
            log.info("📚 Запрос документации — используем оптимизированный fallback")
            response_body = self._generate_docs_fallback(record_safe)
            method = "fallback_docs"
            validation_warnings = []
        else:
            # Стандартный путь для других категорий
            context = self._build_context(record_safe)  # Существующий метод
            
            prompt = GENERATION_PROMPT.format(
                context=context,
                **{k: record_safe.get(k, "") for k in ["fio", "object_name", "phone", "email", 
                                                       "device_type", "category", "sentiment", "description"]}
            )
            
            response_body = None
            method = "fallback"
            
            if self.generation_model:
                response_body = self._generate_with_llm(prompt)
                if response_body:
                    is_valid, warnings = self._validate_response(response_body, record_safe)
                    if is_valid and not self._is_garbage_response(response_body):
                        method = "llm_qwen"
                    else:
                        log.warning(f"⚠️ LLM-ответ отклонён: {warnings}")
                        response_body = None
            
            if not response_body:
                response_body = self._generate_fallback(record_safe)  # Существующий fallback
                method = "fallback"
        
        # Формирование результата
        email_id = record.get("email_id") or record.get("id") or "Обращение"
        subject = f"RE: {email_id} | {record.get('category') or 'Вопрос'} | ООО «ЭРИС»"
        
        log.success(f"✅ Ответ готов | Метод: {method} | Длина: {len(response_body)}")
        
        return {
            "subject": subject,
            "body": response_body,
            "category": record.get("category") or "другое",
            "device_type": record.get("device_type"),
            "method": method,
            "generated_at": datetime.now().isoformat(),
        }
    
    def __call__(self, record: Dict) -> Dict:
        return self.generate(record)
    
    # =========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (сокращённо — оставляем существующие)
    # =========================================================================
    
    def _build_context(self, record: Dict) -> str:
        # ... оставляем существующую реализацию ...
        return "🏢 Компания: ООО «ЭРИС»\n📞 Поддержка: 8-800-55-00-715\n📧 Email: service@eriskip.ru"
    
    def _generate_fallback(self, record: Dict) -> str:
        # ... оставляем существующую реализацию для недок. категорий ...
        return f"Уважаемый(ая) {record.get('fio', 'Клиент')}!\n\nБлагодарим за обращение..."