# BIOTech Futures Hub – 后端文档（中文版）

## 1. 项目概述
后端负责 BIOTech Futures Hub 平台的所有业务逻辑与数据服务，对外提供经过认证的 REST API，涵盖项目管理、团队协作、公告投放、活动管理、资源库以及群组聊天等核心能力。  
技术栈基于 Django 5.1 与 Django REST Framework（DRF），使用 PostgreSQL 作为主数据库、Redis 作为缓存与魔法链接令牌存储，文件上传依赖 Vultr Object Storage（S3 兼容）。

- 核心能力概览：
  - **无密码登录**：通过魔法链接 + 一次性验证码完成身份验证。
  - **角色权限体系**：学生、导师、督导、管理员四类角色配合 Django staff/superuser 标志，覆盖平台全部操作。
  - **团队协作**：支撑群组、成员、里程碑、任务等完整工作流。
  - **沟通通知**：群聊消息、资源文件、活动、公告等内容分发。
  - **管理后台接口**：支持用户筛选、状态更新、导出统计等运维需求。
  - **可扩展架构**：使用标准 Django/DRF 组件，方便增量开发与部署。

| 组件             | 技术 / 服务 |
|------------------|-------------|
| Web 框架         | Django 5.1（兼容 Python 3.13） |
| API 层           | Django REST Framework 3.15 |
| 认证             | JWT（djangorestframework-simplejwt）+ 邮件魔法链接 |
| 数据库           | PostgreSQL（psycopg2-binary） |
| 缓存 / OTP       | Redis（django-redis） |
| 对象存储         | Vultr Object Storage（S3 兼容，django-storages + boto3） |
| 邮件             | django-anymail（本地默认 console backend） |
| API 文档         | drf-spectacular（Swagger / Redoc） |
| 生产运行         | Gunicorn（WSGI） |

## 2. 代码结构
后端代码位于 `backend/` 目录，各模块遵循 DRF 的 models → serializers → views → urls 分层。

```
backend/
├── authentication/       # 魔法链接 + JWT 逻辑
│   ├── urls.py           # 对外认证入口
│   └── views.py          # OTP、Token 颁发、邮件发送
├── users/                # 用户与个人资料管理
│   ├── admin_urls.py     # 管理员专用端点
│   ├── serializers.py    # snake_case <-> camelCase
│   └── views.py          # 自助接口 & 管理接口
├── groups/               # 团队、里程碑、任务
│   ├── serializers.py
│   └── views.py
├── chat/                 # 群聊消息及附件元数据
├── resources/            # 资源库 CRUD + 上传
├── events/               # 活动管理与报名
├── announcements/        # 公告系统
├── core/                 # 健康检查、上传、公共权限
├── btf_backend/          # 全局 settings、urls、WSGI/ASGI
├── scripts/              # 管理脚本（如批量加人）
├── requirements.txt      # Python 依赖锁定
└── manage.py             # Django 命令入口
```

## 3. 配置与环境变量
全局配置位于 `backend/btf_backend/settings.py`，通过 `python-dotenv` 读取 `.env`。关键环境变量如下：

| 变量 | 说明 | 开发环境默认值 |
|------|------|----------------|
| `SECRET_KEY` | Django 密钥，生产环境必须显式设置。 | `django-insecure-default-key-change-in-production` |
| `DEBUG` | `"True"` / `"False"` 控制调试模式。 | `True` |
| `ALLOWED_HOSTS` | 允许访问的域名，逗号分隔。 | `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL 连接信息。 | `btf_db`, `btf_user`, 空, `localhost`, `5432` |
| `REDIS_URL` | Redis 连接串，例如 `redis://127.0.0.1:6379/1`。 | `redis://127.0.0.1:6379/1` |
| `CHANNEL_REDIS_URL` | 可选项：为 Django Channels 指定 WebSocket 发布/订阅专用 Redis，未设置时回退到 `REDIS_URL` 或内存实现。 | 默认未配置 |
| `FRONTEND_BASE_URL` | 魔法链接跳转基地址。 | `https://yourdomain.com` |
| `MAGIC_LINK_EXPIRY_SECONDS` | 魔法链接与 OTP 有效期（秒）。 | `600` |
| `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, `EMAIL_HOST` 等 | 邮件发送设置。 | 控制台输出 |
| `VULTR_ACCESS_KEY`, `VULTR_SECRET_KEY`, `VULTR_BUCKET_NAME`, `VULTR_S3_ENDPOINT` | 对象存储凭据与 Endpoint。 | 默认未配置（使用本地文件） |
| `JWT_ACCESS_TOKEN_LIFETIME_HOURS`, `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | JWT 生命周期覆盖。 | `1`, `7` |
| `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` | CORS 配置。 | `http://localhost:5173` |

环境建议：
- **开发环境**：`DEBUG=True`、控制台邮件 backend、不配置对象存储即可使用本地 `media/`。
- **预发环境**：与生产保持一致的第三方服务，仅缩小配额；Redis 与对象存储建议使用隔离前缀。
- **生产环境**：`DEBUG=False`、限制 `ALLOWED_HOSTS`、启用 HTTPS 与邮件服务、定期轮换密钥及访问凭据。

静态资源托管在 `staticfiles/`，可配合 CDN；上传文件默认写入 `media/`（生产建议配置 S3 存储）。

## 4. 认证 / 授权流程
1. **请求魔法链接**（`POST /api/auth/magic-link/`）：清洗邮箱、校验格式，在 Redis 存储 magic token + OTP，并发送邮件（包含链接与验证码）。  
2. **验证 OTP 或链接**（`POST /api/auth/verify-otp/`、`GET /api/auth/verify/`）：校验成功后签发 access / refresh token，同时返回用户信息。若邮箱首次出现，会自动创建 `User` + `UserProfile`。  
3. **刷新令牌**（`POST /api/auth/refresh/`）：根据 refresh token 下发新的 access/refresh 组合。  
4. **访问控制**：除认证及健康检查外，其余接口默认需要有效 JWT。

失败处理与防护：
- Redis 记录成功验证后会清除相关 key，确保 OTP / magic token 无法重复使用。
- Redis TTL 自带速率限制，若公开给互联网仍建议配合 API 网关限流或验证码。
- 新建用户设置不可用密码，强制全站通过魔法链接登录，避免出现密码登录入口。

角色体系（`users.User.role`）：
- `student`、`mentor`、`supervisor`：普通业务角色。
- `admin`：平台管理员，拥有 `IsPlatformAdmin` 权限。
- Django `is_staff` / `is_superuser`：用于 Django Admin 与高级操作，`superuser` 自动视为平台管理员。

## 5. 核心应用模块
### authentication
- 负责魔法链接、OTP 生成与校验。
- 依赖 Redis 缓存、邮件发送服务以及 `rest_framework_simplejwt`。
- 主要接口：`/api/auth/magic-link/`、`/api/auth/verify-otp/`、`/api/auth/verify/`、`/api/auth/refresh/`。
- 关键配置：`MAGIC_LINK_EXPIRY_SECONDS`、`FRONTEND_BASE_URL`。

### users
- 自定义 `User` 模型（邮箱登录、角色/状态/赛道字段）与 `UserProfile` 扩展信息。
- 用户自助接口：`/api/users/me/`，支持 PATCH 更新资料。
- 管理接口：`/api/admin/users/` 系列（用户列表、创建、更新、删除、状态修改、导出 CSV、过滤条件查询）。
- CSV 导出直接生成流式响应，避免临时文件。
- 安全策略：禁止管理员删除自身或 superuser；状态更新严格校验枚举。

### groups
- 模型：`Group`、`GroupMember`、`Milestone`、`Task`。
- 功能：群组列表、详情、创建/删除（限管理员）、里程碑与任务增删改、成员可见范围控制。
- `_user_can_manage_group` 集中校验权限，支持管理员/督导/导师/成员多层权限。
- 查询优化：`select_related("mentor")`、`prefetch_related("members__user", "milestones__tasks")`。

### chat
- 模型：`Message`、`MessageAttachment`（仅存储文件元数据）。
- 接口：`GET /api/groups/<id>/messages` 支持 `limit` + `before` 游标，`POST` 发送消息并附带附件信息。
- 上传文件需先通过 `/api/uploads/` 获得 URL，再写入消息附件。
- `hasMore` 字段用于前端判断是否继续向上拉取历史记录。

### resources
- 模型：`Resource`（类型、角色、描述、封面、下载次数）。
- 接口：列表/详情对所有认证用户开放；上传、删除、封面更新仅管理员可用。
- 上传流程：多部分表单 → Django Storage（本地或 S3） → 返回文件 URL。
- 角色过滤：普通用户仅能访问 `role=all` 或匹配自身角色的资源，管理员可查看全部。

### events
- 模型：`Event`、`EventRegistration`。
- 管理功能：创建、删除、封面上传（PUT `/cover/`）。
- 用户功能：按类型、即将开始（`upcoming=true`）、关键词搜索；报名接口会阻止重复报名（HTTP 400）。
- `registration_count` 通过 queryset 注解获取。

### announcements
- 模型：`Announcement`，受众枚举包括 `all`、`student`、`mentor`、`supervisor`、`admin`。
- 管理员可创建、删除公告；普通角色仅能看到 `all` 或自身角色对应的公告。
- 支持标题、摘要、正文全文搜索，默认按创建时间倒序。

### core
- `/api/health/`：综合检测数据库与 Redis，失败返回 503，并附带错误信息。
- `/api/uploads/`：认证用户的文件上传接口，返回文件 URL、文件名、大小、MIME 类型。
- `permissions.IsPlatformAdmin`：跨模块复用的管理员权限判断。
- 后续可在此模块扩展分页、存储、日志等通用工具。

## 6. 数据模型要点
- `users.User`：重写 `USERNAME_FIELD` 为 `email`，新增 `role`、`track`、`status`；`get_full_name` 支持回退邮箱。
- `users.UserProfile`：补充姓名、兴趣、学校、年级、地区、可用时间、简介等字段；`areas_of_interest` 使用 JSON 列表。
- `groups.Group`：自定义字符串主键（如 `BTF046`），包含导师引用与状态。
- `groups.GroupMember`：`unique_together` 保证同一用户仅能在同一群组关联一次。
- `groups.Milestone` / `Task`：支持排序（`order_index`）与任务完成状态。
- `chat.MessageAttachment`：记录文件 URL、名称、大小、MIME 类型，便于前端渲染。
- `resources.Resource`：下载次数字段预留，后续可在下载接口自增。
- `events.EventRegistration`：数据库层面限制重复报名。

关系示意：
```
User ──1:1── UserProfile
   │
   ├─1:M── Group (mentor 角色)
   ├─M:N── GroupMember──Group──Milestone──Task
   ├─1:M── Message──MessageAttachment
   ├─1:M── EventRegistration──Event
   └─未来可扩展 Resource 创建者字段
```

所有时间字段使用 UTC 自动填充，删除策略按照 `on_delete` 配置执行（群组成员、任务采用级联删除，导师引用为 `SET_NULL`）。

## 7. 外部服务集成
- **邮件**：默认使用 console backend，将邮件内容打印到日志；生产环境建议接入 Anymail 对接 SendGrid/Mailgun 等服务，并配置 SPF/DKIM。
- **对象存储**：`django-storages` + `boto3` 与 Vultr S3 兼容存储交互，存储路径分别为 `uploads/`、`resources/files/`、`resources/covers/`、`events/covers/`。
- **Redis**：通过 `django-redis` 作为默认缓存，既用于魔法链接令牌，也可扩展其他缓存逻辑。
- **实时消息（Channels）**：群聊 WebSocket 由 Django Channels 驱动，建议配置 `CHANNEL_REDIS_URL`（可复用 `REDIS_URL`）以便所有 ASGI Worker 共用同一 Redis 实例。
- **DRF Spectacular**：生成 OpenAPI 3.0 文档，提供 Swagger (`/api/docs/`) 与 Redoc (`/api/redoc/`)。
- **Django Admin**：超级用户可通过 `/admin/` 检视和维护底层数据。

## 8. 本地开发流程
1. 安装依赖
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 配置 `.env`（可从第 3 节表格复制）。若未配置数据库，可临时使用 SQLite，但 OTP 邮件会打印在控制台。
3. 执行迁移
   ```bash
   python manage.py migrate
   ```
4. （可选）创建管理员
   ```bash
   python manage.py createsuperuser
   ```
5. 启动开发服务器
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
6. 运行测试
   ```bash
   python manage.py test
   ```

辅助脚本：
- `backend/install_dependencies.sh`：安装系统级依赖（CI 初始化使用）。
- `backend/setup_database.sh`：创建 PostgreSQL 数据库与用户。
- `backend/scripts/add_users_to_group.py`：在 Django shell 中批量创建用户与群组关系。
- `backend/test_step*.sh`：课程里程碑提供的自动化脚本，复用前请先确认逻辑是否仍适用。

## 9. 部署注意事项
- 生产环境推荐架构：反向代理（NGINX）→ Gunicorn → Django 应用。TLS 终止与压缩可在 NGINX 完成。
- 发布流程应包含 `python manage.py migrate`，确保数据库结构同步。
- 使用 `python manage.py collectstatic` 将静态资源上传至 CDN 或对象存储。
- 配置环境变量（数据库、Redis、对象存储、邮件、CORS、JWT 生命周期等）。
- `DEBUG=False` 时务必配置正确的日志、文件存储凭据及邮件服务，否则上传和魔法链接会失败。
- 注意将健康检查（`/api/health/`）放通在负载均衡安全组中。

## 10. 运维与监控
- **健康检查**：`/api/health/` 同时检查 PostgreSQL 与 Redis，失败返回 503；可直接集成到负载均衡或监控系统。
- **API 文档**：Swagger 与 Redoc 页面实时反映最新 schema，便于前后端联调。
- **缓存监测**：Redis 若不可用，将导致登录/刷新失败，需设置告警。
- **日志**：魔法链接发送在 `authentication.views` 中记录，生产环境建议配置文件日志或集中式日志平台。
- **指标**：暂无内置 Metrics，可在 NGINX 或新增中间件中扩展。
- **备份**：定期备份 PostgreSQL、Redis；对象存储可启用版本控制或生命周期策略。

## 11. 已知限制 / 后续改进方向
- 资源下载次数尚未和真实下载动作对接。
- 活动暂不支持 PATCH 部分更新，如需修改需扩展序列化器与视图逻辑。
- 魔法链接邮件为纯文本，可考虑制作 HTML 模板和品牌化样式。
- 未集成后台任务队列，若未来需要批量通知或异步任务，可评估 Celery/RQ。
- 限流、防暴力破解依赖上层网关，后续可使用 DRF Throttle 或 WAF。
- 文件上传默认为公开 URL，若需私有访问可引入签名链接或临时凭证。

## 12. 参考资料
- API 详细协议：`docs/API.md`
- 历史规划记录：`docs/BACKEND_PLAN.md`
- 前端请求示例：`frontend/src/views/`（用于了解数据结构）

## 13. 请求生命周期与中间件
1. 请求到达 Gunicorn（生产）或 `runserver`（本地）。
2. 经过中间件（CORS、Security、Session、CSRF、Authentication）处理。
3. DRF 执行内容协商、JWT 校验、权限判定、分页/过滤等。
4. 序列化器进行输入校验与输出格式化。
5. 响应回传时再次叠加中间件（如 CORS Header、Security Header）。

中间件亮点：
- `corsheaders.middleware.CorsMiddleware`：处理跨域预检与响应头。
- `django.middleware.security.SecurityMiddleware`：可启用 HSTS、HTTPS 重定向等安全策略。
- 默认分页器为 `PageNumberPagination`，可通过 `page` / `page_size` 控制大小。

## 14. 安全注意事项
- **传输层**：生产环境务必启用 HTTPS，可在 NGINX 层开启 `SECURE_SSL_REDIRECT`。
- **密钥管理**：`SECRET_KEY` 泄露需立即轮换；JWT 使用 HS256 签名，依赖同一密钥。
- **CORS**：上线后应仅允许可信前端域名。
- **管理员接口**：由 `IsPlatformAdmin` 守护，管理员账号建议设置企业邮箱并结合邮件安全策略。
- **文件上传**：目前仅校验字段存在，若要限制类型或进行病毒扫描需自行扩展。
- **滥用检测**：魔法链接接口可能被用于邮箱探测，可结合网关限流或验证码增强防护。

## 15. 测试策略
- **单元测试**：各 app 默认为 `tests.py`，推荐拆分成 `tests/` 目录以覆盖模型、视图、序列化器。
- **集成测试**：使用 DRF `APIClient` 验证完整流程（魔法链接 → JWT → 业务接口）。
- **脚本测试**：管理脚本可通过 `call_command` 在测试中调用，确保可重复执行。
- **CI 建议**：部署前执行 `python manage.py test`，并可引入 flake8、black 等静态检查。
- **测试数据**：可使用 JSON Fixture 预置群组、用户、公告等场景。

## 16. 数据初始化与演示账号
- `backend/scripts/add_users_to_group.py`：快速创建示例群组和用户成员关系。
- 魔法链接流程可在演示环境快速拉起新账号，建议配置临时 SMTP 服务便于验证。
- 可考虑新增管理命令，支持批量导入用户/资源/活动（待规划）。

## 17. 故障排查与支持
- **PostgreSQL 连接失败**：检查 `.env` 凭据、确保数据库实例与用户存在、排查防火墙或 VPC 规则。
- **Redis 报错**：健康检查失败会返回 503，需确认 Redis 服务是否运行并可被访问。
- **文件上传异常**：核对对象存储凭据与 Bucket 权限；本地需确保 `media/` 可写。
- **邮件未送达**：控制台 backend 会在终端输出；若使用真实 SMTP，需检查 SPF/DKIM 和 API Key。
- **JWT 签名无效**：多实例部署必须共享同一 `SECRET_KEY`，轮换后记得重启 Gunicorn。

_最后更新：2025 年 10 月 24 日_
