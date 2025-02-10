"""
Стоп-слова для фильтрации SEO вакансий
"""

STOP_WORDS = {
    'pbn',
    'агентство',
    'англоговорящие',
    'digital-агентство',
    'seo-компания',
    'линкбилдер',
    'performance-агенство',
    'igaming',
    'дроп домен',
    'seo-агентство',
    'маркетинговое агентство',
    'английский b',
    'linkbuild',
    'кибер',
    'крипто',
    'беттинг',
    'букмекер',
    'бурж',
    'гэмблинг',
    'трейдинг',
    'web3',
}

def contains_stop_words(text: str) -> bool:
    """
    Проверяет, содержит ли текст стоп-слова
    
    Args:
        text: Текст для проверки
        
    Returns:
        bool: True если найдены стоп-слова, False иначе
    """
    text = text.lower()
    return any(word in text for word in STOP_WORDS)
