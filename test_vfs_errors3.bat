@echo off
chcp 65001 > nul
echo ========================================
echo    ТЕСТ ОБРАБОТКИ ОШИБОК VFS
echo ========================================
echo.

echo 1. Тест: несуществующий файл VFS
python stepn1.py -v nonexistent.zip --no-interactive
echo.

echo 2. Тест: не-ZIP файл
python stepn1.py -v emulator.py
echo.

echo ========================================
echo    ТЕСТ ОШИБОК ЗАВЕРШЕН
echo ========================================
pause