"""
Translation module for multi-language support.
Provides English (default) and Russian translations for the UI.
"""
from typing import Dict

# Available languages
LANGUAGES = {
    "en": "English",
    "ru": "Русский"
}

# Default language
DEFAULT_LANGUAGE = "en"

# Translations dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Page configuration
        "page_title": "PDF Translation Cost Calculator",
        "page_icon": "📚",
        
        # Main UI
        "upload_prompt": "Upload an Arabic PDF book to calculate translation costs across multiple LLM providers.",
        "choose_pdf_file": "Choose a PDF file",
        "upload_help": "Upload a single PDF file for translation cost estimation",
        
        # Sidebar
        "sidebar_settings": "Settings",
        "sidebar_info": "Upload a PDF file to get started. The app will calculate token counts and cost estimates for translation to Russian.",
        "token_counting": "Token Counting",
        "token_counting_info": "✅ All token counting is **100% free** and done locally. No API keys or credits required!",
        "token_counting_note": "Token counts use free local calculations. OpenAI and DeepL are exact; Anthropic and Google are close approximations.",
        
        # Language selector
        "language": "Language",
        "select_language": "Select Language",
        
        # Processing messages
        "extracting_text": "Extracting text from PDF...",
        "pdf_processed": "✅ PDF processed successfully!",
        "pages": "Pages",
        "characters": "Characters",
        "words": "Words",
        "calculating_tokens": "Calculating token counts for all providers (free, local calculation)...",
        "calculating_costs": "Calculating cost estimates...",
        
        # Token counts section
        "token_counts_title": "📊 Token Counts by Provider",
        "token_counts_caption": "All calculations are free and done locally. OpenAI models are exact; others are close approximations.",
        "exact": "✅ Exact",
        "approximate": "⚠️ Approximate",
        "error": "Error",
        
        # Cost comparison section
        "cost_comparison_title": "💰 Cost Comparison",
        "cost_comparison_caption": "Estimated costs for translating the entire document (Arabic → Russian)",
        "provider": "Provider",
        "model": "Model",
        "input_tokens": "Input Tokens",
        "output_tokens_est": "Output Tokens (est.)",
        "input_cost": "Input Cost ($)",
        "output_cost": "Output Cost ($)",
        "total_cost": "Total Cost ($)",
        "cheapest_option": "💡 **Cheapest option**: {provider} {model} at **${cost}**",
        "cost_range": "Cost range: ${min} - ${max} (difference: ${diff})",
        
        # Translation section
        "translate_title": "🚀 Translate with Selected LLM",
        "translate_with": "Translate with {model}",
        "translate": "Translate",
        "action": "Action",
        "total_cost_label": "Total cost: ${cost}",
        "not_implemented": " (Not yet implemented)",
        "using_api_key": "🔑 Using API key: {api_key}",
        "confirm_translation": "⚠️ Confirm Translation",
        "estimated_cost": "**Estimated Cost**: ${cost}",
        "provider_label": "**Provider**: {provider} {model}",
        "translation_note": "This will translate the entire document paragraph by paragraph. This may take several minutes.",
        "start_translation": "✅ Start Translation",
        "starting_translation": "🚀 Starting translation...",
        "translation_progress": "📊 Translation Progress",
        "translating_paragraph": "🔄 Translating paragraph {current} of {total}...",
        "generating_pdf": "📄 Generating PDF...",
        "translation_completed": "✅ Translation completed successfully!",
        
        # Translation results
        "translation_results_title": "📄 Translation Results",
        "pdf_saved_to": "📁 PDF saved to: `{path}`",
        "pdf_saved_temp": "📁 PDF saved to temporary directory: `{path}`",
        "pdf_saved_tip": "💡 Tip: Set `PDF_OUTPUT_DIR` in your `.env` file to save PDFs to a custom location",
        "preview_label": "Preview (first 500 characters):",
        "download_pdf": "📥 Download Translated PDF",
        
        # Error messages
        "no_text_extracted": "No text could be extracted from the PDF. The file might be image-based or corrupted.",
        "api_key_missing": "API key not found. Please set the required API key in your `.env` file.",
        "api_key_info": "💡 Please set `GOOGLE_API_KEY` in your `.env` file or as an environment variable",
        "authentication_error": "❌ Authentication Error: {error}",
        "troubleshooting_title": "**Troubleshooting API Key Issues:**",
        "troubleshooting_1": "1. **Verify your API key** is correct in your `.env` file",
        "troubleshooting_2": "2. **Check API key permissions**: Ensure the key has access to the Generative Language API",
        "troubleshooting_3": "3. **Regenerate if needed**: Get a new API key from [Google AI Studio](https://makersuite.google.com/app/apikey)",
        "troubleshooting_4": "4. **Enable APIs**: Make sure the Generative Language API is enabled in your Google Cloud project",
        "troubleshooting_5": "5. **Check for whitespace**: Ensure there are no extra spaces in your `.env` file around the key",
        "missing_package": "❌ Missing Package: {error}",
        "install_packages": "💡 Please install required packages: `pip install -e .`",
        "rate_limit_exceeded": "❌ Rate Limit Exceeded",
        "rate_limit_warning": "⚠️ You've hit the API rate limit. Please wait a few minutes and try again.",
        "network_error": "❌ Network Error",
        "network_warning": "⚠️ Network connection issue. Please check your internet connection and try again.",
        "translation_failed": "❌ Translation Failed: {error}",
        "error_details": "🔍 Error Details",
        "translation_error": "❌ Translation Error: {error}",
        "pdf_not_found": "❌ PDF file not found. Please try uploading again.",
        "error_processing_pdf": "❌ Error processing PDF: {error}",
        "pdf_corrupted": "💡 The PDF file might be corrupted or in an unsupported format. Try a different PDF file.",
        "permission_denied": "💡 Permission denied. Make sure the file is not open in another application.",
        "technical_details": "🔍 Technical Details",
        "not_implemented_info": "🚧 Translation with **{provider} {model}** is not yet implemented. This feature will be added soon! Estimated cost: ${cost}",
        
        # No file uploaded
        "no_file_uploaded": "👆 Please upload a PDF file to get started.",
        "how_to_use": "How to use this app",
        "how_to_1": "1. **Upload PDF**: Click the file uploader above and select your Arabic PDF book",
        "how_to_2": "2. **View Statistics**: See page count, character count, and word count",
        "how_to_3": "3. **Check Token Counts**: View token counts for each LLM provider",
        "how_to_4": "4. **Compare Costs**: Review the cost comparison table to see pricing for each provider",
        "how_to_5": "5. **Select Provider**: Choose your preferred LLM and click the translate button (coming soon)",
        "how_to_note": "**Note**: Token counting is free and happens locally. You only pay when you actually translate.",
        
        # Additional UI elements
        "sidebar_language_title": "Language",
        "sidebar_about_title": "About",
        "sidebar_token_counting_title": "Token Counting",
        "sidebar_tip": "💡 **Tip:** All token calculations are free and done locally. No API costs until you translate!",
        "select_provider_title": "Select Provider to Translate",
        "select_provider_caption": "Click a button below to start translation with your chosen provider",
        "translation_in_progress_info": "⏳ Translation in progress... Table collapsed to focus on progress.",
        "estimated_cost_info": "💰 **Estimated Cost:** ${cost} | **Provider:** {provider} {model}",
        "start_translation_button": "🚀 Start Translation",
        "live_translation_title": "Live Translation Preview",
        "live_translation_caption": "Watch the translation appear in real-time as it's generated",
        "translation_stats": "Translation Stats",
        "welcome_title": "Welcome to PDF Translation Cost Calculator",
        "welcome_description": "**Get instant cost estimates** for translating your PDF documents across multiple AI providers before you commit.",
        "welcome_features_title": "✨ Key Features:",
        "welcome_quick_start_title": "💡 Quick Start:",
        "welcome_quick_start_1": "1. Upload a PDF file",
        "welcome_quick_start_2": "2. View cost estimates",
        "welcome_quick_start_3": "3. Choose a provider",
        "welcome_quick_start_4": "4. Download translated PDF",
        "features_title": "Features",
        "features_free_estimates_title": "Free Estimates",
        "features_free_estimates_1": "No API costs",
        "features_free_estimates_2": "Local calculations",
        "features_free_estimates_3": "Instant results",
        "features_compare_title": "Compare Providers",
        "features_compare_1": "Multiple LLM options",
        "features_compare_2": "Side-by-side pricing",
        "features_compare_3": "Best value highlighted",
        "features_live_title": "Live Translation",
        "features_live_1": "Real-time streaming",
        "features_live_2": "Progress tracking",
        "features_live_3": "Live preview",
        "features_pdf_title": "PDF Output",
        "features_pdf_1": "Professional formatting",
        "features_pdf_2": "Preserved structure",
        "features_pdf_3": "Ready to download",
        
        # Metrics and stats
        "metric_start_time": "Start Time",
        "metric_end_time": "End Time",
        "metric_duration": "Duration",
        "metric_total_paragraphs": "Total Paragraphs",
        "metric_characters": "Characters",
        "metric_words": "Words",
        "metric_paragraphs": "Paragraphs",
        "metric_speed": "Speed",
        "metric_avg_speed": "Avg Speed",
        "metric_total_characters": "Total Characters",
        "metric_total_words": "Total Words",
        "metric_cheapest": "Cheapest",
        "metric_most_expensive": "Most Expensive",
        "metric_cost_range": "Cost Range",
        "metric_eta": "ETA",
        "chars_per_sec": "chars/s",
        "coming_soon": "Coming Soon",
        "best_value": "Best Value",
        "step_by_step_guide": "Step-by-Step Guide:",
        "translation_preview_title": "Translation Preview",
        "waiting_for_translation": "Waiting for translation to start...",
        "preview_help_text": "First 1000 characters of the translated text",
        
        # Progress and resume
        "progress_found": "Found existing translation progress",
        "progress_status": "{completed} of {total} paragraphs translated ({percent}%)",
        "last_updated": "Last updated: {timestamp}",
        "resume_translation": "Resume Translation",
        "start_fresh": "Start Fresh",
        "resuming_from": "Resuming from paragraph {index}",
        "progress_saved": "Progress saved after paragraph {index}",
        "download_partial_pdf": "Download Partial PDF ({completed}/{total} paragraphs)",
        "partial_pdf_title": "Partial Translation - {completed} of {total} paragraphs",
        "partial_pdf_note": "This is a partial translation. {completed} of {total} paragraphs have been translated.",
        "generating_partial_pdf": "Generating partial PDF...",
        "stop_translation": "⏹️ Stop Translation",
        "resume_translation_button": "▶️ Resume Translation",
        "translation_stopped": "⏸️ Translation Stopped",
        "translation_stopped_message": "Translation was stopped. Progress has been saved. You can resume from where you left off.",
    },
    "ru": {
        # Page configuration
        "page_title": "Калькулятор стоимости перевода PDF",
        "page_icon": "📚",
        
        # Main UI
        "upload_prompt": "Загрузите арабскую PDF-книгу для расчета стоимости перевода с помощью различных LLM-провайдеров.",
        "choose_pdf_file": "Выберите PDF файл",
        "upload_help": "Загрузите один PDF файл для оценки стоимости перевода",
        
        # Sidebar
        "sidebar_settings": "Настройки",
        "sidebar_info": "Загрузите PDF файл, чтобы начать. Приложение рассчитает количество токенов и оценку стоимости перевода на русский язык.",
        "token_counting": "Подсчет токенов",
        "token_counting_info": "✅ Весь подсчет токенов **на 100% бесплатный** и выполняется локально. API ключи или кредиты не требуются!",
        "token_counting_note": "Подсчет токенов использует бесплатные локальные вычисления. OpenAI и DeepL точные; Anthropic и Google - приблизительные.",
        
        # Language selector
        "language": "Язык",
        "select_language": "Выберите язык",
        
        # Processing messages
        "extracting_text": "Извлечение текста из PDF...",
        "pdf_processed": "✅ PDF успешно обработан!",
        "pages": "Страниц",
        "characters": "Символов",
        "words": "Слов",
        "calculating_tokens": "Расчет количества токенов для всех провайдеров (бесплатно, локальный расчет)...",
        "calculating_costs": "Расчет стоимости...",
        
        # Token counts section
        "token_counts_title": "📊 Количество токенов по провайдерам",
        "token_counts_caption": "Все расчеты бесплатны и выполняются локально. Модели OpenAI точные; остальные - приблизительные.",
        "exact": "✅ Точный",
        "approximate": "⚠️ Приблизительный",
        "error": "Ошибка",
        
        # Cost comparison section
        "cost_comparison_title": "💰 Сравнение стоимости",
        "cost_comparison_caption": "Ориентировочная стоимость перевода всего документа (Арабский → Русский)",
        "provider": "Провайдер",
        "model": "Модель",
        "input_tokens": "Входные токены",
        "output_tokens_est": "Выходные токены (прибл.)",
        "input_cost": "Стоимость входа ($)",
        "output_cost": "Стоимость выхода ($)",
        "total_cost": "Общая стоимость ($)",
        "cheapest_option": "💡 **Самый дешевый вариант**: {provider} {model} за **${cost}**",
        "cost_range": "Диапазон стоимости: ${min} - ${max} (разница: ${diff})",
        
        # Translation section
        "translate_title": "🚀 Перевод с выбранным LLM",
        "translate_with": "Перевести с {model}",
        "translate": "Перевести",
        "action": "Действие",
        "total_cost_label": "Общая стоимость: ${cost}",
        "not_implemented": " (еще не реализовано)",
        "using_api_key": "🔑 Используется API ключ: {api_key}",
        "confirm_translation": "⚠️ Подтвердить перевод",
        "estimated_cost": "**Ориентировочная стоимость**: ${cost}",
        "provider_label": "**Провайдер**: {provider} {model}",
        "translation_note": "Это переведет весь документ по абзацам. Это может занять несколько минут.",
        "start_translation": "✅ Начать перевод",
        "starting_translation": "🚀 Начало перевода...",
        "translation_progress": "📊 Прогресс перевода",
        "translating_paragraph": "🔄 Перевод абзаца {current} из {total}...",
        "generating_pdf": "📄 Создание PDF...",
        "translation_completed": "✅ Перевод успешно завершен!",
        
        # Translation results
        "translation_results_title": "📄 Результаты перевода",
        "pdf_saved_to": "📁 PDF сохранен в: `{path}`",
        "pdf_saved_temp": "📁 PDF сохранен во временную директорию: `{path}`",
        "pdf_saved_tip": "💡 Совет: Установите `PDF_OUTPUT_DIR` в файле `.env`, чтобы сохранять PDF в пользовательскую директорию",
        "preview_label": "Предпросмотр (первые 500 символов):",
        "download_pdf": "📥 Скачать переведенный PDF",
        
        # Error messages
        "no_text_extracted": "Не удалось извлечь текст из PDF. Файл может быть основан на изображениях или поврежден.",
        "api_key_missing": "API ключ не найден. Пожалуйста, установите необходимый API ключ в файле `.env`.",
        "api_key_info": "💡 Пожалуйста, установите `GOOGLE_API_KEY` в файле `.env` или как переменную окружения",
        "authentication_error": "❌ Ошибка аутентификации: {error}",
        "troubleshooting_title": "**Решение проблем с API ключом:**",
        "troubleshooting_1": "1. **Проверьте ваш API ключ** в файле `.env`",
        "troubleshooting_2": "2. **Проверьте права доступа API ключа**: Убедитесь, что ключ имеет доступ к Generative Language API",
        "troubleshooting_3": "3. **Пересоздайте при необходимости**: Получите новый API ключ в [Google AI Studio](https://makersuite.google.com/app/apikey)",
        "troubleshooting_4": "4. **Включите API**: Убедитесь, что Generative Language API включен в вашем проекте Google Cloud",
        "troubleshooting_5": "5. **Проверьте пробелы**: Убедитесь, что в файле `.env` нет лишних пробелов вокруг ключа",
        "missing_package": "❌ Отсутствует пакет: {error}",
        "install_packages": "💡 Пожалуйста, установите необходимые пакеты: `pip install -e .`",
        "rate_limit_exceeded": "❌ Превышен лимит запросов",
        "rate_limit_warning": "⚠️ Вы достигли лимита API запросов. Пожалуйста, подождите несколько минут и попробуйте снова.",
        "network_error": "❌ Ошибка сети",
        "network_warning": "⚠️ Проблема с сетевым подключением. Пожалуйста, проверьте ваше интернет-соединение и попробуйте снова.",
        "translation_failed": "❌ Ошибка перевода: {error}",
        "error_details": "🔍 Детали ошибки",
        "translation_error": "❌ Ошибка перевода: {error}",
        "pdf_not_found": "❌ PDF файл не найден. Пожалуйста, попробуйте загрузить снова.",
        "error_processing_pdf": "❌ Ошибка обработки PDF: {error}",
        "pdf_corrupted": "💡 PDF файл может быть поврежден или в неподдерживаемом формате. Попробуйте другой PDF файл.",
        "permission_denied": "💡 Доступ запрещен. Убедитесь, что файл не открыт в другом приложении.",
        "technical_details": "🔍 Технические детали",
        "not_implemented_info": "🚧 Перевод с **{provider} {model}** еще не реализован. Эта функция будет добавлена в ближайшее время! Ориентировочная стоимость: ${cost}",
        
        # No file uploaded
        "no_file_uploaded": "👆 Пожалуйста, загрузите PDF файл, чтобы начать.",
        "how_to_use": "Как использовать это приложение",
        "how_to_1": "1. **Загрузите PDF**: Нажмите на загрузчик файлов выше и выберите вашу арабскую PDF-книгу",
        "how_to_2": "2. **Просмотрите статистику**: Посмотрите количество страниц, символов и слов",
        "how_to_3": "3. **Проверьте количество токенов**: Просмотрите количество токенов для каждого LLM-провайдера",
        "how_to_4": "4. **Сравните стоимость**: Просмотрите таблицу сравнения стоимости, чтобы увидеть цены для каждого провайдера",
        "how_to_5": "5. **Выберите провайдера**: Выберите предпочитаемый LLM и нажмите кнопку перевода (скоро)",
        "how_to_note": "**Примечание**: Подсчет токенов бесплатный и выполняется локально. Вы платите только при фактическом переводе.",
        
        # Additional UI elements
        "sidebar_language_title": "Язык",
        "sidebar_about_title": "О приложении",
        "sidebar_token_counting_title": "Подсчет токенов",
        "sidebar_tip": "💡 **Совет:** Весь подсчет токенов бесплатный и выполняется локально. API расходы только при переводе!",
        "select_provider_title": "Выберите провайдера для перевода",
        "select_provider_caption": "Нажмите кнопку ниже, чтобы начать перевод с выбранным провайдером",
        "translation_in_progress_info": "⏳ Перевод в процессе... Таблица свернута для фокуса на прогрессе.",
        "estimated_cost_info": "💰 **Ориентировочная стоимость:** ${cost} | **Провайдер:** {provider} {model}",
        "start_translation_button": "🚀 Начать перевод",
        "live_translation_title": "Предпросмотр перевода в реальном времени",
        "live_translation_caption": "Смотрите, как перевод появляется в реальном времени по мере генерации",
        "translation_stats": "Статистика перевода",
        "welcome_title": "Добро пожаловать в Калькулятор стоимости перевода PDF",
        "welcome_description": "**Получите мгновенные оценки стоимости** для перевода ваших PDF документов с помощью различных AI-провайдеров перед началом работы.",
        "welcome_features_title": "✨ Основные возможности:",
        "welcome_quick_start_title": "💡 Быстрый старт:",
        "welcome_quick_start_1": "1. Загрузите PDF файл",
        "welcome_quick_start_2": "2. Просмотрите оценки стоимости",
        "welcome_quick_start_3": "3. Выберите провайдера",
        "welcome_quick_start_4": "4. Скачайте переведенный PDF",
        "features_title": "Возможности",
        "features_free_estimates_title": "Бесплатные оценки",
        "features_free_estimates_1": "Без расходов на API",
        "features_free_estimates_2": "Локальные расчеты",
        "features_free_estimates_3": "Мгновенные результаты",
        "features_compare_title": "Сравнение провайдеров",
        "features_compare_1": "Множество LLM опций",
        "features_compare_2": "Сравнение цен рядом",
        "features_compare_3": "Лучшее предложение выделено",
        "features_live_title": "Перевод в реальном времени",
        "features_live_1": "Потоковая передача",
        "features_live_2": "Отслеживание прогресса",
        "features_live_3": "Предпросмотр в реальном времени",
        "features_pdf_title": "PDF вывод",
        "features_pdf_1": "Профессиональное форматирование",
        "features_pdf_2": "Сохраненная структура",
        "features_pdf_3": "Готово к скачиванию",
        
        # Metrics and stats
        "metric_start_time": "Время начала",
        "metric_end_time": "Время окончания",
        "metric_duration": "Длительность",
        "metric_total_paragraphs": "Всего абзацев",
        "metric_characters": "Символов",
        "metric_words": "Слов",
        "metric_paragraphs": "Абзацев",
        "metric_speed": "Скорость",
        "metric_avg_speed": "Средняя скорость",
        "metric_total_characters": "Всего символов",
        "metric_total_words": "Всего слов",
        "metric_cheapest": "Самый дешевый",
        "metric_most_expensive": "Самый дорогой",
        "metric_cost_range": "Диапазон стоимости",
        "metric_eta": "Осталось",
        "chars_per_sec": "симв/с",
        "coming_soon": "Скоро",
        "best_value": "Лучшее предложение",
        "step_by_step_guide": "Пошаговое руководство:",
        "translation_preview_title": "Предпросмотр перевода",
        "waiting_for_translation": "Ожидание начала перевода...",
        "preview_help_text": "Первые 1000 символов переведенного текста",
        
        # Progress and resume
        "progress_found": "Найден существующий прогресс перевода",
        "progress_status": "{completed} из {total} абзацев переведено ({percent}%)",
        "last_updated": "Последнее обновление: {timestamp}",
        "resume_translation": "Продолжить перевод",
        "start_fresh": "Начать заново",
        "resuming_from": "Продолжение с абзаца {index}",
        "progress_saved": "Прогресс сохранен после абзаца {index}",
        "download_partial_pdf": "Скачать частичный PDF ({completed}/{total} абзацев)",
        "partial_pdf_title": "Частичный перевод - {completed} из {total} абзацев",
        "partial_pdf_note": "Это частичный перевод. {completed} из {total} абзацев переведено.",
        "generating_partial_pdf": "Создание частичного PDF...",
        "stop_translation": "⏹️ Остановить перевод",
        "resume_translation_button": "▶️ Продолжить перевод",
        "translation_stopped": "⏸️ Перевод остановлен",
        "translation_stopped_message": "Перевод был остановлен. Прогресс сохранен. Вы можете продолжить с того места, где остановились.",
    }
}


def get_translation(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Get a translated string for the given key and language.
    
    Args:
        key: Translation key
        language: Language code (default: 'en')
        **kwargs: Format arguments for the translation string
        
    Returns:
        Translated string with format arguments applied
    """
    if language not in TRANSLATIONS:
        language = DEFAULT_LANGUAGE
    
    translation = TRANSLATIONS[language].get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    
    # Format the string if kwargs are provided
    if kwargs:
        try:
            return translation.format(**kwargs)
        except KeyError:
            # If formatting fails, return the translation as-is
            return translation
    
    return translation


def get_all_translations(language: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """
    Get all translations for a given language.
    
    Args:
        language: Language code (default: 'en')
        
    Returns:
        Dictionary of all translations for the language
    """
    if language not in TRANSLATIONS:
        language = DEFAULT_LANGUAGE
    
    return TRANSLATIONS[language].copy()
