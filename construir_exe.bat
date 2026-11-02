@echo off
setlocal
set "RESULTADO=1"
cd /d "%~dp0"
echo ==========================================
echo  Gerando TinyDrawStudio.exe com PyInstaller
echo ==========================================
py --version >nul 2>&1
if errorlevel 1 (
  echo [ERRO] O comando "py" nao foi encontrado. Instale o Python em python.org.
  goto :fim
)
echo.
echo [1/2] Instalando ou atualizando o PyInstaller...
py -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo [ERRO] Falha ao instalar o PyInstaller. Veja a mensagem acima.
  goto :fim
)
echo.
echo [2/2] Empacotando o programa...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name TinyDrawStudio ^
  --add-data "runtime;runtime" --add-data "exemplos;exemplos" tinydraw_studio.py
if errorlevel 1 (
  echo [ERRO] O empacotamento falhou. Veja a mensagem acima.
  goto :fim
)
echo.
echo PRONTO!  Seu executavel esta em:  %cd%\dist\TinyDrawStudio.exe
echo.
echo Lembrete: o computador que abrir o .exe precisa ter o gcc instalado,
echo ou uma pasta chamada gcc ao lado do .exe (gcc\bin\gcc.exe).
set "RESULTADO=0"
:fim
echo.
pause
exit /b %RESULTADO%
