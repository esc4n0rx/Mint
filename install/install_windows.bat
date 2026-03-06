@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_DIR=%%~fI"
set "BIN_DIR=%USERPROFILE%\mint-bin"
set "LAUNCHER=%BIN_DIR%\mint.bat"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=python"
  ) else (
    echo Erro: Python nao encontrado. Instale Python 3.10+ e rode novamente.
    exit /b 1
  )
)

%PYTHON_CMD% -c "import sys; assert sys.version_info >= (3,10), 'Erro: e necessario Python 3.10 ou superior.'; print('Python OK:', sys.version.split()[0])"
if errorlevel 1 exit /b 1

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
(
  echo @echo off
  echo set "REPO_DIR=%REPO_DIR%"
  echo set "PYTHONPATH=%%REPO_DIR%%;%%PYTHONPATH%%"
  echo %PYTHON_CMD% -m mintlang.cli %%*
) > "%LAUNCHER%"

echo Launcher criado em %LAUNCHER%

echo %PATH% | find /I "%BIN_DIR%" >nul
if errorlevel 1 (
  setx PATH "%PATH%;%BIN_DIR%" >nul
  echo PATH atualizado. Feche e abra o terminal para aplicar.
)

echo Instalacao concluida. Rode: mint -file examples\hello.mint
endlocal
