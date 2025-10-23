# 测试体系说明（中文）

本文档详尽介绍 BIOTech Futures Hub 项目的测试框架、目录结构、单个测试用例职能与运行方式，覆盖后端 Django REST API、前端 Vue 3 应用以及跨层集成流程，帮助团队快速理解并扩展质量保障体系。

## 1. 总览
- **测试根目录：** `tests/`
- **测试范围：**
  - `tests/backend/` – Django/DRF API 及领域逻辑测试
  - `tests/api/` – 跨端认证与后台工作流验证
  - `tests/integration/` – 跨服务协同与角色可见性 E2E 场景
  - `tests/frontend/` – 前端 Pinia Store、Vue 组件、路由守卫及工具单测/集成测
- **新增前端依赖：** `vitest`、`@vue/test-utils`、`@testing-library/vue`、`msw`、`@testing-library/jest-dom` 等，已记录在 `frontend/package.json`
- **后端依赖：** 继续使用 `backend/requirements.txt`

## 2. 目录结构

```
tests/
├── backend/                # Django/DRF 测试：认证、用户、组、资源、事件、公告、聊天、核心服务
│   ├── base.py             # 通用测试基类（创建用户、组、里程碑等）
│   └── test_*.py           # 具体 API 与逻辑场景
├── api/                    # 跨端流程测试（魔法登录、后台操作闭环）
├── integration/            # 端到端业务场景（组协作、内容访问矩阵）
└── frontend/               # 前端测试
    ├── mocks/              # MSW 模拟服务
    ├── unit/               # Pinia Store / 组件 / 工具单测
    ├── integration/        # Vue Router 守卫等跨模块用例
    └── vitest.setup.js     # Vitest 全局初始化（jsdom、MSW、IntersectionObserver 等）
```

## 3. 详细测试清单

### 3.1 后端（`tests/backend/`）
| 测试文件 | 主要覆盖点 |
| --- | --- |
| `base.py` | 提供 `AuthenticatedAPITestCase`：创建不同角色用户、组、里程碑、任务及便捷登录方法。 |
| `test_authentication.py` | 魔法链接/OTP 申请与验证、刷新令牌异常场景、缓存清理、邮件发送内容。 |
| `test_users_api.py` | `/users/me/` 获取与更新、管理员用户列表筛选/分页/导出、状态更新、权限拦截（自删/删超管）。 |
| `test_groups_api.py` | 组列表可见性、我的小组、组详情、任务增删改、里程碑管理、管理员组创建与删除、权限边界。 |
| `test_resources_api.py` | 资源列表角色过滤、资源上传（含存储 mock）、封面更新、删除权限。 |
| `test_events_api.py` | 事件列表筛选、管理员创建、报名、防重复、封面上传。 |
| `test_announcements_api.py` | 公告角色过滤、管理员发布与删除。 |
| `test_chat_api.py` | 群聊历史分页、参数校验、成员权限校验、含附件的消息创建。 |
| `test_core_endpoints.py` | 健康检查（数据库/Redis 正常与异常）、认证上传、缺文件报错。 |

### 3.2 跨端 API（`tests/api/`）
| 测试文件 | 主要覆盖点 |
| --- | --- |
| `test_auth_flow.py` | 魔法链接登录、OTP 验证、获取/更新个人信息完整流程。 |
| `test_admin_workflow.py` | 管理员创建小组、查看统计、筛选用户、更新学生状态的闭环场景。 |

### 3.3 端到端集成（`tests/integration/`）
| 测试文件 | 主要覆盖点 |
| --- | --- |
| `test_group_collaboration_flow.py` | 管理员建组 → 学生查看详情 → 创建里程碑/任务 → 更新完成状态。 |
| `test_content_access_flow.py` | 学生与导师对资源/公告/活动的角色可见性矩阵验证。 |

### 3.4 前端单元 & 集成（`tests/frontend/`）
| 测试文件 | 主要覆盖点 |
| --- | --- |
| `vitest.setup.js` | 启用 jsdom、MSW、Mock IntersectionObserver、全局断言。 |
| `mocks/server.js` | 定义默认的认证相关请求拦截器。 |
| `unit/AnimatedContent.spec.ts` | 检查动画初始状态、动画触发与属性变更重播。 |
| `unit/authStore.spec.ts` | Magic Link 请求、OTP 登录、刷新令牌重试逻辑、localStorage 持久化。 |
| `unit/groupsStore.spec.ts` | 小组数据缓存、里程碑/任务新增更新、待完成标记。 |
| `unit/adminStore.spec.ts` | 管理员统计、用户筛选分页、筛选项缓存。 |
| `unit/safeJson.spec.ts` | JSON 解析容错与 204 处理。 |
| `integration/routerGuard.spec.ts` | 登录守卫：未登录跳转、已登录阻止返回登录页。 |

## 4. 环境准备

### 4.1 后端
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> `backend/manage.py` 已自动加入项目根目录到 `sys.path`，确保 `tests` 包可被 Django 发现。

### 4.2 前端
```bash
cd frontend
npm install
```
Vitest 脚本：
- `npm run test`：一次性执行并输出覆盖率到 `tests/frontend/coverage`
- `npm run test:watch`：开发态监听

## 5. 执行顺序建议
1. **一键执行全部测试：**
   ```bash
   chmod +x tests/run-all-tests.sh   # 首次使用需赋权
   ./tests/run-all-tests.sh
   ```
   > 按顺序执行后端单元/API、跨端流程与前端 Vitest 套件，失败即停止。

2. **后端单元/API：**
   ```bash
   cd backend
   python manage.py test tests.backend
   ```
3. **跨端流程/集成：**
   ```bash
   python manage.py test tests.api tests.integration
   ```
4. **前端单元与集成：**
   ```bash
   cd ../frontend
   npm run test
   ```

## 6. 覆盖要点速览
- **认证安全：** 魔法链接、OTP、刷新令牌、缓存清理。
- **后台操作：** 列表筛选、导出、状态更新、权限防护。
- **协作工作流：** 组/里程碑/任务生命周期与角色权限。
- **内容分发：** 资源/公告/活动按角色过滤、上传流程。
- **实时协作：** 聊天分页、附件校验、访问控制。
- **健康监测：** DB/Redis 故障响应、文件上传接口。
- **前端状态：** 认证恢复、缓存策略、筛选项缓存、API 错误处理。
- **前端交互：** 动画组件、路由守卫、工具函数健壮性。

## 7. 常见问题 & 解决
- **数据库/缓存连接失败：** 使用 SQLite + `LocMemCache`，或参考 `test_core_endpoints` 中的异常模拟。
- **MSW 未拦截请求：** 默认基址 `http://127.0.0.1:8000/api`；若 `.env` 设置不同基址，请在测试前 `server.use` 更新。
- **Vitest 报错找不到模块：** 确保从 `frontend/` 执行且依赖已安装；`setupFiles` 指向 `../tests/frontend/vitest.setup.js`，路径调整时需同步修改。

## 8. 后续扩展建议
- 引入 Cypress / Playwright 端到端 UI 测试，覆盖真实浏览器交互与上传。
- 在 CI 中拆分阶段执行：后端 (`manage.py test`) 与前端 (`npm run test`)，并收集覆盖率报告。
- 为聊天、资源上传等高并发场景设计性能基准测试脚本。

---

当前测试体系覆盖平台核心业务流、权限边界与前后端协同。可在现有目录中继续补充新的场景、基类或工具，保持高质量交付。

---

**English version:** see `docs/tests-overview.en.md`.
