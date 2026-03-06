@echo off
setlocal
set "ROOT_DIR=%~dp0"
where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PYTHON_CMD=py -3"
) else (
  set "PYTHON_CMD=python"
)
set "PYTHONPATH=%ROOT_DIR%;%PYTHONPATH%"
%PYTHON_CMD% -m mintlang.cli %*
endlocal
