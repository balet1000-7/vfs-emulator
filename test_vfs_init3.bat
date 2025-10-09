@echo off
chcp 65001 > nul
echo ========================================
echo    ТЕСТ КОМАНДЫ VFS-INIT
echo ========================================
echo.
python stepn1.py -v multilevel.zip -s test_vfs_init3.txt
echo.
pause