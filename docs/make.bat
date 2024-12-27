@ECHO OFF

pushd %~dp0

REM

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)

set SOURCEDIR = .
set BUILDDIR = _build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL

if errorlevel 9009 (
	echo.
	echo. The 'sphinx-build' command was not found.
	echo.
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %0%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %0%

:end
popd