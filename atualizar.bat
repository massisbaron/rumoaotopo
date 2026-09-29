@echo off
REM Atualiza os preços pelo seu computador e publica (use se o robô do GitHub for bloqueado).
REM Usa a planilha Documentos\Links afiliados.xlsx como fonte.
cd /d "%~dp0"
copy /Y "%USERPROFILE%\Documents\Links afiliados.xlsx" data\links.xlsx >nul
python scripts\scrape.py || goto :fim
python scripts\build.py || goto :fim
git add data && git commit -m "Atualiza precos" && git push
:fim
pause
