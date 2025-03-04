import os
import re
import logging
from mnemonic import Mnemonic
from colorama import Fore, Style, init
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Инициализация colorama
init(autoreset=True)

# Константы
MIN_PHRASE_LENGTH = 12  # Минимальная длина фразы
MAX_PHRASE_LENGTH = 24  # Максимальная длина фразы
MIN_BIP39_MATCHES = 3   # Минимальное количество совпадений с BIP39 словами

# Типичные замены символов
COMMON_SUBSTITUTIONS = {
    'a': ['@', '4'],
    'o': ['0'],
    'l': ['1', 'I'],
    'e': ['3'],
    's': ['$', '5'],
    'i': ['1', '!'],
}

# Функция расстояния Левенштейна
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

@lru_cache(maxsize=10000)
def is_similar_to_bip39(word, max_changes, bip39_words):
    """Проверяет сходство слова с BIP39 с учетом максимального количества изменений"""
    for bip39_word in bip39_words:
        if len(word) == len(bip39_word) and levenshtein_distance(word, bip39_word) <= max_changes:
            return True
    return False

def normalize_word(word, substitutions):
    """Нормализует слово, заменяя типичные символы"""
    word = word.lower()
    if word in BIP39_WORDS:
        return word
    for orig_char, subs in substitutions.items():
        for sub in subs:
            if sub in word:
                candidate = word.replace(sub, orig_char)
                if candidate in BIP39_WORDS:
                    return candidate
    return word

def clean_prefix_suffix(text):
    """Удаляет возможные префиксы и суффиксы"""
    patterns = [
        r'^(myseed|btc|wallet|phrase|seed)\s*(.+)',  # Префиксы
        r'(.+)\s*(123|pass|key)$',                   # Суффиксы
    ]
    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text

def is_valid_phrase(words, original_phrase, max_changes, substitutions):
    """Проверяет валидность фразы"""
    normalized_words = [normalize_word(word, substitutions) for word in words]
    if not (MIN_PHRASE_LENGTH <= len(normalized_words) <= MAX_PHRASE_LENGTH):
        return False
    if len(normalized_words) != len(set(normalized_words)):
        return False
    
    bip39_count = 0
    for word in normalized_words:
        if word in BIP39_WORDS:
            bip39_count += 1
        elif is_similar_to_bip39(word, max_changes, tuple(BIP39_WORDS)):
            bip39_count += 1
    
    if bip39_count < MIN_BIP39_MATCHES:
        return False
    
    if " " not in original_phrase and not "-" in original_phrase:
        if not (MIN_PHRASE_LENGTH * 8 <= len(original_phrase) <= MAX_PHRASE_LENGTH * 8):
            return False
    
    return True

def extract_phrases_from_text(text, max_changes, substitutions):
    """Извлекает потенциальные BIP39 фразы из текста"""
    phrases = set()
    text = clean_prefix_suffix(text)

    # Обычный текст с пробелами
    words = text.split()
    cleaned_words = [re.sub(r'[^a-zA-Zа-яА-Я]', '', word.lower()) for word in words]
    for i in range(len(cleaned_words)):
        for length in range(MIN_PHRASE_LENGTH, MAX_PHRASE_LENGTH + 1):
            if i + length <= len(cleaned_words):
                phrase = cleaned_words[i:i + length]
                original_phrase = " ".join(words[i:i + length])
                if is_valid_phrase(phrase, original_phrase, max_changes, substitutions):
                    phrases.add(original_phrase)

    # Текст с дефисами
    if '-' in text:
        words = text.replace('-', ' ').split()
        cleaned_words = [re.sub(r'[^a-zA-Zа-яА-Я]', '', word.lower()) for word in words]
        for i in range(len(cleaned_words)):
            for length in range(MIN_PHRASE_LENGTH, MAX_PHRASE_LENGTH + 1):
                if i + length <= len(cleaned_words):
                    phrase = cleaned_words[i:i + length]
                    original_phrase = " ".join(words[i:i + length])
                    if is_valid_phrase(phrase, original_phrase, max_changes, substitutions):
                        phrases.add(original_phrase)

    # Сконкатенированный текст
    if len(text) >= MIN_PHRASE_LENGTH * 8:
        for i in range(0, len(text) - MIN_PHRASE_LENGTH * 8 + 1, 1):
            chunk = text[i:i + MAX_PHRASE_LENGTH * 8]
            words = [chunk[j:j+8] for j in range(0, len(chunk), 8) if len(chunk[j:j+8]) >= 3]
            if len(words) >= MIN_PHRASE_LENGTH:
                original_phrase = " ".join(words)
                if is_valid_phrase(words, original_phrase, max_changes, substitutions):
                    phrases.add(original_phrase)

    return phrases

def process_file(file_path, output_dir, max_changes, substitutions):
    """Обрабатывает один файл"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        phrases = extract_phrases_from_text(text, max_changes, substitutions)
        if phrases:
            logging.info(f"Файл: {file_path}")
            print(f"{Fore.RED}Файл: {file_path}{Style.RESET_ALL}")
            for phrase in sorted(phrases):
                logging.info(f"Найдена фраза: {phrase}")
                print(f"  Найдена фраза: {phrase}")
            
            file_extension = os.path.splitext(file_path)[1][1:] or "no_ext"
            output_file_path = os.path.join(output_dir, f"{file_extension}.txt")
            with open(output_file_path, 'a', encoding='utf-8') as output_file:
                for phrase in sorted(phrases):
                    output_file.write(f"{file_path} --- {phrase}\n")
    except Exception as e:
        logging.error(f"Ошибка в файле {file_path}: {e}")
        print(f"Ошибка при обработке файла {file_path}: {e}")

def scan_directory(directory, output_dir, max_changes, substitutions):
    """Сканирует директорию с использованием параллельной обработки"""
    with ThreadPoolExecutor() as executor:
        for root, _, files in os.walk(directory):
            file_paths = [os.path.join(root, file_name) for file_name in files]
            executor.map(lambda fp: process_file(fp, output_dir, max_changes, substitutions), file_paths)

if __name__ == "__main__":
    # Запрос пути к директории
    directory_to_scan = input("Введите путь к директории: ").strip()

    # Выбор языка
    print("Доступные языки: english, russian, french, spanish, italian, japanese, korean, chinese_simplified")
    language = input("Введите язык фразы (по умолчанию english): ").strip() or "english"
    BIP39_WORDS = set(Mnemonic(language).wordlist)

    # Запрос параметров
    MIN_PHRASE_LENGTH = int(input('Минимальная длина фразы (обычно 12): '))
    MAX_PHRASE_LENGTH = int(input('Максимальная длина фразы (до 24): '))
    MIN_BIP39_MATCHES = int(input('Минимальное количество совпадений с BIP39 (меньше — больше вариантов): '))
    MAX_CHANGES = int(input('Максимально допустимых изменений в слове (0 — точное совпадение): '))

    # Запрос выходной директории
    output_base_dir = input("Путь к директории для результатов: ").strip()
    output_folder_name = input("Имя новой папки: ").strip()
    output_dir = os.path.join(output_base_dir, output_folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # Настройка логирования в указанную директорию
    log_file_path = os.path.join(output_dir, 'phrase_search.log')
    logging.basicConfig(filename=log_file_path, level=logging.INFO, 
                        format='%(asctime)s - %(message)s')

    # Запуск сканирования
    if os.path.isdir(directory_to_scan):
        scan_directory(directory_to_scan, output_dir, MAX_CHANGES, COMMON_SUBSTITUTIONS)
        print("Сканирование завершено. Результаты сохранены в", output_dir)
        print("Лог поиска доступен в", log_file_path)
    else:
        print("Указанный путь не является директорией.")