@echo off
echo === ПОЛНОЕ ТЕСТИРОВАНИЕ ЭТАП 5 - MV ===
echo.

echo Запуск полного тестирования для multivel.zip:
python stepn1.py -v multilevel.zip -s mv_command_test.txt --no-interactive

echo.
echo === ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===
pause