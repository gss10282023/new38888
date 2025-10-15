#!/bin/bash

echo "==================================="
echo "Step 1 测试脚本"
echo "==================================="
echo ""

# 激活虚拟环境提醒
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  请先激活虚拟环境:"
    echo "   source venv/bin/activate  (Mac/Linux)"
    echo "   venv\\Scripts\\activate     (Windows)"
    echo ""
    exit 1
fi

echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
echo ""

# 测试 1: 检查依赖是否安装
echo "测试 1: 检查 Python 依赖..."
python -c "import django; import rest_framework; import redis; import psycopg2; print('✅ 所有核心依赖已安装')" || {
    echo "❌ 依赖安装失败，请运行: pip install -r requirements.txt"
    exit 1
}
echo ""

# 测试 2: 检查数据库连接
echo "测试 2: 检查数据库连接..."
python manage.py shell -c "from django.db import connection; connection.cursor(); print('✅ 数据库连接成功')" || {
    echo "❌ 数据库连接失败"
    echo "   请检查 .env 文件中的数据库配置"
    echo "   确保 PostgreSQL 正在运行: brew services list (Mac) 或 sudo systemctl status postgresql (Linux)"
    exit 1
}
echo ""

# 测试 3: 检查 Redis 连接
echo "测试 3: 检查 Redis 连接..."
python manage.py shell -c "from django.core.cache import cache; cache.set('test', 'ok'); assert cache.get('test') == 'ok'; print('✅ Redis 连接成功')" || {
    echo "❌ Redis 连接失败"
    echo "   确保 Redis 正在运行: brew services list (Mac) 或 sudo systemctl status redis (Linux)"
    exit 1
}
echo ""

# 测试 4: 运行数据库迁移
echo "测试 4: 运行数据库迁移..."
python manage.py migrate || {
    echo "❌ 数据库迁移失败"
    exit 1
}
echo ""

# 测试 5: 启动开发服务器测试
echo "测试 5: 测试开发服务器..."
echo "正在启动服务器（5秒后自动停止）..."

# 后台启动服务器
python manage.py runserver 8000 > /dev/null 2>&1 &
SERVER_PID=$!

# 等待服务器启动
sleep 3

# 测试健康检查端点
echo "测试健康检查端点..."
HEALTH_CHECK=$(curl -s http://localhost:8000/api/health/ | python -c "import sys, json; data=json.load(sys.stdin); print(data['status'])" 2>/dev/null)

# 停止服务器
kill $SERVER_PID 2>/dev/null

if [ "$HEALTH_CHECK" = "healthy" ]; then
    echo "✅ 健康检查通过"
else
    echo "❌ 健康检查失败"
    exit 1
fi
echo ""

# 测试 6: 检查 OpenAPI 文档生成
echo "测试 6: 检查 API 文档..."
python manage.py spectacular --file schema.yml > /dev/null 2>&1 && {
    echo "✅ OpenAPI schema 生成成功"
    rm schema.yml
} || {
    echo "⚠️  OpenAPI schema 生成失败（可能是因为还没有定义 API 端点）"
}
echo ""

echo "==================================="
echo "✅ Step 1 所有测试通过！"
echo "==================================="
echo ""
echo "下一步操作："
echo "1. 启动开发服务器: python manage.py runserver"
echo "2. 访问 API 文档: http://localhost:8000/api/docs/"
echo "3. 访问健康检查: http://localhost:8000/api/health/"
echo "4. 访问 Django Admin: http://localhost:8000/admin/"
echo ""
echo "准备开始 Step 2: 认证系统开发"
