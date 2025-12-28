#!/bin/bash

echo "==================================="
echo "Smoke 脚本：资源库"
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

echo "运行资源库相关自动化测试..."
python manage.py test resources

TEST_EXIT=$?

if [[ $TEST_EXIT -ne 0 ]]; then
    echo ""
    echo "❌ 测试未通过，请检查上方输出。"
    exit $TEST_EXIT
fi

echo ""
echo "✅ Smoke 检查通过！"
echo "   - 资源模型与 API 可用"
echo "   - 上传/封面/权限 行为已验证"
echo ""
echo "下一步："
echo "1. 如需更多数据，可通过 Django Admin 上传资源。"
echo "2. 前端可调用 /api/resources 接口进行联调。"
echo ""
