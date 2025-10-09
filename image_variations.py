#!/usr/bin/env python3
"""
Image Variations Generator
Создает 5 вариаций изображения с различными эффектами
"""

import os
import sys
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np
from io import BytesIO
import base64

def create_image_variations(image_path, output_dir="variations"):
    """
    Создает 5 вариаций изображения
    
    Args:
        image_path (str): Путь к исходному изображению
        output_dir (str): Папка для сохранения вариаций
    """
    
    # Создаем папку для вариаций
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # Загружаем исходное изображение
        original = Image.open(image_path)
        print(f"✅ Загружено изображение: {image_path}")
        print(f"📏 Размер: {original.size}")
        print(f"🎨 Режим: {original.mode}")
        
        # Конвертируем в RGB если необходимо
        if original.mode != 'RGB':
            original = original.convert('RGB')
        
        variations = []
        
        # Вариация 1: Морская волна (сепия + синий оттенок)
        print("\n🌊 Создание вариации 1: Морская волна...")
        sepia = ImageOps.colorize(
            ImageOps.grayscale(original),
            black="black",
            white="#87CEEB"  # Sky blue
        )
        enhancer = ImageEnhance.Contrast(sepia)
        variation1 = enhancer.enhance(1.3)
        variation1_path = os.path.join(output_dir, "variation_1_sea_wave.jpg")
        variation1.save(variation1_path, quality=95)
        variations.append(("Морская волна", variation1_path))
        
        # Вариация 2: Яркий контраст
        print("🔥 Создание вариации 2: Яркий контраст...")
        contrast = ImageEnhance.Contrast(original)
        bright_contrast = contrast.enhance(1.8)
        brightness = ImageEnhance.Brightness(bright_contrast)
        variation2 = brightness.enhance(1.2)
        variation2_path = os.path.join(output_dir, "variation_2_bright_contrast.jpg")
        variation2.save(variation2_path, quality=95)
        variations.append(("Яркий контраст", variation2_path))
        
        # Вариация 3: Черно-белый с высоким контрастом
        print("⚫ Создание вариации 3: Черно-белый...")
        bw = ImageOps.grayscale(original)
        contrast_bw = ImageEnhance.Contrast(bw)
        variation3 = contrast_bw.enhance(1.5)
        variation3_path = os.path.join(output_dir, "variation_3_black_white.jpg")
        variation3.save(variation3_path, quality=95)
        variations.append(("Черно-белый", variation3_path))
        
        # Вариация 4: Цветовой сдвиг (винтажный эффект)
        print("🌈 Создание вариации 4: Цветовой сдвиг...")
        # Создаем винтажный эффект
        vintage = original.copy()
        # Применяем цветовую коррекцию
        r, g, b = vintage.split()
        # Меняем каналы местами и усиливаем
        vintage = Image.merge('RGB', (b, r, g))
        color_enhancer = ImageEnhance.Color(vintage)
        variation4 = color_enhancer.enhance(1.4)
        variation4_path = os.path.join(output_dir, "variation_4_color_shift.jpg")
        variation4.save(variation4_path, quality=95)
        variations.append(("Цветовой сдвиг", variation4_path))
        
        # Вариация 5: Инверсия с эффектом
        print("🔄 Создание вариации 5: Инверсия...")
        inverted = ImageOps.invert(original)
        # Добавляем легкий размытый эффект
        blurred = inverted.filter(ImageFilter.GaussianBlur(radius=0.5))
        # Увеличиваем насыщенность
        color_enhancer = ImageEnhance.Color(blurred)
        variation5 = color_enhancer.enhance(1.3)
        variation5_path = os.path.join(output_dir, "variation_5_inversion.jpg")
        variation5.save(variation5_path, quality=95)
        variations.append(("Инверсия", variation5_path))
        
        print(f"\n✅ Создано 5 вариаций изображения в папке '{output_dir}':")
        for i, (name, path) in enumerate(variations, 1):
            print(f"   {i}. {name}: {path}")
        
        return variations
        
    except Exception as e:
        print(f"❌ Ошибка при обработке изображения: {e}")
        return []

def create_advanced_variations(image_path, output_dir="advanced_variations"):
    """
    Создает продвинутые вариации с использованием numpy для более сложных эффектов
    """
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        original = Image.open(image_path)
        if original.mode != 'RGB':
            original = original.convert('RGB')
        
        # Конвертируем в numpy array для продвинутой обработки
        img_array = np.array(original)
        
        variations = []
        
        # Продвинутая вариация 1: Ретро эффект
        print("\n📻 Создание продвинутой вариации 1: Ретро эффект...")
        retro = img_array.copy().astype(np.float32)
        # Применяем ретро цветовую схему
        retro[:, :, 0] = np.clip(retro[:, :, 0] * 1.2 + 20, 0, 255)  # Красный
        retro[:, :, 1] = np.clip(retro[:, :, 1] * 0.9 - 10, 0, 255)  # Зеленый
        retro[:, :, 2] = np.clip(retro[:, :, 2] * 0.7 - 30, 0, 255)  # Синий
        retro_img = Image.fromarray(retro.astype(np.uint8))
        retro_path = os.path.join(output_dir, "advanced_1_retro.jpg")
        retro_img.save(retro_path, quality=95)
        variations.append(("Ретро эффект", retro_path))
        
        # Продвинутая вариация 2: Кинематографический эффект
        print("🎬 Создание продвинутой вариации 2: Кинематографический...")
        cinema = img_array.copy().astype(np.float32)
        # Создаем кинематографический look
        cinema[:, :, 0] = np.clip(cinema[:, :, 0] * 1.1 - 15, 0, 255)
        cinema[:, :, 1] = np.clip(cinema[:, :, 1] * 1.05, 0, 255)
        cinema[:, :, 2] = np.clip(cinema[:, :, 2] * 1.3 + 10, 0, 255)
        cinema_img = Image.fromarray(cinema.astype(np.uint8))
        cinema_path = os.path.join(output_dir, "advanced_2_cinema.jpg")
        cinema_img.save(cinema_path, quality=95)
        variations.append(("Кинематографический", cinema_path))
        
        # Продвинутая вариация 3: Неоновый эффект
        print("💡 Создание продвинутой вариации 3: Неоновый эффект...")
        neon = img_array.copy().astype(np.float32)
        # Увеличиваем контраст и насыщенность
        neon = (neon - 128) * 1.5 + 128
        neon[:, :, 0] = np.clip(neon[:, :, 0] * 0.8 + 40, 0, 255)
        neon[:, :, 1] = np.clip(neon[:, :, 1] * 1.4, 0, 255)
        neon[:, :, 2] = np.clip(neon[:, :, 2] * 1.6, 0, 255)
        neon_img = Image.fromarray(neon.astype(np.uint8))
        neon_path = os.path.join(output_dir, "advanced_3_neon.jpg")
        neon_img.save(neon_path, quality=95)
        variations.append(("Неоновый эффект", neon_path))
        
        # Продвинутая вариация 4: Драматический черно-белый
        print("🎭 Создание продвинутой вариации 4: Драматический ЧБ...")
        dramatic_bw = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
        # Увеличиваем контраст драматически
        dramatic_bw = (dramatic_bw - 128) * 2.0 + 128
        dramatic_bw = np.clip(dramatic_bw, 0, 255)
        dramatic_bw_img = Image.fromarray(dramatic_bw.astype(np.uint8)).convert('RGB')
        dramatic_path = os.path.join(output_dir, "advanced_4_dramatic_bw.jpg")
        dramatic_bw_img.save(dramatic_path, quality=95)
        variations.append(("Драматический ЧБ", dramatic_path))
        
        # Продвинутая вариация 5: Художественный эффект
        print("🎨 Создание продвинутой вариации 5: Художественный...")
        artistic = img_array.copy().astype(np.float32)
        # Создаем художественный эффект с мягкими тонами
        artistic = np.power(artistic / 255.0, 0.8) * 255.0
        artistic[:, :, 0] = np.clip(artistic[:, :, 0] * 1.1 + 15, 0, 255)
        artistic[:, :, 1] = np.clip(artistic[:, :, 1] * 0.95 + 10, 0, 255)
        artistic[:, :, 2] = np.clip(artistic[:, :, 2] * 0.9 + 20, 0, 255)
        artistic_img = Image.fromarray(artistic.astype(np.uint8))
        artistic_path = os.path.join(output_dir, "advanced_5_artistic.jpg")
        artistic_img.save(artistic_path, quality=95)
        variations.append(("Художественный", artistic_path))
        
        print(f"\n✅ Создано 5 продвинутых вариаций в папке '{output_dir}':")
        for i, (name, path) in enumerate(variations, 1):
            print(f"   {i}. {name}: {path}")
        
        return variations
        
    except Exception as e:
        print(f"❌ Ошибка при создании продвинутых вариаций: {e}")
        return []

def main():
    """Основная функция"""
    print("🎨 Генератор вариаций изображений")
    print("=" * 50)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) < 2:
        print("Использование: python image_variations.py <путь_к_изображению>")
        print("Пример: python image_variations.py image.jpg")
        return
    
    image_path = sys.argv[1]
    
    # Проверяем существование файла
    if not os.path.exists(image_path):
        print(f"❌ Файл не найден: {image_path}")
        return
    
    # Создаем базовые вариации
    print("Создание базовых вариаций...")
    basic_variations = create_image_variations(image_path)
    
    # Создаем продвинутые вариации
    print("\nСоздание продвинутых вариаций...")
    advanced_variations = create_advanced_variations(image_path)
    
    total_variations = len(basic_variations) + len(advanced_variations)
    print(f"\n🎉 Готово! Создано {total_variations} вариаций изображения")
    print("\n📁 Файлы сохранены в папках:")
    print("   - variations/ (базовые эффекты)")
    print("   - advanced_variations/ (продвинутые эффекты)")

if __name__ == "__main__":
    main()