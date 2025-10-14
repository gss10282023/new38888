#!/bin/bash

# 安装脚本 - 根据你的操作系统选择执行

echo "==================================="
echo "BIOTech Futures Hub - 环境安装脚本"
echo "==================================="

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到 macOS 系统"

    # 检查是否安装 Homebrew
    if ! command -v brew &> /dev/null; then
        echo "正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    echo "正在安装 PostgreSQL..."
    brew install postgresql@15
    brew services start postgresql@15

    echo "正在安装 Redis..."
    brew install redis
    brew services start redis

    echo "✅ PostgreSQL 和 Redis 已安装并启动"

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "检测到 Linux 系统"

    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        echo "正在更新包管理器..."
        sudo apt-get update

        echo "正在安装 PostgreSQL..."
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql

        echo "正在安装 Redis..."
        sudo apt-get install -y redis-server
        sudo systemctl start redis
        sudo systemctl enable redis

        echo "✅ PostgreSQL 和 Redis 已安装并启动"
    else
        echo "❌ 不支持的 Linux 发行版，请手动安装 PostgreSQL 和 Redis"
        exit 1
    fi

elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "检测到 Windows 系统"
    echo ""
    echo "请手动安装以下软件："
    echo ""
    echo "1. PostgreSQL:"
    echo "   下载地址: https://www.postgresql.org/download/windows/"
    echo "   安装时记住你设置的密码（默认用户是 postgres）"
    echo ""
    echo "2. Redis:"
    echo "   下载地址: https://github.com/tporadowski/redis/releases"
    echo "   或使用 WSL/Docker 运行 Redis"
    echo ""
    echo "3. 安装完成后，继续执行后续步骤"
    exit 0
else
    echo "❌ 未知操作系统: $OSTYPE"
    exit 1
fi

# 验证安装
echo ""
echo "==================================="
echo "验证安装..."
echo "==================================="

# 检查 PostgreSQL
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL 已安装"
    psql --version
else
    echo "❌ PostgreSQL 未找到"
fi

# 检查 Redis
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis 已安装"
    redis-cli --version
else
    echo "❌ Redis 未找到"
fi

echo ""
echo "==================================="
echo "安装完成！"
echo "==================================="
echo "下一步：创建数据库"
echo "运行: bash setup_database.sh"