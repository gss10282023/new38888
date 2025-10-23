# BIOTech Futures Hub

本仓库是 BIOTech Futures Hub 的完整全栈项目，包含：
- **后端**：Django REST API（魔法链接登录、用户/小组/活动/资源/公告等接口）
- **前端**：基于 Vue 3 + Vite 的单页应用
- **文档**：位于 `docs/` 目录的中英文技术文档

---

## 项目结构
```
new38888/
├── README.md                     # 中文说明（即本文档）
├── README.en.md                  # 英文说明
├── backend/                      # Django 后端项目
│   ├── manage.py
│   ├── requirements.txt
│   ├── btf_backend/              # 配置、URL、WSGI/ASGI
│   ├── authentication/           # 魔法链接 + JWT 认证流程
│   ├── users/                    # 用户与管理员接口
│   ├── groups/                   # 小组、里程碑、任务接口
│   ├── chat/                     # 小组聊天接口
│   ├── resources/                # 资源库接口
│   ├── events/                   # 活动接口
│   ├── announcements/            # 公告接口
│   ├── core/                     # 健康检查、文件上传、权限
│   └── ...
├── frontend/                     # Vue 3 + Vite 前端
│   ├── package.json
│   ├── src/
│   │   ├── main.js               # 程序入口
│   │   ├── App.vue               # 全局布局 + GSAP 动画
│   │   ├── router/               # Hash 路由与登录守卫
│   │   ├── stores/               # Pinia store（认证、资源、管理员等）
│   │   ├── views/                # 页面组件（仪表盘、管理员等）
│   │   └── assets/styles.css     # 全局样式与设计变量
│   └── ...
├── docs/                         # 技术文档
│   ├── API.md
│   ├── backend-overview.en.md / .zh.md
│   ├── frontend-overview.en.md / .zh.md
│   └── BACKEND_PLAN.md
├── tests/                        # 前后端测试套件（Django + Vitest，详见 docs/tests-overview.md）
├── package.json                  # 根目录依赖占位
├── package-lock.json
└── ...
```

---

## 运行环境要求
- **Python** 3.11 及以上（建议使用虚拟环境）
- **Node.js** 20.19 或 22.12 及以上
- **PostgreSQL**、**Redis**（可本地或云端部署）
- 需要配置 **Vultr Object Storage**（S3 兼容）和 **邮件服务** 才能在生产环境发送魔法链接邮件并存储文件

---

## 快速启动

### 1. 后端（Django API）
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt

# 创建 .env（示例见下方配置说明）
python manage.py migrate
python manage.py createsuperuser  # 可选：创建管理员
python manage.py runserver 0.0.0.0:8000
```

### 2. 前端（Vue 单页应用）
```bash
cd frontend
npm install
npm run dev            # 默认地址 http://localhost:5173
```

浏览器访问 http://localhost:5173 即可，并会使用 `VITE_API_BASE_URL` 指定的后端地址。若前后端分属不同域名，可在 `frontend/.env.local` 里同时配置 `VITE_API_BASE_URL` 与 `VITE_WS_BASE_URL`。

---

## 配置说明

### 后端环境变量 (`backend/.env`)
创建 `backend/.env`，例如：
```dotenv
# Django
SECRET_KEY=请替换
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库
DB_NAME=btf_db
DB_USER=btf_user
DB_PASSWORD=btf_password_2025
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis（缓存 & OTP 存储）
REDIS_URL=redis://127.0.0.1:6379/1

# 魔法链接中使用的前端地址
FRONTEND_BASE_URL=http://localhost:5173
MAGIC_LINK_EXPIRY_SECONDS=600

# 邮件默认使用控制台输出，生产环境请替换
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@biotechfutures.org
```

下一节将介绍如何切换 Vultr 存储和邮件服务。

---

### 前端环境变量 (`frontend/.env` 或 `.env.local`)
```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

- `VITE_API_BASE_URL`：前端请求后端 REST API 的基础地址，需包含 `/api` 路径。
- `VITE_WS_BASE_URL`：可选，用于覆盖 WebSocket 主机（群聊 Channels 连接等实时功能）。未设置时会复用 `VITE_API_BASE_URL` 的域名并自动推断 `ws://`/`wss://` 协议及 `/ws/chat/...` 路径。

---

## 更换 Vultr Object Storage（S3 兼容）
项目默认使用本地文件系统保存上传文件。若需改用 Vultr：

1. **确认依赖**：`requirements.txt` 已包含 `django-storages`、`boto3`，确保已安装。
2. **在 `.env` 中设置以下变量**：
   ```dotenv
   DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
   AWS_ACCESS_KEY_ID=<你的 Vultr Access Key>
   AWS_SECRET_ACCESS_KEY=<你的 Vultr Secret Key>
   AWS_STORAGE_BUCKET_NAME=<你的桶名称>
   AWS_S3_ENDPOINT_URL=https://<区域>.vultrobjects.com
   AWS_S3_REGION_NAME=<区域>         # 示例：sjc1
   AWS_S3_ADDRESSING_STYLE=virtual
   AWS_DEFAULT_ACL=public-read       # 可根据需要调整
   ```
3. **可选：自定义域名**  
   若启用了 CDN 或自定义域名，可设置 `AWS_S3_CUSTOM_DOMAIN`。
4. **如需让 Django 提供静态资源** 请运行 `python manage.py collectstatic`。
5. **重启后端**，新的资源上传（如资源库文件、活动封面、聊天附件）即会写入 Vultr 存储。

---

## 更换魔法链接邮件发送服务
认证流程会向用户发送包含魔法链接与 6 位 OTP 的邮件。生产环境可选择 SMTP 或第三方 ESP（如 SendGrid、Mailgun）：

1. **配置邮件后端**
   - 若使用 SMTP：
     ```dotenv
     EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
     EMAIL_HOST=smtp.sendgrid.net
     EMAIL_PORT=587
     EMAIL_USE_TLS=True
     EMAIL_HOST_USER=apikey                   # SendGrid 示例
     EMAIL_HOST_PASSWORD=<你的 SendGrid Key>
     DEFAULT_FROM_EMAIL=BIOTech Futures Hub <noreply@biotechfutures.org>
     ```
   - 若使用 Anymail（已在依赖中）：
     ```dotenv
     EMAIL_BACKEND=anymail.backends.sendgrid.EmailBackend
     ANYMAIL_SENDGRID_API_KEY=<你的 SendGrid Key>
     DEFAULT_FROM_EMAIL=noreply@biotechfutures.org
     ```
2. **更新前端地址**：若前端部署在其他域名，请同步修改 `FRONTEND_BASE_URL`，确保邮件中的链接正确。
3. **自定义邮件内容**（可选）：编辑 `backend/authentication/views.py` 内 `request_magic_link` 函数中的主题或正文。
4. **测试**：触发登录流程，检查邮件服务是否收到请求。使用 SMTP 时可在提供商控制台查看发送记录；使用默认 console backend 时则会在终端打印邮件内容。

---

## 常用命令
| 功能                           | 命令                                                                           |
|--------------------------------|--------------------------------------------------------------------------------|
| 安装后端依赖                  | `pip install -r backend/requirements.txt`                                      |
| 运行后端测试                  | `python manage.py test`                                                        |
| 运行全量测试                  | `./tests/run-all-tests.sh`                                                     |
| 生成数据库迁移                | `python manage.py makemigrations`                                              |
| 启动前端开发模式              | `npm run dev`（于 `frontend/` 目录下）                                         |
| 构建前端生产包                | `npm run build`                                                                |

---

## 测试与质量保证
- **测试目录**：所有后端、跨端、前端测试均位于 `tests/`，详细说明请参阅：
  - `docs/tests-overview.md`（中文）
  - `docs/tests-overview.en.md`（English）
- **一键执行全部测试：**
  ```bash
  chmod +x tests/run-all-tests.sh   # 首次赋权
  ./tests/run-all-tests.sh          # 顺序运行后端单元/API、跨端流程、前端 Vitest
  ```
  每个阶段都会打印结果，并在最后输出 ✅/❌ 汇总表。
- 也可按需单独运行：
  - `python manage.py test tests.backend`（后端 API/领域逻辑）
  - `python manage.py test tests.api tests.integration`（跨端流程）
  - `cd frontend && npm run test`（前端单元/集成）

---

## 延伸阅读
- 后端架构：`docs/backend-overview.zh.md`
- 前端架构：`docs/frontend-overview.zh.md`
- REST API 参考：`docs/API.md`

英文说明请参见 `README.en.md` 与 `docs` 下的英文文档。

---

_最后更新：2025 年 10 月 24 日_
