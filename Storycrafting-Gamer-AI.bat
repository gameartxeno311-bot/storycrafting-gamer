@echo off
setlocal EnableExtensions
title The Storycrafting Gamer - AI

echo ==========================================
echo       THE STORYCRAFTING GAMER - AI
echo ==========================================
echo.

where ollama >nul 2>&1
if errorlevel 1 (
    echo Ollama was not found.
    echo.
    echo Install Ollama from https://ollama.com/ and then run this file again.
    echo.
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3.10+ and run this file again.
    echo.
    pause
    exit /b 1
)

set "MODEL=storycrafting-gamer"
set "BASEMODEL=llama3.2"
set "MODFILE=%TEMP%\storycrafting-gamer.Modelfile"

(
echo FROM %BASEMODEL%
echo SYSTEM You are The Storycrafting Gamer, a fictional AI influencer focused on game development, storytelling, animation, and world-building.
echo SYSTEM Your tagline is: Create a game people love.
echo SYSTEM Your personality is friendly, direct, curious, creative, cooperative, hardworking, imaginative, and grounded.
echo SYSTEM Your interests include game development, narrative design, world-building, character creation, animation, indie games, game mechanics, and creative technology.
echo SYSTEM Speak conversationally. Share ideas openly, ask questions, celebrate progress, and acknowledge that creative work is iterative.
echo SYSTEM When discussing your identity, be transparent that you are a fictional AI-created persona, not a real human.
echo SYSTEM Help users develop game concepts, stories, characters, worlds, animation ideas, social posts, and creative projects.
echo SYSTEM Do not claim fictional projects are real-world accomplishments.
) > "%MODFILE%"

echo Preparing the AI model...
ollama create "%MODEL%" -f "%MODFILE%"
if errorlevel 1 (
    echo.
    echo Failed to create the Ollama model.
    echo Make sure Ollama is running and the "%BASEMODEL%" model is available.
    echo You can download it with: ollama pull %BASEMODEL%
    echo.
    pause
    exit /b 1
)

del "%MODFILE%" >nul 2>&1

:menu
cls
echo ==========================================
echo       THE STORYCRAFTING GAMER - AI
echo ==========================================
echo.
echo 1. Chat with the AI
echo 2. Connect / authorize X account
echo 3. Check X connection
echo 4. Post text to X
echo 5. Exit
echo.
choice /c 12345 /n /m "Choose an option: "

if errorlevel 5 goto :done
if errorlevel 4 goto :post
if errorlevel 3 goto :status
if errorlevel 2 goto :connect
if errorlevel 1 goto :chat

:chat
cls
echo Starting The Storycrafting Gamer...
echo Type /bye to exit.
echo.
ollama run "%MODEL%"
goto :menu

:connect
cls
echo ==========================================
echo           CONNECT YOUR X ACCOUNT
echo ==========================================
echo.
echo Before connecting, make sure config\.env contains
echo your X OAuth 2.0 Client ID and the exact redirect URI
echo configured in your X Developer App.
echo.
python social\x_oauth.py connect
echo.
pause
goto :menu

:status
cls
python social\x_oauth.py status
echo.
pause
goto :menu

:post
cls
echo ==========================================
echo              POST TO X
echo ==========================================
echo.
set "XPOST="
set /p "XPOST=Enter the post text: "
if not defined XPOST (
    echo.
    echo No text entered.
    pause
    goto :menu
)
echo.
python social\x_oauth.py post "%XPOST%"
echo.
pause
goto :menu

:done
endlocal
