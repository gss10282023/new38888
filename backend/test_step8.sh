#!/bin/bash

echo "==================================="
echo "Step 8 测试脚本 - 公告系统"
echo "==================================="
echo ""

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  请先激活虚拟环境:"
    echo "   source venv/bin/activate  (macOS/Linux)"
    echo "   venv\\Scripts\\activate     (Windows)"
    exit 1
fi

echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
echo ""

echo "运行公告模块测试..."
python manage.py test announcements
TEST_RESULT=$?

if [[ $TEST_RESULT -ne 0 ]]; then
    echo ""
    echo "❌ 测试未通过，请查看上方错误日志。"
    exit $TEST_RESULT
fi

echo ""
echo "✅ Step 8 测试通过！"
echo "   - 公告列表按角色过滤与搜索正确"
echo "   - 公告详情、管理员创建功能验证通过"
echo ""
echo "手动验证建议："
echo "1. 启动后端：python manage.py runserver"
echo "2. 管理员账号调用：POST /api/announcements/ 创建公告"
echo "3. 学生账号访问：GET /api/announcements/，确认只看到面向自己的公告"
echo ""
