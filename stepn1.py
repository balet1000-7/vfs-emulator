import os
import sys
import shlex
import re
import argparse


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
VFS_NAME = "MYVFS"   # имя VFS в приглашении
CWD = "/"            # текущий путь (пока заглушка)
CONFIG = {
    "vfs_root": None,         # путь к физическому расположению VFS
    "startup_script": None,   # путь к стартовому скрипту
    "no_interactive": False,  # не входить в REPL после скрипта
}

def make_prompt() -> str:
    return f"[{VFS_NAME} {CWD}]$ "

# допустимое имя переменной окружения
_VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _expand_exact_env_ref(token: str) -> str:
    # ${NAME}
    if token.startswith("${") and token.endswith("}") and len(token) > 3:
        name = token[2:-1]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    # $NAME
    if token.startswith("$") and len(token) > 1 and "{" not in token:
        name = token[1:]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    # %NAME%
    if token.startswith("%") and token.endswith("%") and len(token) > 2:
        name = token[1:-1]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    # $env:NAME (PowerShell)
    low = token.lower()
    if low.startswith("$env:") and len(token) > 5:
        name = token[5:]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    return token

def parse_command(line: str) -> list[str]:
    """
    1) Разбивает строку как shell (учитывает кавычки).
    2) По каждому токену выполняет раскрытие переменных окружения.
    """
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

# ВЫПОЛНЕНИЕ ОДНОЙ КОМАНДЫ (общая для REPL и скрипта)
def execute_line(line: str) -> str | None:
    """Возвращает 'exit', если команда должна завершить сценарий/REPL."""
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
        # заглушка по ТЗ
        print(f"Команда: ls, аргументы: {args}")

    elif cmd == "cd":
        # заглушка по ТЗ
        print(f"Команда: cd, аргументы: {args}")

    else:
        print(f"Неизвестная команда: {cmd}")

    return None

# ВЫПОЛНЕНИЕ СТАРТОВОГО СКРИПТА
def run_script(path: str) -> None:
    """
    Читает UTF-8 файл. Комментарии (#...) и пустые строки не выполняются.
    Перед выполнением каждой команды печатаем приглашение + команду,
    чтобы имитировать диалог с пользователем
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                stripped = line.strip()

                # Показываем комментарии (для наглядности), но не выполняем
                if stripped.startswith("#") or stripped == "":
                    print(line)
                    continue

                # эхо "ввода"
                print(make_prompt() + line)
                status = execute_line(line)
                if status == "exit":
                    return
    except FileNotFoundError:
        print(f"Ошибка: стартовый скрипт не найден: {path}")
    except UnicodeDecodeError:
        print(f"Ошибка: некорректная кодировка скрипта (ожидается UTF-8): {path}")

# REPL
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

# CLI: параметры Этапа 2
def _abspath_or_none(p: str | None) -> str | None:
    if not p:
        return None
    return os.path.abspath(os.path.expanduser(os.path.expandvars(p)))

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Эмулятор оболочки — Этап 2: Конфигурация")
    parser.add_argument("-v", "--vfs", dest="vfs_root",
                        help="Путь к физическому расположению VFS", default=None)
    parser.add_argument("-s", "--script", dest="startup_script",
                        help="Путь к стартовому скрипту (UTF-8)", default=None)
    parser.add_argument("--no-interactive", action="store_true",
                        help="Не входить в REPL после выполнения скрипта")
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

    # п. «Организовать отладочный вывод всех заданных параметров»
    print_debug_config()

    # Если задан стартовый скрипт — сначала выполнить его
    if CONFIG["startup_script"]:
        run_script(CONFIG["startup_script"])

    # Затем (если не отключили) — интерактив
    if not CONFIG["no_interactive"]:
        repl()

if __name__ == "__main__":
    main()
