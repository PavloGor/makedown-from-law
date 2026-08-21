@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

:: ── Якщо передано аргументи при запуску (Drag & Drop на файл convert.cmd у провіднику) ──
if not "%~1"=="" goto DRAG_DROP

:: ── Пошук Python ──
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

if not exist "%~dp0Output" mkdir "%~dp0Output"
if not exist "%~dp0input" mkdir "%~dp0input"

:: ── Інтерактивне меню ──
:MENU
cls
echo ================================================================
echo           КОНВЕРТЕР ЗАКОНІВ УКРАЇНИ В MARKDOWN (UTF-8)
echo ================================================================
echo.
echo  [1] Пакетна конвертація з папки "input" (всі файли -^> Output)
echo  [2] Конвертувати окремий файл (ввести шлях або перетягнути сюди)
echo  [3] Конвертувати тільки .htm / .html з папки "input"
echo  [4] Вказати власні папки (Вхідна тека -^> Вихідна тека)
echo  [5] Відкрити папку з результатами (Output)
echo  [0] Вихід
echo.
echo  (💡 Підказка: ви також можете просто перетягнути файл сюди!)
echo ================================================================
set "CHOICE="
set /p "CHOICE=Оберіть варіант [0-5] або перетягніть файл: "

if not defined CHOICE goto MENU

:: Очищаємо лапки з введеного значення
set "CLEAN_CHOICE=!CHOICE:"=!"

:: Видаляємо можливий кінцевий пробіл від Drag and Drop
:TRIM_CHOICE_LOOP
if "!CLEAN_CHOICE:~-1!"==" " (
    set "CLEAN_CHOICE=!CLEAN_CHOICE:~0,-1!"
    goto TRIM_CHOICE_LOOP
)

:: Якщо користувач перетягнув файл безпосередньо у головне меню
if exist "!CLEAN_CHOICE!" (
    set "FILE_PATH=!CLEAN_CHOICE!"
    goto RUN_CONVERT_FILE
)

:: Обробка пунктів меню
if "!CLEAN_CHOICE!"=="1" goto BULK_INPUT
if "!CLEAN_CHOICE!"=="2" goto SINGLE_FILE
if "!CLEAN_CHOICE!"=="3" goto HTM_INPUT_ONLY
if "!CLEAN_CHOICE!"=="4" goto CUSTOM_DIRS
if "!CLEAN_CHOICE!"=="5" goto OPEN_OUTPUT
if "!CLEAN_CHOICE!"=="0" goto EXIT_APP

echo.
echo [!] Невірний вибір: "!CHOICE!". Спробуйте ще раз.
timeout /t 2 >nul
goto MENU

:BULK_INPUT
echo.
echo ----------------------------------------------------------------
echo  Запуск пакетної конвертації з папки "input"...
echo ----------------------------------------------------------------
"!PYTHON_CMD!" "%~dp0law_to_md.py" "%~dp0input" --output "%~dp0Output"
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
if not defined FILE_PATH (
    echo [Скасовано] Шлях не вказано.
    echo.
    pause
    goto MENU
)

set "FILE_PATH=!FILE_PATH:"=!"

:TRIM_FILE_LOOP
if "!FILE_PATH:~-1!"==" " (
    set "FILE_PATH=!FILE_PATH:~0,-1!"
    goto TRIM_FILE_LOOP
)

:RUN_CONVERT_FILE
if not exist "!FILE_PATH!" (
    echo.
    echo [ПОМИЛКА] Файл не знайдено: "!FILE_PATH!"
    echo.
    pause
    goto MENU
)

echo.
echo ----------------------------------------------------------------
echo  Конвертую: "!FILE_PATH!"
echo ----------------------------------------------------------------
"!PYTHON_CMD!" "%~dp0law_to_md.py" "!FILE_PATH!" --output "%~dp0Output"
echo.
pause
goto MENU

:HTM_INPUT_ONLY
echo.
echo ----------------------------------------------------------------
echo  Конвертація тільки .htm / .html з папки "input"...
echo ----------------------------------------------------------------
"!PYTHON_CMD!" "%~dp0law_to_md.py" "%~dp0input/*.htm" "%~dp0input/*.html" --output "%~dp0Output"
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
if not defined IN_DIR (
    echo [Скасовано] Вхідний шлях не вказано.
    echo.
    pause
    goto MENU
)
set "IN_DIR=!IN_DIR:"=!"

:TRIM_IN_LOOP
if "!IN_DIR:~-1!"==" " (
    set "IN_DIR=!IN_DIR:~0,-1!"
    goto TRIM_IN_LOOP
)

set /p "OUT_DIR=Введіть шлях до папки результатів [за замовчуванням Output]: "
set "OUT_DIR=!OUT_DIR:"=!"
if "!OUT_DIR!"=="" set "OUT_DIR=%~dp0Output"

:TRIM_OUT_LOOP
if "!OUT_DIR:~-1!"==" " (
    set "OUT_DIR=!OUT_DIR:~0,-1!"
    goto TRIM_OUT_LOOP
)

if not exist "!IN_DIR!" (
    echo.
    echo [ПОМИЛКА] Вхідний шлях не існує: "!IN_DIR!"
    echo.
    pause
    goto MENU
)

echo.
"!PYTHON_CMD!" "%~dp0law_to_md.py" "!IN_DIR!" --output "!OUT_DIR!"
echo.
pause
goto MENU

:OPEN_OUTPUT
if not exist "%~dp0Output" mkdir "%~dp0Output"
start "" "%~dp0Output"
goto MENU

:EXIT_APP
echo.
echo Дякуємо за використання!
timeout /t 1 >nul
exit /b 0


:: ── Блок прямої конвертації (Drag & Drop на файл convert.cmd у Windows Explorer) ──
:DRAG_DROP
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

if not exist "%~dp0Output" mkdir "%~dp0Output"

echo ================================================================
echo  Пряма конвертація: Drag and Drop
echo ================================================================
"!PYTHON_CMD!" "%~dp0law_to_md.py" %* --output "%~dp0Output"
echo.
echo [Готово] Результати збережено в папку: Output
echo.
pause
exit /b 0

