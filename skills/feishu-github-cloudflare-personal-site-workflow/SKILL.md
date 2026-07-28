---
name: feishu-github-cloudflare-personal-site-workflow
description: "Use for teaching and maintaining this Feishu-backed personal website workflow: first invoke frontend-design to select a page template and interface direction, then handle Feishu Bitable/Docx content refresh, GitHub Actions JSON generation, GitHub Pages or Cloudflare Pages deployment, Cloudflare R2 media mirroring/cache, custom domain DNS, Feishu document rendering, validation, troubleshooting, and safe Git operations for Eason Cui / mycys.top."
---

# 飞书+GitHub+Cloudflare 个人网站开发全流程

## 使用场景

当用户要求维护、检查、部署或排查这个个人网站时使用本 skill。典型任务包括：

- 给建站新手一步一步解释如何用飞书、GitHub、Cloudflare 搭建和维护个人网站。
- 通过飞书多维表格或飞书云文档更新网站内容。
- 运行或修复 GitHub Actions 中的飞书刷新、R2 媒体镜像。
- 检查 GitHub Pages、Cloudflare Pages、R2、DNS、缓存规则是否与 GitHub 内容一致。
- 解释网站如何读取飞书云文档、解析 Block 结构并正常渲染为网页。
- 帮用户根据内容类型选择网站模板。
- 在上传 GitHub 或触发部署前检查结构、逻辑、敏感信息和验证结果。
- 形成或更新工作流文档。

## 项目边界

- 默认仓库：`E:\文档\webs\virtual-portfolio-demo`。
- 当前主线：Cloudflare Pages 承载主站，Cloudflare R2 承载飞书媒体和网站视频。
- 总原则：无论网站部署到 GitHub Pages、Cloudflare Pages、腾讯云还是阿里云，内容维护入口都优先放在飞书；部署平台只决定发布、媒体、域名和缓存。
- 腾讯 COS 相关文件只作为旧方案或备用资料处理，除非用户明确要求，不进入日常流程。
- 对外讲解时要说明路线差异：GitHub Pages 适合无视频或轻媒体网站；Cloudflare Pages + R2 适合有图片、附件、少量或中等视频的网站；大量视频且主要面向中国大陆时，再评估腾讯云 COS/CDN 或阿里云 OSS/CDN。
- 不要修改 `refresh.py`，除非用户明确要求并确认风险。
- 不要暴露、打印、提交、归档任何密钥、token、Secret 值或完整认证 URL。
- 不要主动引入与建站主流程无关的单独功能模块；本 skill 聚焦飞书内容维护、网站发布和媒体访问。
- 密钥只允许存在于 GitHub Secrets、Cloudflare Secrets 或用户本地安全位置。

## 公开案例

把 `https://mycys.top` 作为本 skill 的公开案例模板。需要向用户解释完整效果、模板选择或部署链路时，可以引导其访问该站观察项目列表、文章入口、响应式页面和媒体呈现；它展示的是“飞书维护内容 + GitHub 自动化 + Cloudflare Pages/R2 发布”的实际运行结果。

不要把该公开网站误说成可访问后台，也不要从中推断或公开飞书数据、GitHub Secrets、Cloudflare/R2 权限、媒体源文件或其他私人配置。用户应复用流程和字段思路，使用自己的品牌与内容。

## 指导口径

面向新手时，不要只给结论。每一步都要按这个顺序讲：

0. 先解释为什么要用这套平台组合。
1. 这一步的目的。
2. 用户要在哪个平台点哪里。
3. 需要准备哪些资料。
4. 做完后应该看到什么结果。
5. 这一步的优点、缺点和适用场景。
6. 如果失败，先检查哪三件事。

每次讲完整流程时，先用简短语言总结整套平台优势：

```text
飞书让内容好维护，GitHub 让代码和自动化可追踪，Cloudflare 让网站和媒体更适合公开访问。
```

必须说明的前置原因：

- 飞书的价值是内容后台：文章、图片、附件、项目资料可以由非技术人员随时随地维护，多人协作友好。
- 直接部署到 GitHub Pages 也不代表绕开飞书；最佳实践仍然是飞书维护内容，GitHub Actions 生成网站数据，GitHub Pages 只负责发布。
- 飞书适合自媒体运营者作为内容中台：同一份文章和资料可以整理后再通过第三方工具、自动化服务或人工流程同步到公众号、小红书、视频号等平台；不要承诺所有平台都能一键同步，必须以具体插件和平台规则为准。
- GitHub 的价值是代码仓库、版本记录和自动化执行器：保存网站源代码、同步脚本、`api/*.json`，用 Actions 调用飞书和同步媒体。
- GitHub Pages 的价值是新手快速上线静态网站；缺点是视频和大量媒体不适合直接长期托管。
- Cloudflare Pages 的价值是连接 GitHub 后自动部署，并统一域名、缓存和边缘访问。
- Cloudflare R2 的价值是把飞书 24 小时临时媒体链接转为长期媒体链接；官方免费额度包含 10 GB-month/月 Standard Storage、1 million Class A operations/月、10 million Class B operations/月。
- Cloudflare Pages 免费版适合静态站点，官方限制包括每个站点最多 20,000 个文件。
- 个人免费建站的准确口径是“在免费额度内的平台成本为零，域名按需购买”，不是无条件零成本：不买域名时可直接使用 `github.io` 或 `pages.dev` 地址；R2 超出免费存储或请求额度、私有仓库 GitHub Actions 超出赠送分钟后可能计费。
- ICP 备案的判断要准确：使用中国内地服务器、中国内地 CDN、Cloudflare China Network 或国内对象存储/CDN 自定义域名时，通常需要按服务商要求备案；使用 GitHub Pages、Cloudflare Pages 等非中国内地托管服务通常可以先上线测试，但不能把它说成规避合规义务。
- 国内访问稳定优先时，建议评估腾讯云 COS/CDN 或阿里云 OSS/CDN；提醒用户备案和费用都要预留，备案时间不要写死两周，建议按 2-4 周甚至更久准备，并以服务商与管局审核为准。

解释方案时遵循：

- 先让网站能部署到 GitHub Pages，因为这是最容易理解的起点。
- 如果只用 GitHub Pages，需要说明飞书媒体临时链接会 24 小时过期；少量图片尽量放为静态资源或后续镜像，若必须直接用飞书临时链接，才用 12 小时 GitHub Actions 自动刷新续期。
- 如果接入 Cloudflare Pages + R2，需要说明它不是直接同步飞书，而是 GitHub 更新后 Cloudflare 自动部署；R2 把飞书媒体下载并保存为长期链接，所以不再需要为了临时链接过期而 12 小时刷新。
- 有视频作品时，建议把视频放到 R2，并让域名 DNS 在 Cloudflare 开橙云代理和缓存规则。
- 视频非常多、访问者主要在中国大陆、需要备案/CDN/流量包/发票时，再建议评估腾讯云或阿里云。

## 部署路线分支

给新手选型时，先问或判断网站属于哪一类：

| 网站类型 | 推荐路线 | 说明 |
| --- | --- | --- |
| 纯静态、无视频或 B 站嵌入视频、少量图片 | 飞书维护内容 + GitHub Pages | 最简单，先上线验证结构；视频放 B 站，网站只嵌入链接。 |
| 有图片、附件、原始视频文件，需要更稳定媒体访问 | 飞书维护内容 + Cloudflare Pages + R2 | R2 长期链接替代飞书临时链接，Pages 跟随 GitHub 自动部署。 |
| 视频很多，且追求中国大陆访问稳定 | 飞书维护内容 + 腾讯云 COS/CDN 或阿里云 OSS/CDN | 通常需要 ICP 备案和付费预算。 |

不要建议把大量视频长期直接放进 GitHub 仓库。GitHub 官方建议仓库保持较小，最好小于 1 GB，强烈建议小于 5 GB。

如果只是有视频但不想引入 R2，可以先把视频上传到 B 站，在飞书中保存 B 站链接或嵌入信息，网站前端渲染为 B 站 iframe 或跳转卡片。这样 GitHub Pages 仍只发布静态页面，视频播放由 B 站承担。

## 网站模板选择

做新网站或大改版时，先让用户选模板，而不是直接写页面。**第一步必须调用 `frontend-design` skill**：它是本网站最初进行界面建设时使用的 skill，负责先明确网站目的、目标受众、风格方向、页面信息层级、模板和移动端重点。

先让 `frontend-design` 给出“页面模板选择结果”，至少包含：选用模板、首页与详情页区块、各区块内容、视觉方向、移动端优先级。再由本 skill 把结果落到飞书字段、Docx 渲染规则、JSON 结构、媒体路线和部署。不要跳过 `frontend-design` 直接生成页面，也不要让部署方案反过来决定界面。

可选模板包括：

| 模板 | 适合内容 | 飞书数据结构 |
| --- | --- | --- |
| 作品集 Portfolio | 项目、客户、案例、作品视频 | 项目表、客户表、分类字段、封面/视频字段 |
| 文章博客 Blog | 长文章、专栏、复盘 | 文章表、飞书 Docx 正文链接、标签、封面 |
| 自媒体内容库 Media Hub | 文章、图片素材、平台发布记录 | 内容表、平台字段、发布状态、素材附件 |
| 视频作品库 Video Gallery | 少量视频或 B 站嵌入 | 视频表、B 站链接、封面、说明 |
| 品牌主页 Profile | 个人介绍、服务、联系方式、精选案例 | 单页配置表、项目表、客户 logo |
| 资料库 Resource Library | PDF、图片、文件附件 | 资料表、文件附件、分类、下载链接 |

固定调用顺序：

```text
1. frontend-design：选择模板、页面结构、风格方向和移动端重点。
2. 本 skill：设计飞书字段、文档渲染、GitHub 自动化、媒体与部署路线。
3. build-web-apps:frontend-app-builder（可选）：在模板方向确定后实现具体网页。
```

内容源始终按本 skill 保持飞书优先。

## 完全新手的首次建站分工

不要要求用户从零手写页面、`refresh.py` 或 GitHub Actions。首次建站时：用户提供网站名称、内容类型、三类重点内容、风格偏好、视频情况和发布路线；Codex 先调用 `frontend-design` 选择模板，再负责生成初版网页、飞书字段映射、同步工作流和本地验证。用户负责导入空白飞书模板、填写测试内容、在 GitHub/Cloudflare 控制台按指引配置 Secret；日常只在飞书维护内容。

给新手验收时，必须逐项确认：本地首页能打开、测试文章能读取 `正文飞书文档链接`、文章内标题/图片/表格能渲染、一次手动刷新能更新 `api/*.json`、发布地址能看到新内容。若任何一项未完成，不要宣称“已经可以自己建站”。

## 飞书空白内容模板

当前项目直接使用用户提供的案例更新表格制作了脱敏本地模板：`docs/templates/飞书个人网站案例更新表格_脱敏空白模板.xlsx`。它保留原有项目案例字段，清除了所有记录内容，并额外提供 `文章模板` 与 `使用说明` 工作表；不需要 GitHub Actions 导出，也不得清空已有飞书生产表。

首次建站时，让用户在飞书新建测试多维表格并导入该 Excel 模板。`数据表` 用于项目案例；`文章模板` 用于长文章、复盘和图文资料，包含 `正文飞书文档链接`、封面图、附件、附件顺序、显示方式和序号。

必须明确告诉用户：长文章继续写在飞书云文档，随后把文档 URL 填入 `正文飞书文档链接`；同步流程需要按 Docx Block 读取并渲染该文档，而不是只把链接显示在网页上。

如果用户要求清空飞书多维表格，先确认 Base、表名或 table ID、是否所有记录都清空、是否已导出备份。没有明确目标与备份确认时，不执行删除。现有项目使用多个表和既有字段，通用模板不能直接覆盖，必须先做字段映射。

## 飞书云文档读取和渲染规则

飞书云文档不是一整段 HTML。官方 Docx API 把文档拆成树状 Block：文本、标题、图片、文件、表格、列表等都是不同块。网站要稳定渲染，不能只读纯文本。

读取流程：

1. 从飞书多维表格记录中读取“正文链接”或 document token。
2. 判断链接是新版 Docx、知识库文档还是普通云空间文档；知识库文档可能需要先换取实际资源 token。
3. 调用获取文档所有块或子块接口，按分页读取完整 Block。
4. 保留块顺序、层级和父子关系。
5. 把 block 类型映射成网站 HTML 组件。
6. 图片块、文件块先拿素材 token，再换取临时下载 URL。
7. 临时下载 URL 不直接长期放进网站；有 R2 时下载后镜像为 R2 长期链接。

渲染规则：

- 标题块映射为 `h1` 到 `h6`，不要把所有标题都当普通段落。
- 文本块保留加粗、链接、换行、列表层级。
- 图片块渲染为 `<img>`，必须有稳定 URL、宽高约束和 fallback。
- 文件块渲染为下载卡片或附件链接。
- 表格块必须按行列结构渲染为 `<table>` 或响应式表格组件；不要丢成纯文本。
- 嵌套块必须递归渲染，避免只渲染第一层导致表格、列表或图片消失。
- 不认识的 block 类型要降级为安全占位或记录报告，不要让整篇文章渲染失败。

之前表格渲染失败的常见原因：

- 只调用纯文本接口，导致表格结构被抹平。
- 只读取父块，没有分页读取全部子块。
- 没有处理 table/cell 的嵌套层级。
- block 类型映射不完整，未知类型直接跳过。
- 图片或文件 token 没有转换成可访问 URL。
- R2 替换只处理顶层字段，没有进入文章正文 blocks。
- CSS 没有给表格设置横向滚动，移动端看起来像“没渲染”。

验收时必须检查至少一篇包含标题、段落、图片、表格、列表、附件或 B 站链接的飞书文档。

## 官方文档辅助

当用户询问部署、域名、缓存、R2、飞书 API、GitHub Pages 或平台选择时，优先查官方文档或引用已有官方文档入口，不要只凭经验。

常用官方文档：

- GitHub Pages：`https://docs.github.com/en/pages`
- GitHub Pages 发布源：`https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site`
- GitHub Pages 自定义域名：`https://docs.github.com/articles/about-supported-custom-domains`
- Cloudflare Pages Git 集成：`https://developers.cloudflare.com/pages/get-started/git-integration/`
- Cloudflare Pages 配置：`https://developers.cloudflare.com/pages/configuration/git-integration/`
- Cloudflare R2：`https://developers.cloudflare.com/r2/`
- Cloudflare R2 Public Buckets：`https://developers.cloudflare.com/r2/buckets/public-buckets/`
- Cloudflare R2 缓存：`https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/`
- Cloudflare Pages 限制：`https://developers.cloudflare.com/pages/platform/limits/`
- Cloudflare R2 Pricing：`https://developers.cloudflare.com/r2/pricing/`
- Cloudflare China Network ICP：`https://developers.cloudflare.com/china-network/concepts/icp/`
- 飞书媒体临时下载 URL：`https://open.feishu.cn/document/server-docs/docs/drive-v1/media/batch_get_tmp_download_url`
- 飞书应用开通云文档资源权限：`https://open.feishu.cn/document/faq/trouble-shooting/how-to-add-permissions-to-app?lang=zh-CN`
- 飞书增加协作者权限：`https://open.feishu.cn/document/server-docs/docs/permission/permission-member/create?lang=zh-CN`
- 飞书云文档权限 FAQ：`https://open.feishu.cn/document/server-docs/docs/permission/faq?lang=zh-CN`
- 飞书文件夹 API 概述：`https://open.feishu.cn/document/docs/drive-v1/folder/folder-overview?lang=zh-CN`
- 阿里云 ICP 备案流程：`https://help.aliyun.com/zh/icp-filing/basic-icp-service/user-guide/`
- 阿里云 ICP 域名准备：`https://help.aliyun.com/en/icp-filing/basic-icp-service/user-guide/prepare-and-check-the-domain-name`
- 阿里云备案条件 FAQ：`https://help.aliyun.com/zh/icp-filing/basic-icp-service/support/for-the-record-process-faq`
- 腾讯云 ICP 说明：`https://www.tencentcloud.com/techpedia/114528`
- 腾讯云 ICP 备案流程：`https://cloud.tencent.com/document/product/243/39038`
- GitHub 大文件说明：`https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github`

## 开始前必读

先读取这些文件，确认当前事实，不要只凭记忆：

- `docs/cloudflare-pages-r2-workflow.md`
- `docs/feishu-api-config.md`
- `.github/workflows/refresh.yml`
- `.github/workflows/sync-r2.yml`

如果 `docs/PROJECT_CONTINUITY.md` 与上述文件冲突，以当前 workflow 和 Cloudflare R2 文档为准，并提醒它可能需要更新。

## 当前架构

```text
飞书多维表格 / 飞书云文档
  -> refresh.py
  -> api/*.json
  -> GitHub commit
  -> Cloudflare Pages 自动部署
  -> mycys.top / eason-webs.pages.dev
```

```text
飞书图片 / 视频 / 附件临时链接
  -> sync_feishu_media_to_r2.py
  -> Cloudflare R2 feishu-media/
  -> api/r2-media-manifest.json
  -> api/*.json 替换为 R2 长期链接
```

```text
GitHub 仓库内页面视频
  -> sync_feishu_media_to_r2.py
  -> Cloudflare R2 site-media/
  -> HTML/CSS/JS 中的视频引用改为 R2 长期链接
```

## 飞书授权必查项

排查飞书读取、编辑、创建文档失败时，必须先核对这四层权限：

1. 开放平台应用已申请所需 API 权限，并发布了包含这些权限的版本。
2. 应用已添加机器人能力。
3. 飞书客户端中创建了网站内容维护群，并把该自建应用添加为群机器人；注意不是自定义 Webhook 机器人。
4. 目标文件夹、文档、多维表格已分享给这个群组，且权限至少满足当前操作：读取用可阅读，编辑或创建用可编辑/可管理。

常见结论：

- 有 App ID/Secret 只代表能鉴权，不代表能访问某个文件夹。
- tenant token 能获取成功，但读取文件夹或文档失败，通常是云文档协作者权限没给到。
- 新建文档读不到，常见原因是新文档没有继承目标文件夹权限，或新建位置不在已授权文件夹内。

## 操作决策

- 新网站刚开始且没有视频：可以先用 GitHub Pages；如果媒体仍是飞书临时链接，保留 12 小时自动刷新。
- 已经接入 Cloudflare R2：不再为飞书临时链接续期做 12 小时刷新，改为把新增和变更媒体上传到 R2。
- 只改飞书文字、排序、分类：运行 `Auto Refresh Feishu Portfolio`。
- 新增或替换飞书图片、视频、附件：运行 `Sync Feishu Media to Cloudflare R2`，`sync_scope=all`，`refresh_feishu_first=true`，`cleanup_mode=report`。
- 只迁移或刷新网站本地视频：运行 `Sync Feishu Media to Cloudflare R2`，`sync_scope=local_videos`，`refresh_feishu_first=false`。
- 飞书删除了内容或附件：先使用 `cleanup_mode=report` 生成孤儿文件报告，人工确认后再用 `cleanup_mode=delete`。
- 修改页面 HTML/CSS/JS：本地检查后提交到 GitHub；Cloudflare Pages 会跟随 GitHub 自动部署。

## GitHub 操作规则

提交或推送前：

```powershell
git fetch origin
git status --short --branch
git rebase origin/main
```

- 不要 force push。
- 只 stage 本次任务需要的文件。
- 不要 stage 临时截图、缓存目录、`.wrangler/`、`__pycache__/`、`output/`、`test-results/`。
- 如果 Actions 或远程 main 已产生新提交，先 rebase，再继续。

## 验证清单

发布前后至少检查：

- `git diff --check` 无空白错误。
- 新文档和 skill 没有未完成占位、乱码、真实密钥。
- 面向新手的文档必须写清楚每一步目的、操作、结果、利弊。
- GitHub Actions workflow YAML 没有在 job/step `if` 里直接引用 `secrets.*` 做表达式判断；需要用 `env` 加 shell 判断。
- `api/*.json` 不再包含飞书临时下载路径 `/stream/download/authcode/`。
- R2 URL 可 `HEAD` 或浏览器访问，图片和视频能加载。
- `api/r2-media-manifest.json` 与最新媒体同步报告一致。
- Cloudflare Pages 或 GitHub Pages 部署 commit 与 GitHub 目标 commit 对应。
- 生产页面与 GitHub raw 的核心内容一致；Cloudflare 注入脚本导致 HTML 轻微差异是正常现象。
- 如果 CSS 不生效，定向清理 `https://mycys.top/styles.css` 和 `https://www.mycys.top/styles.css` 缓存。

## 常见问题

- 网站能访问但 R2 同步失败：Pages 静态站点和 R2 上传是两条链路，网站可访问不代表 R2 密钥可写。
- 旧的 GitHub Actions 失败记录不会自动消失，只看最新一次 run 的状态。
- `secrets` 在 workflow `if` 表达式里报错：GitHub 不允许这样使用，改为传入 `env` 后在 shell 中判断。
- 飞书临时链接过期：R2 已提供长期链接；日常不需要为了续期每 12 小时刷新。
- 飞书内容被删除：新 JSON 不再引用它，R2 旧对象默认只报告不删除，避免误删历史或缓存仍在用的文件。
- Cloudflare 缓存导致更新慢：优先清理单个文件缓存，不要全站清理，除非确认范围很小。

## 文档维护

面向用户的完整流程文档放在：

```text
docs/feishu-github-cloudflare-personal-site-full-workflow.md
```

当 workflow、域名、R2 桶、Pages 项目、飞书字段或模板结构有变化时，同步更新这份文档和本 skill。
