# BIOTech Futures Hub（new38888）

本仓库目前包含一个使用 Vue 3 + Vite 构建的前端项目，用于演示 BIOTech Futures Hub 的界面与交互流程。以下内容详细说明项目结构、各目录与文件的职责，便于快速理解和继续开发。

## 技术栈与运行方式
- Node.js：推荐使用 `^20.19.0`（`package.json` 中已限定）
- 前端框架：Vue 3、Pinia、Vue Router
- 构建工具：Vite
- 代码质量：ESLint（Vue + Prettier 配置）

启动步骤：
```bash
cd website
npm install
npm run dev
```

## 目录结构总览
```text
new38888/
├── README.md                # 当前文档
├── package-lock.json        # 项目依赖锁定文件（根目录保留）
└── website/                 # 前端应用主体
    ├── README.md            # Vite 模板自带的开发说明
    ├── package.json         # website 子项目依赖与脚本
    ├── package-lock.json
    ├── index.html           # Vite 入口 HTML
    ├── vite.config.js       # Vite 配置（含 @ 路径别名、DevTools 插件）
    ├── eslint.config.js     # ESLint Flat 配置
    ├── jsconfig.json        # 编辑器路径别名支持
    ├── public/
    │   └── favicon.ico      # 应用 favicon
    └── src/                 # Vue 源代码
        ├── main.js          # 应用入口，挂载 Vue、Pinia、路由
        ├── App.vue          # 全局布局（头部、侧边栏、通知面板）
        ├── router/
        │   └── index.js     # 路由表 + 登录状态守卫
        ├── stores/
        │   └── auth.js      # Pinia 登录状态管理与本地存储同步
        ├── data/
        │   └── mock.js      # 站内使用的模拟数据（用户、资源、事件等）
        ├── assets/
        │   ├── styles.css   # 全局样式（品牌色、布局、组件基础样式）
        │   ├── logo.svg
        │   └── btf-logo.png
        └── views/           # 按页面拆分的视图组件
            ├── LoginPage.vue
            ├── DashboardPage.vue
            ├── GroupDetailPage.vue
            ├── ResourcesPage.vue
            ├── EventsPage.vue
            ├── AnnouncementsPage.vue
            ├── ProfilePage.vue
            ├── AdminPage.vue
            └── AboutView.vue
```

## 关键目录与文件说明

### 根目录
- `README.md`：项目总体说明（即本文档）。
- `package-lock.json`：锁定上一次安装的依赖版本，确保不同环境一致。
- `website/`：所有前端源码与构建脚本均位于该子目录。

### website 子项目
- `package.json`：定义依赖（Vue、Pinia、Vue Router 等）与脚本（`dev`、`build`、`lint`、`format`）。
- `vite.config.js`：启用 `@` 别名指向 `src/`，并集成 `vite-plugin-vue-devtools` 方便调试。
- `eslint.config.js`：使用 ESLint Flat 配置，结合 `eslint-plugin-vue` 和 Prettier Skip Formatting。
- `jsconfig.json`：为 IDE 提供路径别名解析能力。
- `index.html`：Vite 入口模板，挂载点为 `#app`。
- `public/favicon.ico`：默认站点图标，可根据品牌替换。
- `README.md`：保留 Vite 官方模板的基础使用说明。

### src 目录
- `main.js`：创建 Vue 应用、注册 Pinia 与路由、加载全局样式，并在启动时从 `localStorage` 恢复登录态。
- `App.vue`：根组件，负责全局布局。包含头部导航、侧边栏菜单、通知面板，以及根据登录状态切换登录页/内页。
- `router/index.js`：声明所有路由（登录、仪表盘、资源、事件、公告、分组详情、个人资料、管理员面板等）并配置登录守卫：未登录访问受限页面会跳转到 `/login`；已登录访问 `/login` 会重定向到 `/dashboard`。
- `stores/auth.js`：Pinia 状态库，提供登录、登出、状态恢复、管理员身份判断和头像缩写等功能，登录数据来源于 `mockUsers`。
- `data/mock.js`：集中管理演示数据，包括：
  - `mockUsers`：示例用户列表（含角色、赛道、状态）
  - `mockGroups`：分组信息
  - `mockResources`：资源列表及类型、适用角色
  - `mockEvents`：活动安排及时间地点
  - `mockAnnouncements`：公告数据（标题、作者、受众、链接等）
- `assets/styles.css`：定义品牌色、字体、布局网格、按钮、卡片、通知等全局样式，供所有页面复用。
- `assets/logo.svg` / `btf-logo.png`：站点使用的品牌图标。

### 视图组件（src/views）
- `LoginPage.vue`：两栏式登录页面，左侧展示活动介绍，右侧为邮箱 + OTP 模拟登录流程（含验证码输入、重新发送按钮等）。
- `DashboardPage.vue`：登录后首页，展示当前用户欢迎语、活跃分组数、事件、公告统计，以及分组卡片和精选资源列表，数据来自 `mock.js`。
- `GroupDetailPage.vue`：小组详情页，左侧 Plan 栏维护阶段任务（支持勾选、添加任务），右侧 Discussion 栏模拟讨论区与消息流。
- `ResourcesPage.vue`：资源库，支持搜索、类别筛选，并为管理员提供上传封面图、移除封面的交互（前端存储为 DataURL）。
- `EventsPage.vue`：活动列表，包含封面管理、详情弹窗、注册链接/按钮等；管理员可上传封面或发起新活动。
- `AnnouncementsPage.vue`：公告列表，支持关键词搜索，标记不同受众范围，支持外链或内部详情跳转。
- `ProfilePage.vue`：个人资料页，显示用户基本信息，可编辑兴趣、联系方式、可用时间，提供保存/取消的前端演示。
- `AdminPage.vue`：管理员仪表盘，展示用户、分组、导师、学生的统计卡片，并提供用户管理表格（搜索、批量选择、导出按钮等示例交互）。
- `AboutView.vue`：示例占位页，目前仅展示一段简单文本，可按需扩展或删除。

## 后续可拓展方向
- 接入真实后端接口替换 `mock.js` 中的模拟数据。
- 将 OTP 登录流程与实际认证服务对接，并完善错误处理与提示。
- 在 `GroupDetailPage`、`AdminPage` 等页面中接入 WebSocket 或 API，实现实时数据更新。
- 按需补充单元测试与端到端测试，保障核心流程的可靠性。
