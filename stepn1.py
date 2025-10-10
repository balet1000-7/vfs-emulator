import os
import sys
import shlex
import re
import argparse
import zipfile
import base64

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

if os.name == "nt":
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Глобальные настройки эмулятора
VFS_NAME = "MYVFS"
CONFIG = {
    "vfs_root": None,
    "startup_script": None,
    "no_interactive": False,
}

# ===== VFS (Виртуальная Файловая Система) =====
VFS = {
    "files": {},
    "folders": set(),
    "cwd": "/",
    "loaded": False
}


def make_prompt() -> str:
    return f"[{VFS_NAME} {VFS['cwd']}]$ "


def load_vfs_from_zip(zip_path: str) -> bool:
    """
    Загружает VFS из ZIP-архива в память
    Соответствует требованиям 1, 2, 3 этапа 3
    """
    try:
        if not os.path.exists(zip_path):
            print(f"Ошибка: VFS файл не найден: {zip_path}")
            return False

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            VFS["files"] = {}
            VFS["folders"] = set()

            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    folder_path = file_info.filename
                    if folder_path and not folder_path.endswith('/'):
                        folder_path += '/'
                    VFS["folders"].add(folder_path)
                else:
                    with zip_ref.open(file_info.filename) as file:
                        content = file.read()
                        try:
                            VFS["files"][file_info.filename] = content.decode('utf-8')
                        except UnicodeDecodeError:
                            VFS["files"][file_info.filename] = f"[base64]{base64.b64encode(content).decode('ascii')}"

            VFS["cwd"] = "/"
            VFS["loaded"] = True
            print(f"VFS загружена из: {zip_path}")
            print(f"Файлов: {len(VFS['files'])}, Папок: {len(VFS['folders'])}")
            return True

    except zipfile.BadZipFile:
        print(f"Ошибка: неправильный формат ZIP-архива: {zip_path}")
        return False
    except Exception as e:
        print(f"Ошибка загрузки VFS: {e}")
        return False


def vfs_init():
    """
    Сбрасывает VFS к состоянию по умолчанию
    Соответствует требованию 4 этапа 3
    """
    VFS["files"] = {}
    VFS["folders"] = set()
    VFS["cwd"] = "/"
    VFS["loaded"] = False
    print("VFS сброшена к состоянию по умолчанию")


def list_vfs_directory(path: str = None) -> list:
    """Возвращает список файлов и папок в указанной директории VFS"""
    if path is None:
        path = VFS["cwd"]

    # Нормализуем путь для поиска
    if path == "/":
        search_path = ""
    else:
        search_path = path.lstrip('/')

    items = set()

    # Проверяем все элементы VFS
    for item_path in list(VFS["files"].keys()) + list(VFS["folders"]):
        # Если элемент находится в искомой директории
        if item_path.startswith(search_path):
            # Получаем относительный путь
            relative_path = item_path[len(search_path):].lstrip('/')
            if not relative_path:
                continue

            # Разделяем на части
            parts = relative_path.split('/')
            if len(parts) > 1:
                # Это вложенный элемент - добавляем первую папку
                items.add(parts[0] + '/')
            else:
                # Это файл или папка в текущей директории
                items.add(parts[0])

    return sorted(list(items))


def change_vfs_directory(new_path: str) -> bool:
    """Меняет текущую директорию в VFS"""
    if new_path.startswith('/'):
        # Абсолютный путь
        target_path = new_path
    else:
        # Относительный путь
        if VFS["cwd"] == "/":
            target_path = "/" + new_path
        else:
            target_path = VFS["cwd"].rstrip('/') + "/" + new_path

    # Нормализуем путь
    if target_path != "/" and not target_path.endswith('/'):
        target_path += '/'

    # Проверяем существование пути
    search_path = target_path.lstrip('/')
    path_exists = False

    # Проверяем есть ли файлы или папки в этой директории
    for item_path in list(VFS["files"].keys()) + list(VFS["folders"]):
        if item_path.startswith(search_path) or item_path == search_path.rstrip('/'):
            path_exists = True
            break

    # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: не позволяем переходить в файлы
    # Убираем слеш в конце и проверяем не файл ли это
    clean_path = search_path.rstrip('/')
    if clean_path in VFS["files"]:
        print(f"Ошибка: '{new_path}' является файлом, а не директорией")
        return False

    if path_exists:
        VFS["cwd"] = target_path
        return True
    else:
        print(f"Ошибка: директория не существует: {target_path}")
        return False


def cat_file(filename: str) -> bool:
    """Выводит содержимое файла из VFS"""
    # Получаем абсолютный путь к файлу
    if filename.startswith('/'):
        abs_path = filename.lstrip('/')
    else:
        if VFS["cwd"] == "/":
            abs_path = filename
        else:
            abs_path = VFS["cwd"].lstrip('/') + filename

    # Убираем завершающий слеш если он есть (когда пользователь использовал cd на файле)
    abs_path = abs_path.rstrip('/')

    # Ищем файл в VFS
    if abs_path in VFS["files"]:
        content = VFS["files"][abs_path]
        if content.startswith("[base64]"):
            print(f"Файл {filename} содержит бинарные данные")
        else:
            print(content)
        return True
    else:
        print(f"cat: {filename}: No such file or directory")
        return False


def rev_text(text: str) -> str:
    """Переворачивает строку"""
    return text[::-1]


def rev_file(filename: str) -> bool:
    """Выводит содержимое файла в обратном порядке"""
    # Получаем абсолютный путь к файлу
    if filename.startswith('/'):
        abs_path = filename.lstrip('/')
    else:
        if VFS["cwd"] == "/":
            abs_path = filename
        else:
            abs_path = VFS["cwd"].lstrip('/') + filename

    # Убираем завершающий слеш если он есть
    abs_path = abs_path.rstrip('/')

    # Ищем файл в VFS
    if abs_path in VFS["files"]:
        content = VFS["files"][abs_path]
        if content.startswith("[base64]"):
            print(f"rev: {filename}: Binary file")
            return False
        else:
            # Переворачиваем содержимое файла
            reversed_content = rev_text(content)
            print(reversed_content)
            return True
    else:
        print(f"rev: {filename}: No such file or directory")
        return False


# допустимое имя переменной окружения
_VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _expand_exact_env_ref(token: str) -> str:
    if token.startswith("${") and token.endswith("}") and len(token) > 3:
        name = token[2:-1]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    if token.startswith("$") and len(token) > 1 and "{" not in token:
        name = token[1:]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    if token.startswith("%") and token.endswith("%") and len(token) > 2:
        name = token[1:-1]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    low = token.lower()
    if low.startswith("$env:") and len(token) > 5:
        name = token[5:]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    return token


def parse_command(line: str) -> list[str]:
    try:
        parts = shlex.split(line, posix=True)
    except ValueError as e:
        print(f"Ошибка парсера: {e}")
        return []

    if os.name == "nt":
        home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
        if home:
            os.environ.setdefault("HOME", home)

    return [_expand_exact_env_ref(p) for p in parts]


def execute_line(line: str) -> str | None:
    if line.startswith("$") or line.startswith("%") or line.lower().startswith("$env:"):
        line = "echo " + line

    parts = parse_command(line)
    if not parts:
        return None

    cmd, *args = parts

    if cmd == "exit":
        print("Выход.")
        return "exit"

    elif cmd == "echo":
        print(" ".join(args))

    elif cmd == "ls":
        if not VFS["loaded"]:
            print("VFS не загружена. Используйте -v путь_к_zip для загрузки.")
        else:
            files = list_vfs_directory()
            if files:
                for file in files:
                    print(file)
            else:
                print("Директория пуста")

    elif cmd == "cd":
        if not VFS["loaded"]:
            print("VFS не загружена. Используйте -v путь_к_zip для загрузки.")
        else:
            if args:
                change_vfs_directory(args[0])
            else:
                VFS["cwd"] = "/"

    elif cmd == "vfs-init":
        vfs_init()

    elif cmd == "pwd":
        print(VFS["cwd"])

    elif cmd == "cat":
        if not VFS["loaded"]:
            print("VFS не загружена. Используйте -v путь_к_zip для загрузки.")
        elif not args:
            print("cat: missing operand")
        else:
            for filename in args:
                cat_file(filename)


    elif cmd == "rev":
        if not VFS["loaded"]:
            print("VFS не загружена. Используйте -v путь_к_zip для загрузки.")

        elif not args:
            print("rev: missing operand")
        else:
            for arg in args:
                # Проверяем является ли аргумент файлом в VFS
                abs_path = arg.lstrip('/')
                if VFS["cwd"] != "/":
                    abs_path = VFS["cwd"].lstrip('/') + arg

                abs_path = abs_path.rstrip('/')

                if abs_path in VFS["files"]:
                    # Если это файл - обрабатываем как файл
                    rev_file(arg)

                else:
                    # Иначе обрабатываем как текст
                    print(rev_text(arg))

    else:
        print(f"Неизвестная команда: {cmd}")

    return None


def run_script(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                stripped = line.strip()

                if stripped.startswith("#") or stripped == "":
                    print(line)
                    continue

                print(make_prompt() + line)
                status = execute_line(line)
                if status == "exit":
                    return
    except FileNotFoundError:
        print(f"Ошибка: стартовый скрипт не найден: {path}")
    except UnicodeDecodeError:
        print(f"Ошибка: некорректная кодировка скрипта: {path}")


def repl():
    print("Эмулятор запущен. Введите 'exit' для выхода.")
    while True:
        try:
            line = input(make_prompt()).strip()
            if not line:
                continue
            status = execute_line(line)
            if status == "exit":
                break
        except KeyboardInterrupt:
            print("\n^C")
            break
        except EOFError:
            print()
            break


def _abspath_or_none(p: str | None) -> str | None:
    if not p:
        return None
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))


def parse_cli_args():
    parser = argparse.ArgumentParser(description="Эмулятор оболочки — Этап 4: Основные команды")
    parser.add_argument("-v", "--vfs", dest="vfs_root", help="Путь к ZIP-архиву с VFS", default=None)
    parser.add_argument("-s", "--script", dest="startup_script", help="Путь к стартовому скрипту", default=None)
    parser.add_argument("--no-interactive", action="store_true", help="Не входить в REPL")
    return parser.parse_args()


def print_debug_config():
    print("=== DEBUG: параметры запуска ===")
    print(f"OS: {os.name}, Python: {sys.version.split()[0]}")
    print(f"VFS root:       {CONFIG['vfs_root'] or '(не задан)'}")
    print(f"Startup script: {CONFIG['startup_script'] or '(не задан)'}")
    print(f"Interactive:    {not CONFIG['no_interactive']}")
    print("===============================")


def main():
    args = parse_cli_args()
    CONFIG["vfs_root"] = _abspath_or_none(args.vfs_root)
    CONFIG["startup_script"] = _abspath_or_none(args.startup_script)
    CONFIG["no_interactive"] = bool(args.no_interactive)

    print_debug_config()

    if CONFIG["vfs_root"]:
        if not load_vfs_from_zip(CONFIG["vfs_root"]):
            print("Не удалось загрузить VFS")

    if CONFIG["startup_script"]:
        run_script(CONFIG["startup_script"])

    if not CONFIG["no_interactive"]:
        repl()


if __name__ == "__main__":
    main()