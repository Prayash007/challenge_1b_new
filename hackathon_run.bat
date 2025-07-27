@echo off
REM Adobe Hackathon Challenge 1B New - BERT Compliant Build & Run Script

echo 🏆 Adobe Hackathon Challenge 1B New - BERT Document Ranking
echo ============================================================

REM Build command as specified in hackathon guidelines
echo 🔨 Building Docker image...
docker build --platform linux/amd64 -t challenge1b-bert:roberta-ranker .

if %errorlevel% neq 0 (
    echo ❌ Docker build failed!
    pause
    exit /b 1
)

echo ✅ Docker image built successfully!

REM Create input and output directories if they don't exist
if not exist "input" mkdir input
if not exist "output" mkdir output

echo 📂 Directory structure ready:
echo    input/  - Place your PDF files and challenge1b_input.json here
echo    output/ - Results will be written here
echo.
echo 🚀 To run the solution, use:
echo docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" --network none challenge1b-bert:roberta-ranker
echo.
echo 📋 Expected behavior:
echo    • Processes all PDFs from input/ directory with BERT
echo    • Uses RoBERTa-Base model (~500MB, ^<1GB compliant)
echo    • Advanced semantic ranking with persona adaptation
echo    • Generates filename.json for each filename.pdf
echo    • Creates consolidated output.json with BERT rankings
echo.
echo 🤖 BERT Features:
echo    • Multi-layer embeddings from RoBERTa-Base
echo    • Dynamic persona handling
echo    • INT8 quantization for speed
echo    • Semantic query expansion
echo.

REM Check if input directory has files
dir /b input\*.* >nul 2>&1
if %errorlevel% equ 0 (
    echo 📄 Files found in input directory. Running BERT solution...
    docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" --network none challenge1b-bert:roberta-ranker
) else (
    echo 💡 Add PDF files and challenge1b_input.json to the 'input' directory and run the Docker command above.
)

echo 🎉 Challenge 1B BERT setup complete!
pause
