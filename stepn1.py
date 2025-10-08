import os
import sys
import shlex
import re

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

if os.name == "nt":
    try:
        import ctypes
        # Кодовые страницы консоли
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except Exception:
        pass
    # Страховка для Python
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


VFS_NAME = "MYVFS"   # имя VFS в приглашении
CWD = "/"            # текущий путь (пока заглушка)

def make_prompt() -> str:
    return f"[{VFS_NAME} {CWD}]$ "

# допустимое имя переменной окружения
_VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _expand_exact_env_ref(token: str) -> str:
    """
    Раскрывает ТОКЕН, если он полностью одной из форм:
      $NAME
      ${NAME}
      %NAME%        (cmd.exe стиль)
      $env:NAME     (PowerShell стиль, регистронезависимо для 'env')
    Иначе возвращает исходный token.
    """
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

    # $env:NAME  (PowerShell)
    low = token.lower()
    if low.startswith("$env:") and len(token) > 5:
        name = token[5:]
        if _VAR_NAME.match(name):
            return os.environ.get(name, token)
        return token

    return token

def parse_command(line: str) -> list[str]:
    """
    Разбивает строку как shell: учитывает кавычки.
    Затем по каждому токену выполняет раскрытие переменных окружения.
    """
    try:
        parts = shlex.split(line, posix=True)
    except ValueError as e:
        print(f"Ошибка парсера: {e}")
        return []
    # подстановка HOME для Windows, если вдруг отсутствует
    if os.name == "nt":
        home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
        if home:
            os.environ.setdefault("HOME", home)

    return [_expand_exact_env_ref(p) for p in parts]

def repl():
    print("Эмулятор запущен. Введите 'exit' для выхода.")
    while True:
        try:
            line = input(make_prompt()).strip()
            if not line:
                continue


            if line.startswith("$") or line.startswith("%") or line.lower().startswith("$env:"):
                line = "echo " + line

            parts = parse_command(line)
            if not parts:
                continue

            cmd, *args = parts

            if cmd == "exit":
                print("Выход.")
                break

            elif cmd == "echo":
                # простая реализация echo
                print(" ".join(args))

            elif cmd == "ls":
                # заглушка по ТЗ
                print(f"Команда: ls, аргументы: {args}")

            elif cmd == "cd":
                # заглушка по ТЗ (можно потом реально менять CWD)
                print(f"Команда: cd, аргументы: {args}")

            else:
                print(f"Неизвестная команда: {cmd}")

        except KeyboardInterrupt:
            print("\n^C")
            break
        except EOFError:
            print()
            break

if __name__ == "__main__":
    repl()