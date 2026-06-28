@echo off
chcp 65001 > nul
echo ========================================
echo   构建象棋助手可执行程序
echo ========================================
echo.

REM 检查 PyInstaller 是否安装
python -m PyInstaller --version > nul 2>&1
if errorlevel 1 (
    echo 未检测到 PyInstaller，正在安装...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo PyInstaller 安装失败，请检查网络或 pip 配置。
        pause
        exit /b 1
    )
)

echo 正在清理旧的构建产物...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo 正在打包，请稍候...
python -m PyInstaller xiangqi.spec --noconfirm
if errorlevel 1 (
    echo.
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo 正在生成发布压缩包...
powershell -Command "Compress-Archive -Path 'dist/象棋助手/*' -DestinationPath 'dist/象棋助手.zip' -Force"

echo.
echo ========================================
echo   构建完成！
echo ========================================
echo.
echo 可执行程序: dist\象棋助手\象棋助手.exe
echo 发布压缩包: dist\象棋助手.zip
echo.
echo 把 dist\象棋助手.zip 上传到 GitHub Release 即可。
echo.
pause
