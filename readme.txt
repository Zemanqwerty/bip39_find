для подгрузки библиотек - pip install -r reqs.pip
для билда - pyinstaller --onefile main.py

скрипт попросит указать:
Минимальную длину искомой фразы
Максимальную длину искомой фразы
(обычно фращы имеют длину 12 или 24 слова, так что лучше указывать в этом промежутке +- пара слов)
Минимальное количетсов совпадений с BIP39 (при каком количестве слов из словаря в найденной фразе она будет считаться валидной.
К примеру, если во фразе некоторые слова изменялись, стоит это учитывать и указывать это значение меньше, чем кол-во слов в искомой фразе)
Путь к диреткории для вывода (по этому пути скрипт создаст новую папку, в которую будет писать результаты)
Название папки (Название папки, в которую скрипт будет писать результаты)

По итогам парсинга в указаной папке скрипт создаст несколько текстовых файлов с именами расширейний найденых файлов. К примеру,
если скрипт нашёл фразы в файлах .txt и .dll в указанной папке создадутся файлы txt.txt и dll.txt, в каждом их которых будут записаны
найденные фразы в файлах этого типа и пути к файлам, в которых эти фразы были найдены
Сделано для удобства просмотра результатов, чтобы в первую очередь можно было проверить txt файлы и потом уже перейти к dll и подобным.