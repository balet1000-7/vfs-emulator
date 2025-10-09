@echo off
chcp 65001 > nul
echo === ТЕСТИРОВАНИЕ MULTILEVEL.ZIP СО ВСЕМИ КОМАНДАМИ ===

echo Запуск с многоуровневым VFS и тестом всех команд:
python stepn1.py -v multilevel.zip -s all_commands3.txt

echo.
echo === ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===
pause