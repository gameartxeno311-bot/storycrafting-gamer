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

echo.
echo Starting The Storycrafting Gamer...
echo Type /bye to exit.
echo.
ollama run "%MODEL%"

endlocal
