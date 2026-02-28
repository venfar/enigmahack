import re
from app.core.config import settings
from app.core.logger import log
from app.models.base.problem_keywords import PROBLEM_KEYWORDS

class SummarizerModel:    
    MAX_LENGTH = 200
    SENTENCES_COUNT = 2
    PROBLEM_KEYWORDS = PROBLEM_KEYWORDS
    def __init__(self):
        log.info("Суммаризатор инициализирован")
        log.success("Суммаризатор готов к работе")

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _split_sentences(self, text: str) -> list:
        if not text:
            return []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _find_problem_sentence(self, sentences: list) -> str:
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in self.PROBLEM_KEYWORDS:
                if keyword in sentence_lower:
                    return sentence
        return ""

    def summarize(self, text: str, subject: str = "") -> dict:
        if not text:
            return {'summary': '', 'method': 'empty'}
        
        text = self._clean_text(text)
        sentences = self._split_sentences(text)
        
        # 1. Если тема информативная — используем её
        if subject and 10 <= len(subject) <= 100:
            log.debug(f"Суть из темы: {subject}")
            return {'summary': subject, 'method': 'subject'}
        
        # 2. Ищем предложение с ключевыми словами
        if sentences:
            problem_sentence = self._find_problem_sentence(sentences)
            if problem_sentence and len(problem_sentence) >= 20:
                if len(problem_sentence) > self.MAX_LENGTH:
                    problem_sentence = problem_sentence[:self.MAX_LENGTH - 3] + "..."
                log.debug(f"Суть из ключевого предложения: {problem_sentence[:50]}...")
                return {'summary': problem_sentence, 'method': 'keywords'}
        
        # 3. Берём первые 1-2 предложения
        if sentences:
            summary = ' '.join(sentences[:self.SENTENCES_COUNT])
            if len(summary) > self.MAX_LENGTH:
                summary = summary[:self.MAX_LENGTH - 3] + "..."
            log.debug(f"📝 Суть из первых предложений: {summary[:50]}...")
            return {'summary': summary, 'method': 'sentences'}
        
        # 4. Fallback
        summary = text[:self.MAX_LENGTH]
        if len(text) > self.MAX_LENGTH:
            summary += "..."
        
        return {'summary': summary, 'method': 'fallback'}

    def __call__(self, text: str, subject: str = "") -> dict:
        return self.summarize(text, subject)