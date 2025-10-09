@echo off
chcp 65001 > nul
echo ========================================
echo    ТЕСТ МНОГОУРОВНЕВОЙ VFS
echo ========================================
echo.

echo Запускаем эмулятор с multilevel.zip...
python stepn1.py -v multilevel.zip

echo.
echo ========================================
echo    ТЕСТ ЗАВЕРШЕН
echo ========================================
pause