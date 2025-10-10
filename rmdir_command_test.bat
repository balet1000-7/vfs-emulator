@echo off
chcp 65001 > nul
echo === ТЕСТИРОВАНИЕ КОМАНДЫ RMDIR - ЭТАП 5 ===
echo.

echo Запуск тестового скрипта для for_5stage.zip:
python stepn1.py -v for_5stage.zip -s rmdir_command_test.txt --no-interactive

echo.
echo === ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===
pause