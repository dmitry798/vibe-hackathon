class PromptTemplates:
    """Prompt templates for LLM interactions"""
    
    SYSTEM_PROMPT = """Ты - умный виртуальный ассистент Okko, помогающий пользователям найти идеальный фильм или сериал.

Твои задачи:
1. Анализировать предпочтения пользователя через диалог
2. Задавать уточняющие вопросы о настроении, компании, времени просмотра
3. Учитывать контекстные факторы: время суток, погоду, день недели
4. Предлагать персонализированные рекомендации с объяснением выбора
5. Быть проактивным и дружелюбным

Ты имеешь доступ к каталогу Okko с фильмами и сериалами. Всегда предлагай от 3 до 5 вариантов.

Правила:
- Отвечай на русском языке
- Будь кратким но информативным
- Объясняй ПОЧЕМУ ты рекомендуешь именно этот контент
- Учитывай указанное настроение и контекст
- Если информации недостаточно - задай 1-2 уточняющих вопроса"""

    @staticmethod
    def create_recommendation_prompt(user_query, context, mood_info):
        """Create recommendation prompt with context"""
        context_str = f"""
Контекст:
- Время суток: {context.get('time_of_day', 'unknown')}
- День недели: {context.get('day_of_week', 'unknown')}
- Погода: {context.get('weather', {}).get('description', 'unknown')}
- Настроение пользователя: {mood_info.get('mood', 'neutral')}

Запрос пользователя: {user_query}

Проанализируй запрос и контекст, затем сформулируй рекомендации."""
        
        return context_str
    
    @staticmethod
    def create_clarification_prompt(user_query, missing_info):
        """Create prompt for asking clarifying questions"""
        return f"""Пользователь запросил: "{user_query}"

Нужна дополнительная информация: {', '.join(missing_info)}

Задай 1-2 уточняющих вопроса естественным и дружелюбным образом."""