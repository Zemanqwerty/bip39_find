import os
import re
from mnemonic import Mnemonic
from colorama import Fore, Style, init

# Инициализация colorama
init(autoreset=True)

# Константы
MIN_PHRASE_LENGTH = 12  # Минимальная длина фразы
MAX_PHRASE_LENGTH = 24  # Максимальная длина фразы
MIN_BIP39_MATCHES = 3   # Минимальное количество совпадений с BIP39 словами

# Инициализация списка BIP39 слов для английского и русского языков
BIP39_EN_WORDS = set(Mnemonic("english").wordlist)
BIP39_RU_WORDS = set(Mnemonic("russian").wordlist)

def is_valid_phrase(words, original_phrase):
    """
    Проверяет, является ли список слов валидной BIP39 фразой.
    """
    # Условие 1: Длина фразы должна быть от MIN_PHRASE_LENGTH до MAX_PHRASE_LENGTH
    if not (MIN_PHRASE_LENGTH <= len(words) <= MAX_PHRASE_LENGTH):
        return False

    # Условие 2: Ни одно слово не должно повторяться
    if len(words) != len(set(words)):
        return False

    # Условие 3: Минимум MIN_BIP39_MATCHES совпадений с BIP39 словами
    bip39_count = sum(1 for word in words if word in BIP39_EN_WORDS or word in BIP39_RU_WORDS)
    if bip39_count < MIN_BIP39_MATCHES:
        return False

    # Условие 4: Если фраза сконкатенирована, проверяем её длину
    if " " not in original_phrase:  # Фраза сконкатенирована
        if not (MIN_PHRASE_LENGTH * 8 <= len(original_phrase) <= MAX_PHRASE_LENGTH * 8):
            return False

    return True

def extract_phrases_from_text(text):
    """
    Извлекает уникальные потенциальные BIP39 фразы из текста.
    """
    # Разбиваем текст на слова, сохраняя исходный текст для вывода
    words = text.split()
    cleaned_words = [re.sub(r'[^a-zA-Zа-яА-Я]', '', word.lower()) for word in words]

    # Группируем слова в потенциальные фразы длиной от MIN_PHRASE_LENGTH до MAX_PHRASE_LENGTH слов
    phrases = set()  # Используем множество для исключения дубликатов
    for i in range(len(cleaned_words)):
        for length in range(MIN_PHRASE_LENGTH, MAX_PHRASE_LENGTH + 1):
            if i + length <= len(cleaned_words):
                phrase = cleaned_words[i:i + length]
                original_phrase = " ".join(words[i:i + length])
                if is_valid_phrase(phrase, original_phrase):
                    phrases.add(original_phrase)  # Добавляем фразу в множество
    return phrases

def process_file(file_path, output_dir):
    """
    Обрабатывает один файл: читает его содержимое и ищет BIP39 фразы.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        phrases = extract_phrases_from_text(text)
        if phrases:
            # Вывод имени файла красным цветом
            print(f"{Fore.RED}Файл: {file_path}{Style.RESET_ALL}")
            for phrase in sorted(phrases):  # Сортируем фразы для удобства чтения
                print(f"  Найдена фраза: {phrase}")

            # Сохраняем найденные фразы в соответствующие файлы
            file_extension = os.path.splitext(file_path)[1][1:]  # Получаем расширение файла без точки
            output_file_path = os.path.join(output_dir, f"{file_extension}.txt")
            with open(output_file_path, 'a', encoding='utf-8') as output_file:
                for phrase in sorted(phrases):
                    output_file.write(f"{file_path} --- {phrase}\n")
    except Exception as e:
        print(f"Ошибка при обработке файла {file_path}: {e}")

def scan_directory(directory, output_dir):
    """
    Сканирует указанную директорию и обрабатывает все файлы.
    """
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            process_file(file_path, output_dir)

if __name__ == "__main__":
    # Укажите путь к директории, которую нужно сканировать
    directory_to_scan = input("Введите путь к директории: ").strip()

    # Запрос параметров поиска
    MIN_PHRASE_LENGTH = int(input('Введите минимальную длину искомой фразы (чаще всего используется 12): '))
    MAX_PHRASE_LENGTH = int(input('Введите максимальную длину искомой фразы (Иногда фразы могут достигать 24): '))
    MIN_BIP39_MATCHES = int(input('Введите минимальное количество совпадений с bip39 (чем меньше - тем больше разброс по фразам): '))

    # Запрос пути и имени для выходной директории
    output_base_dir = input("Введите путь к директории, где создать новую папку: ").strip()
    output_folder_name = input("Введите имя новой папки: ").strip()
    output_dir = os.path.join(output_base_dir, output_folder_name)

    # Создание выходной директории
    os.makedirs(output_dir, exist_ok=True)

    if os.path.isdir(directory_to_scan):
        scan_directory(directory_to_scan, output_dir)
    else:
        print("Указанный путь не является директорией.")