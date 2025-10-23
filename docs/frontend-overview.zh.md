# BIOTech Futures Hub – 前端文档（中文版）

## 1. 项目概述
本前端项目为 BIOTech Futures Hub 提供完整的用户界面，覆盖登录、仪表盘、团队协作、资源和活动浏览，以及平台级管理员工具。技术栈采用 Vue 3 + Vite，Pinia 负责状态管理，通过 Fetch API 调用后端 REST 接口。

- 核心能力：
  - 与后端一致的免密码登录流程（魔法链接 + 一次性验证码）。
  - 基于角色的导航与仪表盘内容动态展示。
  - 群组工作区：里程碑 / 任务追踪与类即时聊天。
  - 资源、活动、公告栏目，并支持管理员上传/发布。
  - 管理员后台：统计数据、用户 CRUD、CSV 导出、状态审批。
  - GSAP 驱动的页面过渡动画与自定义设计语言（CSS 变量）。

| 模块             | 技术 / 服务                                            |
|------------------|--------------------------------------------------------|
| 框架             | Vue 3（Composition API、`<script setup>`）             |
| 构建工具         | Vite 7                                                 |
| 状态管理         | Pinia 3                                                |
| 路由             | Vue Router 4（Hash History）                           |
| 动画             | GSAP 3 + 自定义 `AnimatedContent` 组件                 |
| 样式系统         | `src/assets/styles.css` 中的设计变量                   |
| API 访问         | Fetch API + JWT Bearer Token                           |
| 开发工具         | ESLint 9、Prettier 3、Vite Vue Devtools 插件           |

## 2. 工具链与运行环境
- **Node 版本要求：** `^20.19.0` 或 `>=22.12.0`（详见 `package.json`）。
- **包管理器：** npm（锁定文件已提交）。
- **常用 npm 脚本：**
  - `npm run dev`：启动 Vite 开发服务器（默认 `http://localhost:5173`，支持热更新）。
  - `npm run build`：构建生产包，输出至 `frontend/dist`。
  - `npm run preview`：本地预览构建结果。
  - `npm run lint`：执行 ESLint 并尝试自动修复。
  - `npm run format`：使用 Prettier 统一 `src/` 下的代码风格。
- **Vite DevTools：** 通过 `vite-plugin-vue-devtools` 自动启用，可在开发环境中检查组件状态。

## 3. 目录结构
```
frontend/
├── index.html                 # Vite 应用入口
├── vite.config.js             # Vite 配置，别名 `@` 指向 `src`
├── src/
│   ├── main.js                # Vue 应用启动入口
│   ├── App.vue                # 根布局、导航与动画包装
│   ├── router/                # Vue Router 配置与登录守卫
│   ├── stores/                # Pinia 仓库（认证、群组、资源、管理员等）
│   ├── views/                 # 路由对应的页面组件
│   ├── components/            # 可复用组件（如 AnimatedContent）
│   ├── assets/                # 全局样式与品牌资源
│   ├── utils/                 # 工具函数（`safeJson`）
│   └── data/mock.js           # 示例数据（旧版/测试用）
├── public/                    # 构建时直接拷贝的静态资源
└── dist/                      # 构建产物（自动生成）
```

## 4. 架构说明
### 4.1 启动流程
`src/main.js` 创建 Vue 应用实例，引入 Pinia 与路由，调用 `auth.hydrate()` 从 `localStorage` 恢复登录态，然后挂载到 `#app`。全局样式 `src/assets/styles.css` 在此导入。

### 4.2 根布局与导航
- `App.vue` 负责渲染顶部导航、侧边栏、通知面板与内容区，所有路由页面都包裹在 `AnimatedContent` 中以播放 GSAP 动画。
- `/login` 路由隐藏全局框架，展示全屏登录界面。
- 侧边栏菜单会根据角色动态显示（管理员才会出现 Admin Panel）。

### 4.3 路由系统
- `src/router/index.js` 基于 `createWebHashHistory()`，便于静态部署时避免后端重写规则。
- 配置的主要路由：
  - `/login` 登录
  - `/dashboard` 仪表盘
  - `/groups`、`/groups/:id`
  - `/resources`、`/resources/:id`
  - `/events`
  - `/announcements`
  - `/profile`
  - `/admin`
  - 其他路径重定向至 `/login`
- 全局守卫：
  - 进入任何页面前都会尝试 `auth.hydrate()`。
  - 未登录用户访问私有路由会被重定向回 `/login`。
  - 已登录用户访问 `/login` 会自动跳转到 `/dashboard`。

### 4.4 Pinia 状态管理
各业务模块拥有独立 Store，负责数据缓存、加载状态和错误提示。当检测到账号切换时会自动清理缓存。

| Store 文件                | 职责与关键方法                                                                                                                   |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| `auth.js`                 | 魔法链接与 OTP 校验、JWT 存储与刷新、`authenticatedFetch` 封装、`localStorage` 会话持久化。                                       |
| `groups.js`               | 拉取我的群组 / 全部群组、缓存详情、里程碑与任务增删改、调用后端 `/groups/...` 下的接口。                                         |
| `chat.js`                 | 按群组管理消息列表、分页加载、消息发送与附件上传（依赖 `/uploads/`）。                                                           |
| `resources.js`            | 列表缓存、管理员上传资源 / 更新封面 / 删除、将后端字段映射为前端字段。                                                            |
| `events.js`               | 获取活动列表、管理员创建/删除/封面上传、报名状态管理。                                                                           |
| `announcements.js`        | 根据用户角色加载公告、管理员发布公告。                                                                                           |
| `admin.js`                | 管理员统计数据、过滤选项、用户 CRUD、状态更新、CSV 导出与详情缓存。                                                              |

所有网络请求都通过 `auth.authenticatedFetch` 注入 `Authorization: Bearer` 头，遇到 401 会自动尝试刷新一次 token。`safeJson` 封装了解析失败时的容错。

### 4.5 API 交互
- 默认 API 地址：`VITE_API_BASE_URL`（未设置时使用 `http://127.0.0.1:8000/api`）。
- 接口路径与后端保持一致（详见 `docs/API.md`），如 `/auth/magic-link/`、`/users/me/`、`/groups/...`、`/admin/users/...` 等。
- Store 层会接收后端返回的 snake_case 字段，并通过映射函数转换为 camelCase。
- 抛出的错误对象由页面捕获后显示给用户。

### 4.6 UI 与动画
- 设计语言集中在 `src/assets/styles.css`，通过 CSS 变量控制配色、阴影、圆角、间距等。
- 图标使用 Font Awesome（需在 `index.html` 全局引入）。
- `AnimatedContent.vue` 基于 Intersection Observer 触发 GSAP 动画，支持横向/纵向、距离、透明度、延迟等自定义参数。

### 4.7 数据生命周期
- Store 统一维护 `loading`、`error`、`listLoaded` 等状态，避免重复请求。
- `auth.setSession` 会在用户切换时调用下游 Store 的 `reset()`，防止跨账号数据混用。
- 页面在 `onMounted` 时调用 `fetch...`，并监听登录状态、用户 ID、角色变化来重新加载。
- Chat Store 合并新旧消息并按 `id` 去重，保证时间顺序从旧到新。

## 5. 页面功能总览

| 页面（`src/views`）        | 功能说明                                                                                                                                      |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `LoginPage.vue`           | 魔法链接登录界面，发送邮件与验证码、六位数 OTP 输入、恢复上次填写的邮箱，校验成功后进入仪表盘。                                              |
| `DashboardPage.vue`       | 仪表盘展示当前用户的群组、资源、活动、公告。管理员可看到全局统计，监听角色/账户变化自动刷新数据。                                           |
| `GroupsPage.vue`          | 列表展示群组；管理员查看全部群组，其他角色仅显示加入的群组。点击行跳转到 `GroupDetailPage`。                                                  |
| `GroupDetailPage.vue`     | 群组工作区：左侧是里程碑与任务（支持新增、删除、勾选），右侧是讨论区（带附件上传）。移动端以 tab 方式切换。                               |
| `ResourcesPage.vue`       | 资源卡片视图，支持按类型/角色筛选。管理员可上传新资源、更新封面、删除。                                                                     |
| `EventsPage.vue`          | 活动列表，展示报名状态，管理员可以创建、删除和更新封面。                                                                                      |
| `AnnouncementsPage.vue`   | 公告列表，自动按用户角色过滤。管理员可新增公告。                                                                                              |
| `ProfilePage.vue`         | 用户资料编辑，提交的数据结构与后端 serializer 保持一致（track + profile 对象）。                                                            |
| `AdminPage.vue`           | 管理员仪表盘：统计卡片、用户管理表格（搜索、过滤、导出、批量操作）、用户创建与编辑、状态更新、删除等完整流程。                              |

## 6. 管理员工作流
- **统计卡片：** `admin.fetchStats` 按 track 拉取总用户数、活跃群组、导师/学生人数及状态。
- **用户管理表格：** 支持搜索、筛选、批量选择、导出、创建、编辑、删除以及状态更新。多个布尔标志（`usersLoading`、`savingUser` 等）驱动按钮禁用与 loading 状态。
- **CSV 导出：** 将返回的 Blob 与 `Content-Disposition` 头解析为文件名，交由前端触发下载。

## 7. 环境配置
- 在项目根目录或 `frontend/` 下创建 `.env.local`，通过 Vite `VITE_*` 变量覆盖配置，例如：
  ```
  VITE_API_BASE_URL=https://api.biotechfutures.org/api
  VITE_WS_BASE_URL=wss://api.biotechfutures.org
  VITE_APP_TITLE=BIOTech Futures Hub
  ```
- 路由使用 Hash 模式，无需后端额外配置即可部署在任意子路径。
- `public/` 下的文件会直接复制到最终构建产物根目录，可用于 favicon 或静态 JSON。
- `VITE_WS_BASE_URL` 可选，用于在 WebSocket 域名与 API 不一致时显式指定；若未设置，前端会基于 `VITE_API_BASE_URL` 自动推断 `ws://`/`wss://` 与 `/ws/chat/...`。
- 部署前请确认后端已配置 CORS 允许前端域名访问。

## 8. 开发流程
1. `cd frontend`
2. `npm install`
3. 根据环境创建 `.env.local`，设置 `VITE_API_BASE_URL` 等变量。
4. `npm run dev` 启动开发服务器，浏览器访问 `http://localhost:5173/`。
5. 搭配 Vue Devtools、Vite DevTools 检查组件状态与路由切换。

### 质量保障
- ESLint（`eslint.config.js`）集成 Vue + Prettier 规则，提交前应修复所有警告。
- Prettier 通过 `npm run format` 格式化 `src/` 目录。
- 目前尚未引入单元测试，后续可考虑结合 Vitest + Vue Test Utils。

## 9. 构建与部署
- `npm run build` 会生成带哈希的静态文件至 `dist/`，可部署到任意静态主机（Nginx、Netlify、Vercel 等）。
- 构建前确保 `VITE_API_BASE_URL` 指向生产后端，否则静态文件仍会请求默认的本地地址。
- 与 Django 后端同部署时，可将 `dist/` 拷贝到后端静态目录，并配置 Django 提供 `index.html`。
- 由于使用 Hash 路由，刷新任意页面都不会产生 404，也无需服务器侧的重写策略。

## 10. 常见问题排查
- **登录后白屏 / 跨域错误：** 检查 `VITE_API_BASE_URL` 是否正确、后端是否允许跨域，并查看浏览器控制台中的 401/403 错误。
- **切换账号后数据未更新：** Store 会在 `auth.setSession` 中清理缓存，如仍异常需确认导入顺序是否导致循环依赖。
- **上传附件失败：** 验证 `/api/uploads/` 是否接受相应文件类型/大小，以及后端对象存储配置是否正确。
- **动画未生效：** `AnimatedContent` 依赖 Intersection Observer，旧浏览器会自动降级为直接播放动画。
- **图标不显示：** 确保在 `index.html` 或全局 CSS 中引入了 Font Awesome 资源。

## 11. 参考资料
- 后端接口文档：`docs/API.md`
- 后端架构说明：`docs/backend-overview.zh.md`
- 英文版前端文档：`docs/frontend-overview.en.md`

_最后更新：2025 年 10 月 24 日_
