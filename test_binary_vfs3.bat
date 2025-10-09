@echo off
chcp 65001 > nul
echo ========================================
echo    ТЕСТ БИНАРНЫХ ФАЙЛОВ (BASE64)
echo ========================================
echo.
echo Запускаем эмулятор с binary_test.zip...
echo Введите команды вручную для тестирования
echo.
python stepn1.py -v binary_test.zip
echo.
pause