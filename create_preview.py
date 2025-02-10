from PIL import Image, ImageDraw, ImageFont
import os

# Создаем изображение (1280x640 - стандартный размер для GitHub)
width = 1280
height = 640
image = Image.new('RGB', (width, height), '#0D1117')  # Тёмный фон в стиле GitHub

# Создаем градиент
gradient = Image.new('RGB', (width, height))
for y in range(height):
    r = int(25 + (y / height) * 30)  # Тёмно-синий
    g = int(40 + (y / height) * 40)
    b = int(70 + (y / height) * 70)
    for x in range(width):
        gradient.putpixel((x, y), (r, g, b))

image = Image.blend(image, gradient, 0.5)

# Создаем объект для рисования
draw = ImageDraw.Draw(image)

# Загружаем шрифты
try:
    title_font = ImageFont.truetype("Arial Bold.ttf", 72)
    subtitle_font = ImageFont.truetype("Arial.ttf", 36)
    author_font = ImageFont.truetype("Arial.ttf", 28)
except:
    # Если шрифты не найдены, используем дефолтный
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()
    author_font = ImageFont.load_default()

# Текст
title = "🔍 SEO Jobs Hunter"
subtitle = "Умный парсер вакансий с GPT анализом"
author = "by SergD (@sergei_dyshkant)"
features = "🤖 AI-powered | 🔄 Real-time | 📊 Smart filtering"

# Позиционирование текста
title_position = (width//2, height//2 - 100)
subtitle_position = (width//2, height//2)
author_position = (width//2, height//2 + 60)
features_position = (width//2, height//2 + 120)

# Добавляем текст
for text, position, font in [
    (title, title_position, title_font),
    (subtitle, subtitle_position, subtitle_font),
    (author, author_position, author_font),
    (features, features_position, subtitle_font)
]:
    # Получаем размеры текста
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Рисуем текст с центрированием
    x = position[0] - text_width//2
    y = position[1] - text_height//2
    
    # Добавляем тень
    draw.text((x+2, y+2), text, font=font, fill='#000000')
    draw.text((x, y), text, font=font, fill='#FFFFFF')

# Сохраняем изображение
image.save('social_preview.png', 'PNG')
print("✅ Изображение social_preview.png создано!")
