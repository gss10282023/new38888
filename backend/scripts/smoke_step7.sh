#!/bin/bash

echo "==================================="
echo "Smoke 脚本：活动管理"
echo "==================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "⚠️  请先激活虚拟环境:"
    echo "   source venv/bin/activate  (macOS/Linux)"
    echo "   venv\\Scripts\\activate     (Windows)"
    exit 1
fi

echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
echo ""

echo "运行活动模块相关测试..."
python manage.py test events
TEST_RESULT=$?

if [[ $TEST_RESULT -ne 0 ]]; then
    echo ""
    echo "❌ 测试未通过，请查看上方错误日志。"
    exit $TEST_RESULT
fi

echo ""
echo "✅ Smoke 检查通过！"
echo "   - 活动列表 / 详情 / 报名 API 正常工作"
echo "   - 封面上传仅管理员可操作"
echo ""
echo "手动验证建议："
echo "1. 启动后端：python manage.py runserver"
echo "2. 用管理员账号访问 /api/events/，尝试创建活动和上传封面"
echo "3. 用学生账号访问 /api/events/{id}/register 测试报名功能"
echo ""
