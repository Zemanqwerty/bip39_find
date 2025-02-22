import os
import re
from mnemonic import Mnemonic
from collections import Counter

# Создаем объект Mnemonic для английского и русского языков
mnemo_en = Mnemonic("english")
mnemo_ru = Mnemonic("russian")

# Получаем список слов BIP-39 и преобразуем его в множество для быстрого поиска
BIP39_SET_EN = set(mnemo_en.wordlist)
BIP39_SET_RU = set(mnemo_ru.wordlist)

# Минимальное количество слов из списка BIP-39 для валидной фразы
MIN_BIP39_WORDS = 3

def is_concatenated_bip39_word(word, word_set):
    """
    Проверяет, является ли слово сконкатенированной последовательностью слов из word_set.
    Возвращает True, если слово состоит из 8–24 слов из word_set.
    """
    n = len(word)
    dp = [False] * (n + 1)
    dp[0] = True  # Базовый случай: пустая строка валидна
    word_count = [0] * (n + 1)  # Массив для подсчета количества слов в разбиении

    for i in range(1, n + 1):
        for j in range(max(0, i - 8), i):  # Ограничение длины слова до 8 символов (максимальная длина BIP-39 слова)
            if dp[j] and word[j:i] in word_set:
                dp[i] = True
                word_count[i] = word_count[j] + 1
                break

    # Проверяем, что слово состоит из 8–24 слов
    return dp[n] and 8 <= word_count[n] <= 24

def extract_bip39_phrases(text, word_set):
    """
    Извлекает все фразы BIP-39 из текста с длиной от 8 до 24 слов.
    Также извлекает одиночные слова длиной от 30 символов, если они являются сконкатенированными словами из word_set,
    состоящими из 8–24 слов.
    Разрешает до 2 дубликатов каждого слова.
    Обрабатывает многострочные фразы, где каждая строка может содержать несколько слов.
    Фраза считается валидной только если хотя бы одно слово (или часть сконкатенированного слова) начинается с буквы "g".
    """
    phrases = []
    lines = text.splitlines()  # Разбиваем текст на строки
    current_phrase = []

    for line in lines:
        words = re.findall(r'\b\w+\b', line.lower())  # Извлекаем все слова из строки
        valid_words_in_line = [word for word in words if word in word_set]  # Фильтруем только валидные слова
        current_phrase.extend(valid_words_in_line)

        # Если накоплено достаточно слов для проверки фразы
        if len(current_phrase) >= MIN_BIP39_WORDS:
            # Подсчитываем частоту каждого слова
            word_counts = Counter(current_phrase)
            # Проверяем, что каждое слово повторяется не более 2 раз
            if all(count <= 2 for count in word_counts.values()):
                # Проверяем длину фразы (общее количество слов)
                total_words = len(current_phrase)
                if 8 <= total_words <= 24:
                    # Проверяем минимальное количество слов из BIP-39
                    bip39_word_count = sum(1 for word in current_phrase if word in word_set)
                    if bip39_word_count >= MIN_BIP39_WORDS:
                        # Проверяем, что хотя бы одно слово начинается с буквы "g"
                        if any(word.startswith("g") for word in current_phrase):
                            phrases.append(" ".join(current_phrase))

        # Если текущая строка не содержит валидных слов, сбрасываем фразу
        if not valid_words_in_line:
            current_phrase = []

    # Проверка длинных слов (сконкатенированных)
    long_words = re.findall(r'\b\w{30,}\b', text.lower())  # Находим слова длиной 30+ символов
    for word in long_words:
        if is_concatenated_bip39_word(word, word_set):
            # Разбиваем сконкатенированное слово на части
            parts = []
            n = len(word)
            i = 0
            while i < n:
                for j in range(min(i + 8, n), i, -1):  # Ищем подстроки длиной до 8 символов
                    if word[i:j] in word_set:
                        parts.append(word[i:j])
                        i = j
                        break
            # Проверяем, что хотя бы одна часть начинается с "g"
            if any(part.startswith("g") for part in parts):
                phrases.append(word)

    return phrases

def search_files(directory, excluded_dirs=None):
    """
    Поиск файлов с фразами BIP-39 длиной от 8 до 24 слов, а также одиночными словами длиной от 30 символов,
    которые являются сконкатенированными словами из BIP-39 списка.
    Результаты (путь к файлу и фразы) записываются в указанный файл.
    excluded_dirs: Список директорий, которые нужно исключить из обработки.
    """
    if excluded_dirs is None:
        excluded_dirs = []

    for root, dirs, files in os.walk(directory):
        # Исключаем указанные директории
        dirs[:] = [d for d in dirs if os.path.join(root, d) not in excluded_dirs]
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                # Проверяем, является ли файл текстовым
                if not os.path.isfile(file_path):
                    continue
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()  # Читаем весь файл
                    # Ищем фразы для английских и русских слов BIP-39
                    phrases_en = extract_bip39_phrases(content, BIP39_SET_EN)
                    phrases_ru = extract_bip39_phrases(content, BIP39_SET_RU)
                    # Объединяем найденные фразы
                    all_phrases = phrases_en + phrases_ru
                    if all_phrases:
                        # Записываем путь к файлу и найденные фразы
                        for phrase in all_phrases:
                            print(f"  Файл: {file_path}")
                            print(f"  Фраза: {phrase}")
                            # out.write(f"Файл: {file_path}\n")
                            # out.write(f"  Фраза: {phrase}\n\n")
            except Exception as e:
                pass


if __name__ == "main":
    # Указываем путь к диску C:
    directory_to_search = input('Введите путь к директории, в которой нужно искать: ')
    # Файл для записи результатов
    # output_file = input('Введите путь к файлу, в который будут записаны результаты: ')
    # Исключаем папку Windows и её поддиректории
    excluded_dirs = []
    if not os.path.isdir(directory_to_search):
        print("Указанный путь не является директорией.")
    else:
        print("Начинаю поиск файлов...")
        search_files(directory_to_search, excluded_dirs=excluded_dirs)
        input("\nНажмите Enter, чтобы закрыть программу...")