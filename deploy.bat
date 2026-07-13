@echo off
echo === Building frontend ===
cd /d %~dp0frontend
call npx vite build

echo === Packaging ===
cd /d %~dp0
rmdir /s /q www\assets 2>nul
mkdir www\assets
xcopy /s /y frontend\dist\* www\ 2>nul
cd www
tar czf ..\deploy.tar.gz .

echo === Deploying to ECS ===
scp -i %USERPROFILE%\.ssh\baota_ecs_key -o StrictHostKeyChecking=no ..\deploy.tar.gz root@39.96.86.119:/www/wwwroot/csic.thinkalike.com.cn/
ssh -i %USERPROFILE%\.ssh\baota_ecs_key -o StrictHostKeyChecking=no root@39.96.86.119 "cd /www/wwwroot/csic.thinkalike.com.cn/www && rm -rf assets/* && tar xzf /www/wwwroot/csic.thinkalike.com.cn/deploy.tar.gz && nginx -s reload"

echo === Verifying ===
curl -s https://csic.thinkalike.com.cn/api/health
echo.
echo DONE - Ctrl+Shift+R to hard refresh
