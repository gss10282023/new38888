#!/bin/bash

echo "==================================="
echo "创建 PostgreSQL 数据库"
echo "==================================="

# 数据库配置
DB_NAME="btf_db"
DB_USER="btf_user"
DB_PASSWORD="btf_password_2025"

echo "数据库名称: $DB_NAME"
echo "用户名: $DB_USER"
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "在 macOS 上创建数据库..."

    # 创建数据库和用户
    psql postgres << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "在 Linux 上创建数据库..."

    sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\q
EOF

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "在 Windows 上创建数据库..."
    echo ""
    echo "请手动执行以下步骤："
    echo ""
    echo "1. 打开 pgAdmin 或命令行工具"
    echo "2. 连接到 PostgreSQL（用户: postgres）"
    echo "3. 执行以下 SQL："
    echo ""
    echo "CREATE DATABASE $DB_NAME;"
    echo "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    echo "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    echo ""
    echo "或者在命令行运行："
    echo "psql -U postgres -c \"CREATE DATABASE $DB_NAME;\""
    echo "psql -U postgres -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\""
    echo "psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""
    exit 0
fi

# 验证数据库创建
echo ""
echo "==================================="
echo "验证数据库..."
echo "==================================="

if [[ "$OSTYPE" == "darwin"* ]]; then
    psql -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo -u postgres psql -d $DB_NAME -c "SELECT version();" > /dev/null 2>&1
fi

if [ $? -eq 0 ]; then
    echo "✅ 数据库 $DB_NAME 创建成功！"
else
    echo "❌ 数据库创建失败，请检查错误信息"
    exit 1
fi

echo ""
echo "==================================="
echo "数据库配置信息"
echo "==================================="
echo "数据库名: $DB_NAME"
echo "用户名: $DB_USER"
echo "密码: $DB_PASSWORD"
echo "主机: localhost"
echo "端口: 5432"
echo ""
echo "这些信息将用于 .env 配置文件"
echo ""
echo "下一步：创建 Django 项目"
echo "运行: django-admin startproject btf_backend ."