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
echo 1. Chat with AI + Obsidian memory
echo 2. Connect / authorize X account
echo 3. Check X connection
echo 4. Post text to X
echo 5. Check Obsidian connection
echo 6. Save a memory to Obsidian
echo 7. Read AI memory
echo 8. Search Obsidian memory
echo 9. Exit
echo.
choice /c 123456789 /n /m "Choose an option: "

if errorlevel 9 goto :done
if errorlevel 8 goto :obsidian_search
if errorlevel 7 goto :obsidian_read
if errorlevel 6 goto :obsidian_remember
if errorlevel 5 goto :obsidian_status
if errorlevel 4 goto :post
if errorlevel 3 goto :status
if errorlevel 2 goto :connect
if errorlevel 1 goto :chat

:chat
cls
echo Starting The Storycrafting Gamer with Obsidian memory...
echo Type /bye to exit. Use /remember TEXT to save a memory.
echo.
python memory\obsidian_chat.py
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

:obsidian_status
cls
echo ==========================================
echo          OBSIDIAN CONNECTION
echo ==========================================
echo.
python memory\obsidian_memory.py status
echo.
pause
goto :menu

:obsidian_remember
cls
echo ==========================================
echo             SAVE AI MEMORY
echo ==========================================
echo.
set "MEMORY="
set /p "MEMORY=Enter something the AI should remember: "
if not defined MEMORY (
    echo.
    echo No memory entered.
    pause
    goto :menu
)
python memory\obsidian_memory.py remember "%MEMORY%"
echo.
pause
goto :menu

:obsidian_read
cls
echo ==========================================
echo               AI MEMORY
echo ==========================================
echo.
python memory\obsidian_memory.py read
echo.
pause
goto :menu

:obsidian_search
cls
echo ==========================================
echo           SEARCH OBSIDIAN MEMORY
echo ==========================================
echo.
set "QUERY="
set /p "QUERY=Enter a search query: "
if not defined QUERY (
    echo.
    echo No query entered.
    pause
    goto :menu
)
python memory\obsidian_memory.py search "%QUERY%"
echo.
pause
goto :menu

:done
endlocal
