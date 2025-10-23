# Workstream1NewFrontend 分工计划

## 1. 目标与总体思路
- 将现有项目在空分支 `Workstream1NewFrontend` 上按模块逐步复原，确保最终结构与主干一致。
- 七人并行开发，保持模块边界清晰，通过独立分支提交合并请求，减少冲突。
- 每个模块负责人既负责重新提交对应代码，也负责最小范围的验证与自查。

## 2. 通用协作约定
1. 本地准备：`git fetch origin && git checkout Workstream1NewFrontend`；确保本地分支与远端空分支同步。
2. 新分支命名：`feature/<name>-<模块>`（如 `feature/gao-auth-admin`），从 `Workstream1NewFrontend` 切出。
3. 从主干提取文件：在个人分支上执行 `git checkout main -- <path>` 或直接拷贝原始文件，确保只引入负责模块。
4. 每次提交前运行该模块相关脚本/测试；提交信息遵循约定格式：`feat(<name>): restore <模块>`。
5. 合并请求（MR/PR）流程：指向 `Workstream1NewFrontend`，至少 1 位同任务段同事 + gao 复核。
6. 合并顺序按照本计划执行，避免依赖缺失；如需跨模块文件，先与负责同学对齐并在 PR 中解释。

## 3. 分工与详细步骤（聚焦 `backend/` 与 `frontend/src/`）

### Gao —— 权限与管理功能
- 一句话概述：负责上传身份认证与权限功能模块 (`backend/authentication`、`backend/users`) 及前端登陆/管理端页面 (`frontend/src/views/Auth*`、`frontend/src/views/admin/**`、`frontend/src/components/admin|auth`)，落地核心业务。
1. 分支：`feature/gao-auth-admin`。
2. 后端：恢复 `backend/authentication/`、`backend/users/`、相关 migrations、权限与验证逻辑（如 `backend/core/permissions.py`），确保认证流程完整。
3. 前端：恢复登陆注册视图、管理员控制台页面与组件（`frontend/src/views/Auth*`、`frontend/src/views/AdminPage.vue`、`frontend/src/views/admin/**`、`frontend/src/components/admin/**`、`frontend/src/components/auth/**`、`frontend/src/services/auth*`、`frontend/src/store/modules/auth*`、`frontend/src/guards/`）。
4. 与 Li 对齐路由/导航占位，确保管理端和登录路由正确挂载。
5. 自测：`python manage.py test authentication users`；前端运行 `npm run build` 并手测登录、角色切换等关键流程。
6. PR 中附带接口契约与示例请求，便于其他模块接入。

### Hugo —— 公告资讯
- 一句话概述：负责上传公告服务 (`backend/announcements`) 及前端公告页面 (`frontend/src/views/Announcements*`、`frontend/src/components/announcements/**`)，保证信息流展示。
1. 分支：`feature/hugo-announcements`。
2. 后端：恢复 `backend/announcements/` 下 models、views、serializers、urls、tests。
3. 前端：恢复公告列表、详情组件以及相关 API 调用封装（例如 `frontend/src/services/announcements*`）。
4. 与 Gao 对齐路由命名、鉴权需求，确保能直接集成。
5. 自测：`python manage.py test announcements`；前端运行 `npm run build` 并手测主要页面。

### Ma —— 小组协作
- 一句话概述：负责上传团队协作模块 (`backend/groups`) 及前端小组页面 (`frontend/src/views/Groups*`、`frontend/src/components/groups/**`)，支持小组管理与概览。
1. 分支：`feature/ma-groups`。
2. 后端：恢复 `backend/groups/` 的 models、views、urls、migrations、tests。
3. 前端：恢复小组列表、详情组件以及调用逻辑（如 `frontend/src/services/groups*`、`frontend/src/hooks/useGroup*`）。
4. 自测：`python manage.py test groups`；前端冒烟验证小组主要流程。

### Li —— 前后端基础框架
- 一句话概述：负责上传核心框架与路由配置 (`backend/btf_backend`、`backend/core`) 以及前端入口骨架 (`frontend/src/main.*`、`frontend/src/router`、`frontend/src/store`)，为其他功能提供运行环境。
1. 分支：`feature/li-core-framework`。
2. 后端：恢复 `backend/btf_backend/` 项目配置与 `backend/core/` 通用工具，确保基础 settings/urls 可正常启动。
3. 前端：恢复 `frontend/src/main.ts|js`、`frontend/src/App.vue`、`frontend/src/router/**`、`frontend/src/store/**`、全局布局与导航组件（如 `frontend/src/components/layout/**`），并预留钩子供 Gao 等同学挂载模块。
4. 自测：`python manage.py check`、`npm install && npm run build`，确认空壳应用可启动且路由占位无报错。

### Wang —— 即时通信
- 一句话概述：负责上传聊天与实时消息模块 (`backend/chat`) 以及前端聊天界面 (`frontend/src/views/Chat*`、`frontend/src/components/chat/**`)，实现会话与消息流。
1. 分支：`feature/wang-chat-realtime`。
2. 后端：恢复 `backend/chat/` 包括 consumers、routing、models、serializers、tests。
3. 前端：恢复聊天视图、消息组件、socket 封装（如 `frontend/src/services/chatSocket*`）。
4. 自测：`python manage.py test chat`；前端本地模拟双端会话验证。

### Guo —— 活动与日程
- 一句话概述：负责上传活动策划模块 (`backend/events`) 及前端日程页面 (`frontend/src/views/Events*`、`frontend/src/views/Schedule*`、`frontend/src/components/events/**`)，保证时间线功能。
1. 分支：`feature/guo-events-schedule`。
2. 后端：恢复 `backend/events/`（包括日程、提醒逻辑、migrations、tests）。
3. 前端：恢复事件/日历视图、组件，以及与事件 API 的交互逻辑（如 `frontend/src/hooks/useSchedule*`）。
4. 自测：`python manage.py test events`；前端运行日历交互冒烟测试。

### Zhu —— 资源与资料库
- 一句话概述：负责上传学习资源模块 (`backend/resources`) 以及前端资料库页面 (`frontend/src/views/Resources*`、`frontend/src/views/Learning*`、`frontend/src/components/resources/**`)，覆盖资料上传与校验。
1. 分支：`feature/zhu-learning-resources`。
2. 后端：恢复 `backend/resources/` 的上传、权限、版本控制逻辑及 tests。
3. 前端：恢复资料库列表、上传表单、校验逻辑，以及相关 hooks（如 `frontend/src/services/resources*`）。
4. 自测：`python manage.py test resources`；前端走查资源上传与下载流程。

## 4. 合并顺序与质量门槛
- 先合并 Li 的框架骨架，再合并 Gao 的认证与管理功能，随后并行处理 Hugo 公告、Ma 小组、Guo 活动、Wang 聊天、Zhu 资源；如遇交叉依赖提前沟通。
- 每个 PR 至少包含：变更说明、影响范围、验证方式、待办事项（如仍缺依赖）。
- 主干回归前，执行一次全量测试：`npm run build`、`pytest`、`python manage.py test`、关键端到端脚本。

## 5. 时间线建议（可根据实际调整）
- Day 0：Li 提交框架骨架并合并。
- Day 1-2：Gao 补全认证与管理端，Hugo 完成公告模块。
- Day 2-4：Ma 小组协作、Wang 聊天实时、Guo 活动日程陆续交付。
- Day 4-5：Zhu 资料库模块补全并与前述模块联调，所有人解决遗留冲突。
- Day 5：Gao 组织最终集成测试，通过后合并回 `Workstream1NewFrontend`，通知团队验证。

## 6. 沟通与风险控制
- 每日同步进度，记录阻塞项；跨模块改动提前在群内沟通。
- 对共享文件（配置、路由、环境变量）启用“预留人”机制：先在协作文档中声明变更窗口，避免 PR 冲突。
- 如遇关键依赖缺失或脚本失败，第一时间在 Issue/群组中登记，并 @Gao 协助决策。
