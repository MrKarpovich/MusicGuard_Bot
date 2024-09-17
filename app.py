import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import asyncio
import time

API_TOKEN = '7516352227:AAHv1RFI-aNlRZJJdS1nS9fopUCRZ40dfIk'
DISCOGS_API_KEY = 'EuUMoQJolWDmwKjWFQYmDQIYDciYeWuwpjLGUBkA'
YOUTUBE_API_KEY = 'AIzaSyBvGSDRqsqbCX2V_DdzzeKbgjjropyEF_0'
CC_API_URL = 'https://api.openverse.org/v1/audio/'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Функция для поиска через Discogs API
def search_discogs(track_name):
    try:
        url = f"https://api.discogs.com/database/search?q={track_name}&token={DISCOGS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['results'][:3]  # Возвращаем первые три результата
        else:
            logging.error(f"🚫 Ошибка Discogs API: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"❌ Ошибка при запросе Discogs API: {e}")
        return None

# Функция для поиска через YouTube Data API
def search_youtube(track_name):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={track_name}&key={YOUTUBE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['items'][:3]  # Возвращаем первые три видео
        else:
            logging.error(f"🚫 Ошибка YouTube API: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"❌ Ошибка при запросе YouTube API: {e}")
        return None

# Функция для поиска через Openverse (Creative Commons) API
def search_creative_commons(track_name):
    try:
        params = {'q': track_name, 'fields': 'title,url,creator'}
        response = requests.get(CC_API_URL, params=params)

        # Логируем полный ответ от API для отладки
        logging.info(f"Ответ Openverse API: {response.status_code}, Тело ответа: {response.text}")

        if response.status_code == 200:
            data = response.json()
            return data['results'][:3]  # Возвращаем первые три результата
        else:
            logging.error(f"🚫 Ошибка Openverse API: {response.status_code}, Response: {response.text}")
            return None
    except ValueError as ve:
        logging.error(f"❌ Некорректный JSON от Openverse API: {ve}, Response: {response.text}")
        return None
    except Exception as e:
        logging.error(f"❌ Ошибка при запросе Openverse API: {e}")
        return None

# Функция для форматирования результатов Discogs
def format_discogs_results(results):
    formatted = ""
    if results:
        for result in results:
            formatted += f"🎵 {result.get('title')} by {result.get('artist')}\n"
            formatted += f"🔗 Link: {result.get('uri')}\n\n"
        formatted += "ℹ️ Эти песни могут быть защищены авторским правом. Проверьте лицензию перед использованием.\n\n"
    else:
        formatted = "❌ Ничего не найдено на Discogs.\n"
    return formatted

# Функция для форматирования результатов YouTube
def format_youtube_results(results):
    formatted = ""
    if results:
        for result in results:
            if result['id']['kind'] == 'youtube#video':
                formatted += f"🎥 {result['snippet']['title']}\n"
                formatted += f"📺 Channel: {result['snippet']['channelTitle']}\n"
                formatted += f"🔗 Link: https://www.youtube.com/watch?v={result['id']['videoId']}\n\n"
        formatted += "⚠️ На YouTube могут быть видеоматериалы с авторскими правами. Убедитесь в их использовании согласно политике платформы.\n\n"
    else:
        formatted = "❌ Ничего не найдено на YouTube.\n"
    return formatted

# Функция для форматирования результатов Openverse (Creative Commons)
def format_cc_results(results):
    formatted = ""
    if results:
        for result in results:
            formatted += f"📜 {result['title']} by {result['creator']}\n"
            formatted += f"🔗 Link: {result['url']}\n\n"
        formatted += "✅ Найдено в Openverse с открытой лицензией. Использование разрешено с указанием автора!\n\n"
    else:
        formatted = "❌ Ничего не найдено в Openverse (Creative Commons).\n"
    return formatted

# Функция для анализа результатов и формирования более подробного заключения
def analyze_results(discogs_results, youtube_results, cc_results):
    analysis = ""

    if discogs_results:
        analysis += "🚫 Песня найдена на Discogs, что может свидетельствовать о наличии авторских прав. Убедитесь, что у вас есть разрешение на использование.\n\n"
    else:
        analysis += "✅ Песня не найдена на Discogs. Вероятно, она не зарегистрирована как защищённая.\n\n"

    if cc_results:
        analysis += "✅ СУПЕР! Песня найдена в Openverse (Creative Commons) с открытой лицензией. Убедитесь, что вы соблюдаете условия лицензии (например, указание автора).\n\n"
    else:
        analysis += "❌ Песня не найдена в Openverse (Creative Commons), возможно, она не имеет открытой лицензии.\n\n"

    if youtube_results:
        analysis += "⚠️ Песня найдена на YouTube. Это может быть контент с авторскими правами, обязательно проверьте права на использование в вашем случае.\n\n"
    else:
        analysis += "❌ Песня не найдена на YouTube.\n\n"

    return analysis

# Основной обработчик сообщений
@dp.message_handler()
async def search_track(message: types.Message):
    track_name = message.text
    await message.reply(f"🔍 Ищу информацию о песне \"{track_name}\"")

    # Поиск через Discogs
    discogs_results = search_discogs(track_name)
    await message.reply(format_discogs_results(discogs_results))

    # Поиск через YouTube
    youtube_results = search_youtube(track_name)
    await message.reply(format_youtube_results(youtube_results))

    # Поиск через Openverse (Creative Commons)
    cc_results = search_creative_commons(track_name)
    await message.reply(format_cc_results(cc_results))

    # Финальный вердикт с подробным объяснением
    conclusion = analyze_results(discogs_results, youtube_results, cc_results)
    await message.reply(f"📝 Заключение:\n\n {conclusion}")

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        time.sleep(5)
