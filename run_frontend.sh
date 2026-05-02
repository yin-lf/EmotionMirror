#!/bin/bash
# 前端启动脚本
# 使用方式：bash run_frontend.sh

echo "=========================================="
echo "  EmotionMirror Frontend"
echo "  http://localhost:5173"
echo "=========================================="

cd frontend

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

npm run dev
