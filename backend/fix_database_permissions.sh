#!/bin/bash

echo "==================================="
echo "修复数据库权限问题"
echo "==================================="
echo ""

DB_NAME="btf_db"
DB_USER="btf_user"
DB_PASSWORD="btf_password_2025"

echo "数据库名称: $DB_NAME"
echo "用户名: $DB_USER"
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "在 macOS 上修复数据库权限..."

    psql postgres << EOF
-- 删除旧数据库（如果存在）
DROP DATABASE IF EXISTS $DB_NAME;

-- 删除旧用户（如果存在）
DROP USER IF EXISTS $DB_USER;

-- 创建用户
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- 创建数据库，设置 owner
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- 赋予用户权限
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- 连接到数据库并设置 schema 权限
\c $DB_NAME

-- 赋予 public schema 权限
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- PostgreSQL 15+ 需要额外的 CREATE 权限
GRANT CREATE ON SCHEMA public TO $DB_USER;

\q
EOF

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "在 Linux 上修复数据库权限..."

    sudo -u postgres psql << EOF
-- 删除旧数据库（如果存在）
DROP DATABASE IF EXISTS $DB_NAME;

-- 删除旧用户（如果存在）
DROP USER IF EXISTS $DB_USER;

-- 创建用户
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';

-- 创建数据库，设置 owner
CREATE DATABASE $DB_NAME OWNER $DB_USER;

-- 赋予用户权限
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- 连接到数据库并设置 schema 权限
\c $DB_NAME

-- 赋予 public schema 权限
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- 设置默认权限
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- PostgreSQL 15+ 需要额外的 CREATE 权限
GRANT CREATE ON SCHEMA public TO $DB_USER;

\q
EOF

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "在 Windows 上修复数据库权限..."
    echo ""
    echo "请手动执行以下 SQL 命令："
    echo ""
    echo "打开 pgAdmin 或命令行工具，连接到 PostgreSQL，然后执行："
    echo ""
    echo "DROP DATABASE IF EXISTS $DB_NAME;"
    echo "DROP USER IF EXISTS $DB_USER;"
    echo "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    echo "CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    echo "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    echo "\c $DB_NAME"
    echo "GRANT ALL ON SCHEMA public TO $DB_USER;"
    echo "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
    echo "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
    echo "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;"
    echo "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;"
    echo "GRANT CREATE ON SCHEMA public TO $DB_USER;"
    exit 0
fi

# 验证
echo ""
echo "==================================="
echo "验证数据库权限..."
echo "==================================="

if [[ "$OSTYPE" == "darwin"* ]]; then
    psql -d $DB_NAME -U $DB_USER -c "SELECT version();" > /dev/null 2>&1
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PGPASSWORD=$DB_PASSWORD psql -h localhost -d $DB_NAME -U $DB_USER -c "SELECT version();" > /dev/null 2>&1
fi

if [ $? -eq 0 ]; then
    echo "✅ 数据库权限修复成功！"
    echo ""
    echo "现在可以运行："
    echo "  python manage.py migrate"
else
    echo "❌ 数据库连接失败，请检查配置"
    exit 1
fi

echo ""
echo "==================================="
echo "完成！"
echo "==================================="