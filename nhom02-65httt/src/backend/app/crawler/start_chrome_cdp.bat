@echo off
setlocal EnableExtensions
title ERP Smart Pricing - Chrome Headful CDP (Port 9222)
set "PORT=9222"
set "PROFILE=%LOCALAPPDATA%\ERP_SmartPricing_ChromeProfile"

if not exist "%PROFILE%" (
  mkdir "%PROFILE%" >nul 2>&1
)

set "CHROME="
for %%P in (
  "%ProgramFiles%\Google\Chrome\Application\chrome.exe"
  "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
  "%LocalAppData%\Google\Chrome\Application\chrome.exe"
) do (
  if not defined CHROME if exist "%%~P" set "CHROME=%%~P"
)

if not defined CHROME (
  echo [LOI] Khong tim thay chrome.exe trong he thong.
  pause
  exit /b 1
)

echo ============================================================================
echo  KHOI CHAY CHROME HEADFUL CDP (PORT %PORT%)
echo  Profile: %PROFILE%
echo ============================================================================
echo.
echo Hay dang nhap tai khoan Shopee / TikTok / Lazada tren cua so Chrome nay
echo (va giai xac minh tay neu san yeu cau). Sau do chay tu src\backend:
echo   python -m app.crawler.chrome_cdp_collector --diagnose
echo   python -m app.crawler.chrome_cdp_collector --url "https://shopee.vn/..."
echo   python -m app.crawler.chrome_cdp_collector --listen 60
echo.
start "" "%CHROME%" --remote-debugging-port=%PORT% --user-data-dir="%PROFILE%" --start-maximized --new-window --no-first-run --no-default-browser-check --remote-allow-origins=* "https://shopee.vn/buyer/login" "https://www.tiktok.com/login" "https://www.lazada.vn/"
exit /b 0
