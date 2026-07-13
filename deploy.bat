@echo off
echo === Building frontend ===
cd /d %~dp0frontend
call npx vite build

echo === Cleaning outputs ===
cd /d %~dp0
rmdir /s /q www\assets 2>nul
mkdir www\assets

echo === Copying dist ===
xcopy /s /y frontend\dist\* www\

echo === Uploading to ECS ===
scp -i %USERPROFILE%\.ssh\baota_ecs_key -o StrictHostKeyChecking=no -r www\assets root@39.96.86.119:/www/wwwroot/csic.thinkalike.com.cn/www/
scp -i %USERPROFILE%\.ssh\baota_ecs_key -o StrictHostKeyChecking=no www\index.html root@39.96.86.119:/www/wwwroot/csic.thinkalike.com.cn/www/

echo === Verifying ===
curl -s https://csic.thinkalike.com.cn/api/health
echo.
echo DONE - Ctrl+Shift+R to hard refresh
