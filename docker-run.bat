@echo off
REM Docker run scripts for Challenge 1B BERT Implementation
REM Adobe Hackathon Challenge 1B - Windows Version 11 

setlocal EnableDelayedExpansion

REM Configuration
set IMAGE_NAME=adobe-hackathon/challenge1b-bert
set CONTAINER_NAME=challenge1b-bert

:print_header
echo 🤖 Adobe Hackathon Challenge 1B - BERT Docker
echo 🏆 Advanced BERT-based Document Ranking System
echo ================================================================
goto :eof

:build_image
echo 🔨 Building Docker image...
docker build -t %IMAGE_NAME% .
if %errorlevel% equ 0 (
    echo ✅ Docker image built successfully!
) else (
    echo ❌ Docker build failed!
    exit /b 1
)
goto :eof

:run_collection1
echo 🚀 Running BERT on Collection 1...
docker run --rm ^
    -v "%cd%/Collection 1:/app/collections/Collection 1:ro" ^
    -v "%cd%/output:/app/output:rw" ^
    --name %CONTAINER_NAME% ^
    %IMAGE_NAME% python run_collection.py --collection 1
goto :eof

:run_all_collections
echo 🚀 Running BERT on all collections...
docker run --rm ^
    -v "%cd%:/app/collections:ro" ^
    -v "%cd%/output:/app/output:rw" ^
    --name %CONTAINER_NAME% ^
    %IMAGE_NAME% python run_collection.py --all
goto :eof

:run_interactive
echo 🖥️ Starting interactive BERT container...
docker run -it --rm ^
    -v "%cd%:/app/collections:ro" ^
    -v "%cd%/output:/app/output:rw" ^
    --name %CONTAINER_NAME% ^
    %IMAGE_NAME% /bin/bash
goto :eof

:start_with_compose
echo 🐳 Starting with Docker Compose...
docker-compose up --build
goto :eof

:show_help
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   build              Build the Docker image
echo   run-collection1    Run BERT on Collection 1
echo   run-all           Run BERT on all collections
echo   interactive       Start interactive container
echo   compose           Start with Docker Compose
echo   help              Show this help message
echo.
echo Examples:
echo   %0 build ^&^& %0 run-collection1
echo   %0 compose
echo   %0 interactive
goto :eof

REM Create output directory if it doesn't exist
if not exist "output" mkdir output

REM Main command handling
if "%1"=="build" (
    call :print_header
    call :build_image
) else if "%1"=="run-collection1" (
    call :print_header
    call :run_collection1
) else if "%1"=="run-all" (
    call :print_header
    call :run_all_collections
) else if "%1"=="interactive" (
    call :print_header
    call :run_interactive
) else if "%1"=="compose" (
    call :print_header
    call :start_with_compose
) else (
    call :print_header
    call :show_help
)

echo 🎉 BERT Docker operation complete!
