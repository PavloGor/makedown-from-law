@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Налаштування середовища UTF-8
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

:: Пошук Python
set "PYTHON_CMD="
where py >nul 2>&1 && set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
    where python >nul 2>&1 && set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo ================================================================
    echo [ПОМИЛКА] Python не знайдено в системі! Встановіть Python 3.
    echo ================================================================
    pause
    exit /b 1
)

:: Створення робочих папок, якщо вони відсутні
if not exist "Output" mkdir "Output"
if not exist "Examples" mkdir "Examples"
if not exist "input" mkdir "input"

:: Якщо файл або папку перетягнули прямо на іконку convert.cmd (%1)
if not "%~1"=="" (
    echo ================================================================
    echo  Пряма конвертація: %~1
    echo ================================================================
    "%PYTHON_CMD%" law_to_md.py "%~1" --output Output
    echo.
    echo [Готово] Результати збережено в папку Output\
    echo.
    pause
    exit /b 0
)

:MENU
cls
echo ================================================================
echo           КОНВЕРТЕР ЗАКОНІВ УКРАЇНИ В MARKDOWN (UTF-8)
echo ================================================================
echo.
echo  [1] Пакетна конвертація з папки "input"     (всі файли -^> Output)
echo  [2] Пакетна конвертація з папки "Examples"  (всі файли -^> Output)
echo  [3] Конвертувати окремий файл (ввести шлях або перетягнути сюди)
echo  [4] Конвертувати тільки .htm / .html з папки "input"
echo  [5] Вказати власні папки (Вхідна тека -^> Вихідна тека)
echo  [6] Відкрити папку з результатами (Output)
echo  [0] Вихід
echo.
echo ================================================================
set "CHOICE="
set /p "CHOICE=Оберіть варіант [0-6] і натисніть Enter: "

if "%CHOICE%"=="1" goto BULK_INPUT
if "%CHOICE%"=="2" goto BULK_EXAMPLES
if "%CHOICE%"=="3" goto SINGLE_FILE
if "%CHOICE%"=="4" goto HTM_INPUT_ONLY
if "%CHOICE%"=="5" goto CUSTOM_DIRS
if "%CHOICE%"=="6" goto OPEN_OUTPUT
if "%CHOICE%"=="0" goto EXIT_APP

echo.
echo [!] Невірний вибір. Спробуйте ще раз.
timeout /t 2 >nul
goto MENU

:BULK_INPUT
echo.
echo ----------------------------------------------------------------
echo  Запуск пакетної конвертації з папки "input"...
echo ----------------------------------------------------------------
"%PYTHON_CMD%" law_to_md.py input/ --output Output
echo.
pause
goto MENU

:BULK_EXAMPLES
echo.
echo ----------------------------------------------------------------
echo  Запуск пакетної конвертації з папки "Examples"...
echo ----------------------------------------------------------------
"%PYTHON_CMD%" law_to_md.py Examples/ --output Output
echo.
pause
goto MENU

:SINGLE_FILE
echo.
echo ----------------------------------------------------------------
echo  Конвертація окремого файлу (.htm, .html, .docx, .pdf)
echo ----------------------------------------------------------------
set "FILE_PATH="
set /p "FILE_PATH=Перетягніть файл у це вікно або введіть шлях: "
if defined FILE_PATH (
    set "FILE_PATH=!FILE_PATH:"=!"
    if exist "!FILE_PATH!" (
        echo.
        "%PYTHON_CMD%" law_to_md.py "!FILE_PATH!" --output Output
    ) else (
        echo.
        echo [ПОМИЛКА] Файл не знайдено: !FILE_PATH!
    )
) else (
    echo [Скасовано] Шлях не вказано.
)
echo.
pause
goto MENU

:HTM_INPUT_ONLY
echo.
echo ----------------------------------------------------------------
echo  Конвертація тільки .htm / .html з папки "input"...
echo ----------------------------------------------------------------
"%PYTHON_CMD%" law_to_md.py "input/*.htm" "input/*.html" --output Output
echo.
pause
goto MENU

:CUSTOM_DIRS
echo.
echo ----------------------------------------------------------------
echo  Власні папки для конвертації
echo ----------------------------------------------------------------
set "IN_DIR="
set "OUT_DIR="
set /p "IN_DIR=Введіть шлях до вхідної папки/файлу: "
set "IN_DIR=!IN_DIR:"=!"
set /p "OUT_DIR=Введіть шлях до папки результатів [за замовчуванням Output]: "
set "OUT_DIR=!OUT_DIR:"=!"
if "!OUT_DIR!"=="" set "OUT_DIR=Output"

if exist "!IN_DIR!" (
    echo.
    "%PYTHON_CMD%" law_to_md.py "!IN_DIR!" --output "!OUT_DIR!"
) else (
    echo.
    echo [ПОМИЛКА] Вхідний шлях не існує: !IN_DIR!
)
echo.
pause
goto MENU

:OPEN_OUTPUT
if not exist "Output" mkdir "Output"
start "" "Output"
goto MENU

:EXIT_APP
echo.
echo Дякуємо за використання!
timeout /t 1 >nul
exit /b 0
