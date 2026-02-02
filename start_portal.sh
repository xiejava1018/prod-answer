#!/bin/bash

echo "=== 产品门户启动脚本 ==="
echo

# 检查端口占用
function check_port() {
    local port=$1
    local name=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo "❌ 端口 $port 已被占用，$name 可能已在运行"
        return 1
    fi
    return 0
}

# 启动后端
echo "1. 启动后端服务..."
cd backend

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "   激活虚拟环境..."
    source venv/bin/activate
else
    echo "   ⚠️  未找到虚拟环境，使用系统Python"
fi

# 检查端口
if check_port 8000 "Django"; then
    echo "   启动 Django 开发服务器..."
    python manage.py runserver 0.0.0.0:8000 &
    DJANGO_PID=$!
    echo "   ✅ Django 已启动 (PID: $DJANGO_PID)"
else
    echo "   ⚠️  Django 可能已在运行，跳过启动"
fi

cd ..

# 启动前端
echo
echo "2. 启动前端服务..."
cd frontend

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "   安装依赖..."
    npm install
fi

# 检查端口
if check_port 5173 "Vite"; then
    echo "   启动 Vite 开发服务器..."
    npm run dev &
    VITE_PID=$!
    echo "   ✅ Vite 已启动 (PID: $VITE_PID)"
else
    echo "   ⚠️  Vite 可能已在运行，跳过启动"
fi

cd ..

echo
echo "=== 启动完成 ==="
echo
echo "📊 产品门户已启动："
echo "   - 门户首页: http://localhost:5173/portal"
echo "   - 产品列表: http://localhost:5173/portal/products"
echo "   - API文档: http://localhost:8000/api/v1/portal/"
echo
echo "📝 日志文件："
echo "   - 后端日志: backend/logs/"
echo "   - 前端日志: 终端输出"
echo
echo "🛑 停止服务："
echo "   - 按 Ctrl+C 停止所有服务"
echo "   - 或运行: pkill -f 'manage.py runserver'"
echo "   - 或运行: pkill -f 'vite'"
echo

# 等待用户输入
echo "按 Ctrl+C 停止所有服务..."
wait
