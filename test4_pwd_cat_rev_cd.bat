@echo off
chcp 65001 > nul
echo === ТЕСТИРОВАНИЕ CAT И REV ===
echo.

python stepn1.py -v minimal.zip -s test4_pwd_cd_cat_rev.txt

echo.
echo === ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===
pause