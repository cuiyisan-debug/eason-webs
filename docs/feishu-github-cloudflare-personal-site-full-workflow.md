# 飞书+GitHub+Cloudflare 个人网站开发全流程

这份文档给完全不熟悉建站的人使用。它不是一次性把所有平台都配置完，而是按阶段推进：先把网站跑起来，再解决飞书链接过期，再解决视频加载，再考虑大量视频时是否换到腾讯云或阿里云。

核心思路：

```text
飞书负责维护内容
GitHub 负责保存网站代码和自动刷新数据
Cloudflare Pages 负责发布网站
Cloudflare R2 负责把飞书图片、附件、视频变成长期链接
```

总原则：

```text
无论网站最终部署到 GitHub Pages、Cloudflare Pages、腾讯云还是阿里云，内容维护入口都优先放在飞书。
```

部署平台只决定“网站在哪里发布、媒体在哪里加速、域名在哪里解析”；飞书决定“谁来更新内容、怎么更新文章和资料、怎么多人协作维护”。

## 公开案例模板：mycys.top

这份工作流的公开运行案例是 [mycys.top](https://mycys.top)。任何人都可以打开它，查看“飞书维护内容 + GitHub 保存代码与自动化 + Cloudflare Pages/R2 发布媒体”的实际网站效果。

把它当作案例模板时，重点观察：

- 首页项目分类、作品卡片、客户信息和文章入口如何由飞书内容组织。
- 项目图片、附件、视频和文章正文如何在网站上长期访问。
- 手机与桌面端如何使用同一份飞书内容结构渲染。

公开案例只用于理解网站结构和体验，不提供飞书后台、GitHub Secrets、Cloudflare 密钥、R2 管理权限或原始内容数据。新网站应复制流程和字段思路，替换成自己的品牌、内容和媒体。

## 0. 前置理解：为什么套用这套平台

这套方案不是为了炫技，而是把“内容维护、代码保存、网站发布、媒体加速、备案压力”拆开处理。对个人网站和自媒体型网站来说，这样更容易长期维护。

### 0.1 为什么不用传统后台

传统网站后台需要服务器、数据库、登录系统、编辑器、上传接口、权限管理。对个人网站来说，这些东西很容易变成维护负担。

这套方案把后台替换成飞书：

- 飞书多维表格负责结构化内容，例如作品、客户、分类、排序、封面。
- 飞书云文档负责长文章、项目复盘、图文资料。
- GitHub Actions 定期或手动读取飞书，把内容生成成静态网站可用的 JSON。
- 前端页面只读 `api/*.json`，不需要自己做数据库和后台登录。

优点：

- 网站维护者不需要懂代码，也能更新内容。
- 多个人可以随时随地在飞书里协作维护。
- 飞书文档天然适合整理文章、图片、附件、运营素材。
- 自媒体运营者可以把飞书当作内容中台，后续再通过第三方工具、自动化服务或人工流程，把同一份内容分发到公众号、小红书、视频号等平台。

限制：

- 第三方平台同步能力取决于具体插件、工具和平台接口规则，不能默认所有平台都能一键同步。
- 飞书只是内容源，不直接承担高性能网站访问。
- 飞书附件临时链接会过期，所以媒体需要后续处理。

### 0.2 为什么用 GitHub

GitHub 在这套架构里不是“内容后台”，而是“代码仓库 + 自动化执行器 + 版本记录”。

它负责：

- 保存网站源代码。
- 保存同步脚本。
- 保存从飞书生成的 `api/*.json`。
- 用 GitHub Actions 自动执行飞书刷新、媒体同步、提交更新。
- 在最简单阶段，用 GitHub Pages 直接发布网站。

为什么适合新手：

- 不需要先买服务器。
- 每次改动都有记录，错了可以回退。
- GitHub Pages 可以直接托管静态网站。
- GitHub Actions 可以把“手工导出飞书数据”变成自动流程。
- 即使网站直接部署到 GitHub Pages，也建议内容仍然从飞书维护，再由 GitHub Actions 生成网站数据。

限制：

- GitHub Pages 更适合静态页面和少量媒体。
- 大视频、大量媒体不适合长期直接放 GitHub Pages。
- GitHub Actions 有运行时间、频率和失败风险，不能把它当成实时后端服务。

### 0.3 为什么用 Cloudflare

Cloudflare 在这套架构里负责“发布、DNS、缓存、边缘网络、媒体长期链接”。

它负责：

- Cloudflare Pages 连接 GitHub，自动部署网站。
- Cloudflare R2 保存飞书媒体和网站视频。
- Cloudflare DNS 管理域名解析。
- 橙云代理和缓存规则提升静态资源、图片、视频加载体验。

为什么能减少飞书 12 小时刷新：

- 只用 GitHub Pages 时，网站可能直接引用飞书临时媒体链接，需要每 12 小时刷新一次，赶在 24 小时过期前更新链接。
- 接入 R2 后，飞书临时链接只用于“下载原始媒体”。
- 下载后媒体保存在 R2，网站访问 R2 长期链接。
- 所以不再需要为了飞书临时链接续期而频繁刷新。

限制：

- Cloudflare 不是中国大陆备案接入服务商的普通替代品。
- 使用 Cloudflare 全球网络、GitHub Pages、Cloudflare Pages 这类非中国内地主机时，通常不会触发“中国内地服务器开办网站”的 ICP 备案前置要求。
- 如果接入中国内地服务器、中国内地 CDN、Cloudflare China Network、腾讯云 CDN 或阿里云 CDN，就要按接入服务要求准备 ICP 备案。
- 中国大陆访问速度受网络环境影响，不保证一定比国内 CDN 快。

### 0.4 为什么关注 ICP 备案

ICP 备案主要和“网站是否托管在中国内地服务器或接入中国内地 CDN/服务”有关。

对个人网站来说：

- 域名在腾讯云或阿里云注册，不等于必须马上备案。
- 如果网站解析到 GitHub Pages、Cloudflare Pages 这类非中国内地托管服务，通常可以先上线测试。
- 如果以后要接入腾讯云 COS/CDN、阿里云 OSS/CDN 的中国大陆节点，或使用中国内地服务器，就需要备案。

这也是为什么新手阶段推荐：

```text
先 GitHub Pages / Cloudflare Pages 上线
再根据视频量、访问地区、备案进度决定是否转国内云 CDN
```

### 0.5 个人免费建站的费用边界

不使用腾讯云或阿里云的中国内地部署时，个人可以先按“**平台成本为零，域名按需购买**”的方式建站：

| 项目 | 是否必须付费 | 新手建议 |
| --- | --- | --- |
| GitHub 账号、代码仓库、GitHub Pages | 否 | 先用免费的 `用户名.github.io` 地址测试网站。 |
| Cloudflare 账号、Pages、DNS | 否 | 静态网站在免费方案内可发布；Pages 免费方案有文件数量和构建次数等限制。 |
| Cloudflare R2 | 否，但有免费额度上限 | 图片、附件、少量视频可先用免费额度；超额存储或请求会计费。 |
| 自定义域名，例如 `myname.com` | 否 | 不买域名也能上线；想用自己的网址时，域名年费通常是最常见的固定支出。 |
| 腾讯云 / 阿里云中国内地对象存储、CDN、服务器 | 是 | 适合更重的视频和中国大陆稳定访问，需要预算与备案准备。 |

因此，“只需要域名费用”应理解为：**在 GitHub / Cloudflare 免费额度内、没有启用付费产品、且 GitHub Actions 用量未超额时，自定义域名是最可能发生的唯一固定费用。** 不买域名时，可以一直使用 GitHub Pages 或 Cloudflare Pages 分配的免费地址。

要特别留意两件事：

- Cloudflare R2 免费额度目前是每月 10 GB-month Standard Storage、100 万次 Class A 请求、1000 万次 Class B 请求；超过后按量计费，媒体访问量很大时不能忽略。
- 公共仓库使用标准 GitHub-hosted runner 的 GitHub Actions 免费；私有仓库有每月赠送分钟和存储额度，超过后可能计费。不要为“看起来免费”而无限频率运行工作流。

这些免费路线通常不需要因为购买域名本身而办理 ICP 备案；是否需要备案仍由实际接入的中国内地服务器、CDN 或对象存储服务决定。

### 0.5 这套平台的整体优势

一句话总结：

```text
飞书让内容好维护，GitHub 让代码和自动化可追踪，Cloudflare 让网站和媒体更适合公开访问。
```

具体优势：

- 维护成本低：改网站内容像改飞书表格和文档。
- 协作友好：多人可以用飞书共同维护内容。
- 适合自媒体：飞书可以作为文章、资料、图片的内容中台，再对接其他内容分发工具。
- 不依赖传统后端：静态站点加 JSON，减少服务器维护。
- 可逐步升级：先 GitHub Pages，后 Cloudflare Pages，再 R2，再按视频量评估国内云。
- 链接更稳定：R2 解决飞书媒体 24 小时过期。
- 部署可追踪：GitHub commit 和 Actions run 都能回看。
- 密钥更安全：密钥集中放 GitHub Secrets 和 Cloudflare Secrets，不进入前端。

## 1. 先理解为什么这样做

### 为什么用飞书

飞书适合做个人网站的内容后台，因为它对非技术用户友好：

- 文章、项目、客户、图片、附件可以在表格或云文档里直接维护。
- 不需要每次改文章都打开代码编辑器。
- 多维表格适合做“作品库”“文章库”“客户库”这种结构化内容。
- 飞书云文档适合写长文章、图文说明、项目复盘。

缺点也很明确：

- 飞书附件和文档图片通过 API 拿到的下载链接通常是临时链接。
- 飞书官方媒体临时下载 URL 有效期为 24 小时。
- 所以只把飞书临时链接直接放到网站里，过一段时间图片和视频就可能失效。

### 为什么用 GitHub

GitHub 适合做网站的代码仓库和自动化中心：

- 保存 HTML、CSS、JS、同步脚本和 `api/*.json`。
- 每次修改都有历史记录，方便回退。
- GitHub Actions 可以定时或手动运行 `refresh.py`，从飞书重新生成网站数据。
- GitHub Pages 可以直接发布静态网站。

缺点：

- GitHub Pages 更适合轻量静态网站。
- 如果网站有大量视频，直接从 GitHub Pages 加载体验通常不理想。
- GitHub 不是专门的视频或媒体分发平台。

### 为什么接 Cloudflare

Cloudflare 主要解决两个问题：

- Cloudflare Pages 可以连接 GitHub，GitHub 一推送，Cloudflare 自动部署。
- Cloudflare R2 可以保存图片、视频、附件，生成长期可访问链接，避免飞书 24 小时临时链接问题。

如果域名 DNS 托管在 Cloudflare，并开启橙云代理，网站流量会经过 Cloudflare 边缘网络。对静态资源和视频首段加载通常会更友好，尤其比直接从 GitHub Pages 拉大视频更适合。

缺点：

- 多一个平台，需要配置 R2 Bucket、API Token、DNS、缓存规则。
- R2 的 `r2.dev` 公共地址更适合开发测试；正式长期使用建议绑定自己的媒体域名。
- 如果视频非常多、体量很大、主要访问人群在中国大陆，腾讯云 COS/CDN 或阿里云 OSS/CDN 可能更合适。
- 如果使用中国内地 CDN、对象存储自定义域名或内地服务器，需要按服务商要求完成 ICP 备案。

## 2. 三种部署路线怎么选

### 路线 A：飞书维护内容 + GitHub Pages

适合：

- 纯静态网站。
- 没有视频，或只有 B 站、视频号等第三方平台嵌入视频。
- 只有少量图片。
- 希望最快上线，少配置平台。

工作方式：

```text
飞书维护内容
  -> GitHub Actions 生成 api/*.json
  -> GitHub Pages 发布网站
```

如果网站里有视频，优先把视频上传到 B 站等视频平台，再在飞书中保存 B 站链接或嵌入信息。网站前端渲染为 iframe 或视频卡片。这样 GitHub Pages 仍只发布静态页面，视频播放由 B 站承担。

如果少量图片来自飞书附件临时链接，需要知道它仍然会过期。更稳妥的做法是把少量固定图片放进仓库静态资源，或后续镜像到 R2；如果暂时直接使用飞书临时链接，再用 GitHub Actions 做 12 小时刷新续期。

优点：

- 简单，平台少。
- 适合建站初期。
- 成本低。
- 适合先验证网站结构、页面设计、内容分类。
- 视频嵌入第三方平台，不占 GitHub 仓库和 Pages 资源。

缺点：

- 需要接受 B 站播放器样式、平台水印或跳转逻辑。
- 不适合大量自托管图片、附件、原始视频文件。
- 仓库不应长期堆大文件。GitHub 官方建议仓库保持较小，最好小于 1 GB，强烈建议小于 5 GB。

### 路线 B：飞书维护内容 + Cloudflare Pages + R2

适合：

- 有图片、附件、作品视频等媒体文件。
- 希望解决飞书 24 小时临时链接失效。
- 希望用 Cloudflare R2 保存长期媒体链接。
- 希望 Cloudflare Pages 跟随 GitHub 自动部署。
- 希望静态资源和视频通过 Cloudflare 缓存提升访问体验。

工作方式：

```text
飞书更新
  -> GitHub Actions 刷新飞书数据
  -> GitHub Actions 把新增/变更媒体上传到 R2
  -> api/*.json 替换成 R2 长期链接
  -> GitHub 保存更新
  -> Cloudflare Pages 自动部署
```

优点：

- 飞书继续作为内容后台，维护方便。
- R2 长期链接解决飞书 24 小时过期问题。
- Cloudflare Pages 自动跟随 GitHub。
- 视频、图片、CSS、JS 可以用 Cloudflare 缓存规则提速。
- Cloudflare R2 官方免费额度包含 10 GB-month/月 Standard Storage、1 million Class A operations/月、10 million Class B operations/月。
- Cloudflare Pages 免费版可承载静态站点，官方当前限制包括每个站点最多 20,000 个文件。

缺点：

- 首次配置比 GitHub Pages 复杂。
- 要管理 R2 API 权限和 GitHub Secrets。
- 如果视频非常多，仍然要评估专业 CDN 和存储成本。

### 路线 C：飞书维护内容 + 腾讯云 COS/CDN 或阿里云 OSS/CDN

适合：

- 视频很多。
- 主要访问者在中国大陆。
- 已经有 ICP 备案或准备接入大陆 CDN。
- 需要国内云厂商发票、备案、CDN、对象存储一套管理。

优点：

- 更适合大量视频和大陆访问场景。
- 腾讯云和阿里云对 ICP 备案、对象存储、CDN、日志、账单支持更完整。
- 国内访问稳定性和可控性通常更好。

缺点：

- 备案、权限、CDN、缓存、防盗链配置更复杂。
- 费用结构需要单独评估。
- 当前项目主线已经转向 Cloudflare，腾讯 COS 文档只作为备用。
- ICP 备案不要只按“两周”卡时间。建议预留 2-4 周甚至更久；腾讯云英文说明中提到流程通常可能需要 20-30 个工作日，具体取决于实名、资料、初审和管局审核。

## 3. 新手推荐路线

按这个顺序走：

```text
第一阶段：飞书维护内容，GitHub Pages 先上线
第二阶段：如果有视频，优先嵌入 B 站链接
第三阶段：如果有图片、附件、原始视频文件，接 Cloudflare Pages + R2
第四阶段：如果追求中国大陆访问稳定或视频很多，再评估腾讯云或阿里云
```

不要一开始就把所有平台都做满。先让网站能访问，再逐步解决问题。

简单判断：

| 网站类型 | 推荐路线 |
| --- | --- |
| 纯静态、无视频、少量图片 | 飞书维护内容 + GitHub Pages |
| 纯静态、有视频但可用 B 站嵌入 | 飞书维护内容 + GitHub Pages + B 站链接 |
| 有图片、附件、原始视频文件，想解决飞书链接过期 | 飞书维护内容 + Cloudflare Pages + R2 |
| 视频很多，且追求中国大陆访问稳定 | 飞书维护内容 + 腾讯云 COS/CDN 或阿里云 OSS/CDN，先准备 ICP 备案和费用预算 |

### 网站模板先行：先调用 `frontend-design`

做新网站或大改版时，不要一上来就写页面。**第一步必须调用 `frontend-design` skill**：这是本网站最初进行界面建设时使用的前端设计 skill。它先帮助确定网站目的、目标受众、整体风格方向、页面信息层级和模板，再开始写代码。

`frontend-design` 的输出不是最终网页代码，而是一份可落地的“页面模板选择结果”：选哪一种模板、首页和详情页有哪些区块、每个区块展示什么内容、视觉风格是什么、移动端优先级是什么。随后再由本工作流把这些区块翻译成飞书表格字段、飞书 Docx 正文结构、JSON 数据和部署方案。模板决定飞书表格要有哪些字段，也决定前端怎么渲染。

| 模板 | 适合内容 | 飞书数据结构 |
| --- | --- | --- |
| 作品集 Portfolio | 项目、客户、案例、作品视频 | 项目表、客户表、分类字段、封面/视频字段 |
| 文章博客 Blog | 长文章、专栏、复盘 | 文章表、飞书 Docx 正文链接、标签、封面 |
| 自媒体内容库 Media Hub | 文章、图片素材、平台发布记录 | 内容表、平台字段、发布状态、素材附件 |
| 视频作品库 Video Gallery | 少量视频或 B 站嵌入 | 视频表、B 站链接、封面、说明 |
| 品牌主页 Profile | 个人介绍、服务、联系方式、精选案例 | 单页配置表、项目表、客户 logo |
| 资料库 Resource Library | PDF、图片、文件附件 | 资料表、文件附件、分类、下载链接 |

调用顺序固定为：

```text
1. frontend-design：选择模板、页面结构、风格方向和移动端重点
2. 本工作流：设计飞书字段、文档渲染、GitHub 自动化、媒体与部署路线
3. build-web-apps:frontend-app-builder（可选）：在已有模板方向后实现具体网页
```

不要跳过第 1 步直接让代码生成页面，也不要反过来让部署方案决定界面。无论选哪种模板，内容源仍然优先使用飞书。

### 完全新手从零开始：你做什么，Codex 做什么

这份流程的目标不是让不会写代码的人手动编写同步脚本，而是让你能在飞书维护网站。第一次建站按下面分工推进：

| 阶段 | 你只需要完成 | Codex / 开发者负责完成 | 做完的标志 |
| --- | --- | --- | --- |
| 选模板 | 说清网站名称、主要内容、喜欢的感觉、是否有视频 | 调用 `frontend-design`，确定模板、页面区块和移动端重点 | 有一份页面结构与风格方案。 |
| 建初版网站 | 确认方案 | 创建 HTML/CSS/JS、响应式页面、`api/*.json` 数据接口和必要字段映射 | 本地能打开首页和一篇文章详情页。 |
| 建飞书内容库 | 导入空白模板，填一条测试内容和一篇测试文档 | 核对字段名、表 ID、Docx Block 渲染规则 | 测试标题、正文和表格能读到。 |
| 配置自动化 | 在 GitHub/Cloudflare 页面按提示填写 Secret，不把值发到聊天 | 创建或检查 GitHub Actions、R2 同步逻辑与部署设置 | 手动运行一次后 `api/*.json` 更新。 |
| 日常维护 | 只改飞书表格、飞书文档和附件 | 仅在模板、字段或功能变化时改代码 | 网站随刷新或部署更新。 |

第一次向 Codex 提需求时，可以直接复制下面这段，不需要懂技术术语：

```text
我要建一个个人网站。
网站名称：______
内容类型：作品集 / 文章博客 / 自媒体内容库 / 视频作品库 / 品牌主页 / 资料库
我最想展示的三类内容：______、______、______
视觉感觉：极简 / 编辑感 / 明亮 / 深色 / 其他：______
视频情况：没有 / 用 B 站链接 / 有原始视频文件
发布路线：先用 GitHub Pages / 用 Cloudflare Pages + R2 / 以后考虑国内云
请先调用 frontend-design 帮我选页面模板，再告诉我需要在飞书建立哪些字段。
```

因此，完全新手可以按照文档完成建站，但前提是第一版代码、字段映射和工作流由 Codex 或开发者生成；之后的日常更新不需要再写代码。

## 4. 第一步：准备飞书内容

目标：把飞书变成网站后台。

你需要准备：

- 一个飞书多维表格，保存项目、文章、客户、分类、排序等信息。
- 如有长文章，准备飞书云文档链接。
- 如有图片、附件、视频，放在对应记录字段或文档内容里。
- 一个飞书自建应用，用来让 GitHub Actions 读取数据。

### 4.0 使用脱敏后的飞书空白模板

不要删除飞书记录来做模板。当前项目已将用户提供的原始案例更新表格去除全部记录内容，保留字段结构，生成这份可安全复用的本地模板：

[飞书个人网站案例更新表格：脱敏空白模板.xlsx](templates/飞书个人网站案例更新表格_脱敏空白模板.xlsx)

模板中不含原始案例、客户、项目简介、图片/视频文件名、附件、素材路径或外部链接。它包含三个工作表：

| 工作表 | 用途 |
| --- | --- |
| `数据表` | 保留原有项目案例字段：序号、项目名称、分类、标签、年份、简介、图片、封面、客户、视频和精选状态等。 |
| `文章模板` | 长文章、复盘和图文资料；其中明确包含 `正文飞书文档链接`。 |
| `使用说明` | 告诉维护者每张表怎么填，以及敏感信息不该放在哪里。 |

飞书操作：

飞书操作：

1. 打开飞书云文档，点击“新建”。
2. 选择“多维表格”。
3. 在表格中选择“导入”或“从 Excel 导入”。
4. 选择上面的模板文件，保留第一行作为字段名。
5. 导入后先不填真实内容，按下一节把字段类型设好，再新建一条测试记录。

这份模板来自当前项目的实际案例表结构，但**不要直接用它覆盖正在运行的飞书表格**。新建一张测试表导入后，再由开发者核对 `refresh.py` 的字段映射。

字段怎么填：

| 字段 | 推荐飞书字段类型 | 怎么用 |
| --- | --- | --- |
| 内容 ID | 单行文本 | 每条内容一个不变的唯一编号，例如 `article-001`。 |
| 内容类型 | 单选 | 选“项目”“文章”“视频”“资料”之一。 |
| 标题 | 单行文本 | 网站列表和详情页标题。 |
| 摘要 | 多行文本 | 列表页简介。 |
| 分类、发布状态 | 单选 | 用于筛选；发布状态建议有“草稿”“发布”。 |
| 排序 | 数字 | 数字越小越靠前，规则要全站统一。 |
| 封面图片、图片附件、原始视频附件、文件附件 | 附件 | 有 R2 时会在同步中转换为长期链接。 |
| 正文飞书文档链接 | 超链接或单行文本 | **文章继续写在飞书云文档里，把文档链接粘贴到这里。** 同步时读取文档 Block，渲染标题、段落、图片、表格和附件。 |
| B 站链接 | 超链接 | 轻量视频路线使用，网站嵌入或跳转播放。 |
| 外部链接 | 超链接 | 可填写项目网页、报名页或其他外部资料。 |
| 首页推荐 | 复选框 | 勾选后才在首页精选区域展示。 |

最小测试记录只要填：`内容 ID`、`内容类型`、`标题`、`发布状态`，再新建一份飞书云文档，把链接填入“正文飞书文档链接”。这样能先验证“多维表格 -> 飞书文档 -> 网站文章详情页”的完整链路。

### 4.1 飞书开放平台授权关键点

这里是很多新手最容易卡住的地方：飞书开放平台里给应用申请 API 权限，只代表应用有“调用接口的资格”；目标文件夹、文档、多维表格还要在飞书云文档里把协作权限给到这个应用。否则 GitHub Actions 有 App ID 和 App Secret，也可能读不到或改不了文件夹下面的文档。

建议按这个方式准备：

1. 在飞书开放平台创建自建应用。
2. 在应用能力中添加机器人能力。
3. 发布应用版本，并确保应用可用范围包含你自己或网站维护成员。
4. 在飞书客户端创建一个专用群组，例如：

```text
个人网站内容维护群
```

5. 把开放平台里的这个自建应用添加为群机器人。
6. 注意：这里添加的是“应用机器人”，不是普通的“自定义机器人 Webhook”。
7. 找到用于网站内容维护的飞书文件夹。
8. 把这个文件夹分享给刚才的群组。
9. 权限至少给到可阅读；如果需要创建、编辑、移动或管理文档，给到可编辑或可管理。
10. 确认文件夹下面的文档、多维表格、图片附件都继承或具备相应权限。

为什么要用群组授权：

- 后续你可以把维护网站的人都放进这个群。
- 文件夹只需要授权给这个群，不需要每个文档单独给应用补权限。
- 应用机器人在群里后，飞书可以把这个群组视为协作者范围。

如果这一步没做好，常见表现是：

- `refresh.py` 能拿到 tenant token，但读取文档时报无权限。
- 能读多维表格字段，但读不到文档正文或图片块。
- 能读某些旧文档，新建文档读不到。
- 文件夹下新建的文档没有被同步出来。

官方依据：

- 飞书开放平台的云文档资源权限说明中提到，需要为应用开通云文档相关资源权限。
- 飞书开放平台“增加协作者权限”文档说明，如果希望给应用授予文件夹权限，需要将应用作为群机器人添加到群组内，然后授予该群组相应权限。
- 飞书开放平台权限 FAQ 也说明，个人创建的文件夹要给应用访问，需要启用机器人能力，创建群组，将应用添加为群机器人，再在云文档中授权。

### 4.2 GitHub Secrets

需要给 GitHub 的 Secret 名称：

```text
LARK_APP_ID
LARK_APP_SECRET
LARK_BASE_TOKEN
LARK_TABLE_ID
LARK_ZHIXING_TABLE_ID
LARK_CURATION_TABLE_ID
```

注意：

- 只把这些值填到 GitHub Secrets。
- 不要写进 HTML、JS、Markdown、截图、聊天记录或公开仓库。
- 飞书权限不足时，脚本能跑但数据或附件会读取失败。
- API 权限、应用版本发布、机器人入群、文件夹协作权限要同时满足，缺一项都可能导致读取失败。

### 4.3 飞书云文档如何读取和正常渲染

飞书云文档不是一整段 HTML。官方 Docx API 把文档拆成树状 Block：标题、段落、图片、文件、表格、列表都是不同 block。网站如果只读取纯文本，就会丢失表格、图片、附件和很多样式。

正确读取流程：

1. 从飞书多维表格记录中读取“正文链接”或 document token。
2. 判断链接是新版 Docx、知识库文档还是普通云空间文档。
3. 如果是知识库文档，先通过知识库接口或资源信息拿到实际文档 token。
4. 调用“获取文档所有块”或“获取所有子块”接口。
5. 按分页完整读取，不要只读第一页。
6. 保留 block 顺序、层级、父子关系。
7. 图片块和文件块先拿素材 token，再换取临时下载 URL。
8. 有 R2 时，把临时下载 URL 下载后镜像为 R2 长期链接。
9. 把 block 类型映射成网站 HTML 组件。

渲染映射建议：

| 飞书内容 | 网站渲染 |
| --- | --- |
| 标题块 | `h1` 到 `h6` |
| 普通文本 | 段落、富文本、链接、加粗 |
| 有序/无序列表 | `ol` / `ul`，保留缩进层级 |
| 图片块 | `<img>`，使用 R2 长期链接或可访问图片 URL |
| 文件块 | 附件下载卡片或文件链接 |
| 表格块 | `<table>` 或移动端可横向滚动表格 |
| B 站链接 | iframe 嵌入或视频卡片 |
| 未识别 block | 安全占位并写入同步报告 |

之前表格渲染不出来，通常是这些原因：

- 只调用纯文本接口，表格结构被抹平。
- 只读取父块，没有分页读取所有子块。
- 没有递归处理 table、table_cell 这类嵌套结构。
- block 类型映射不完整，未知类型被直接跳过。
- 图片或文件 token 没有转换成可访问 URL。
- R2 替换只处理 `api/*.json` 顶层字段，没有进入文章正文 blocks。
- CSS 没有给表格设置横向滚动，移动端看起来像没渲染。

验收时必须准备一篇飞书测试文档，里面至少包含：

```text
标题
段落
图片
表格
列表
附件或 B 站链接
```

只有这篇测试文档能完整渲染，才说明飞书云文档解析逻辑是可靠的。

## 5. 第二步：部署到 GitHub Pages

目标：先让网站有一个公开地址。

操作：

1. 创建 GitHub 仓库。
2. 上传网站文件：

```text
index.html
home.html
styles.css
script.js
api/*.json
refresh.py
.github/workflows/refresh.yml
```

3. 打开 GitHub 仓库。
4. 进入 `Settings -> Pages`。
5. 选择发布来源：

```text
Deploy from a branch
Branch: main
Folder: /
```

6. 保存后等待 GitHub Pages 生成网站地址。

适合什么情况：

- 网站没有视频，或者视频很少。
- 你只想先看到网站能跑。

风险：

- 如果页面直接使用飞书临时媒体链接，24 小时后可能失效。
- 所以后面要么做 12 小时刷新，要么升级到 R2 长期链接。

官方依据：

- GitHub Pages 官方文档说明，可以从指定分支和目录发布网站，也可以用 GitHub Actions 发布。
- 阿里云和腾讯云备案文档均说明，使用中国内地服务器/服务开办网站通常需要 ICP 备案；阿里云文档也说明，域名仅解析至非中国内地服务器时无需进行工信备案。

## 6. 可选补救：什么时候需要 12 小时刷新飞书

目标：当网站还没有接 R2，且页面直接使用飞书媒体临时链接时，用定时刷新降低链接过期风险。

工作方式：

```text
GitHub Actions 定时触发
  -> refresh.py 调用飞书 API
  -> 重新生成 api/*.json
  -> 提交回 GitHub
  -> GitHub Pages 自动更新
```

如果还没有接 R2，可以在 `.github/workflows/refresh.yml` 中保留定时：

```yaml
on:
  schedule:
    - cron: "0 */12 * * *"
  workflow_dispatch:
```

适合：

- 纯静态网站。
- 暂时不接 Cloudflare R2。
- 少量图片或附件仍然直接来自飞书临时链接。

优点：

- 不用改网站结构。
- 对无视频、少量媒体的网站可临时够用。

缺点：

- 这是应对飞书临时链接的补救方案。
- 如果 Actions 失败，链接仍可能过期。
- 不适合大量图片、附件、视频。

当前项目状态：

- 现在已经接入 Cloudflare R2，所以不再需要为了飞书临时链接每 12 小时刷新。
- `Auto Refresh Feishu Portfolio` 可以保留为手动刷新，主要用于文字、排序、分类更新。

## 7. 第四步：连接 Cloudflare Pages

目标：让 Cloudflare 接管网站发布，同时继续从 GitHub 自动同步。

操作：

1. 登录 Cloudflare 控制台。
2. 进入：

```text
计算 -> Workers 和 Pages
```

3. 创建 Pages 项目。
4. 选择：

```text
连接到 Git
```

5. 授权 GitHub。
6. 选择网站仓库。
7. 设置：

```text
生产分支：main
构建命令：留空
构建输出目录：/
```

8. 点击部署。

部署后工作方式：

```text
GitHub main 有新提交
  -> Cloudflare Pages 自动检测
  -> 自动部署
  -> Cloudflare Pages 地址更新
```

优点：

- 仍然在 GitHub 更新代码和数据。
- Cloudflare 自动发布，不需要手工上传文件。
- 后续 DNS 和缓存都能统一在 Cloudflare 管理。

缺点：

- 只是接入 Pages 还不能解决飞书链接 24 小时过期。
- 要解决媒体长期链接，还需要 R2。

官方依据：

- Cloudflare Pages 官方文档说明，Pages 可以连接 GitHub/GitLab，并在 push 到分支时自动构建和部署。

## 8. 第五步：接 Cloudflare R2，把飞书媒体变长期链接

目标：把飞书图片、附件、视频从临时链接变成 R2 长期链接。

操作：

1. 在 Cloudflare 创建 R2 Bucket。
2. 开启公开访问，测试阶段可使用 `r2.dev` 公共地址。
3. 更正式的做法是绑定自己的媒体域名，例如：

```text
media.mycys.top
```

4. 创建 R2 API Token。
5. 在 GitHub Secrets 配置：

```text
CLOUDFLARE_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET
R2_PUBLIC_BASE_URL
```

6. 运行 GitHub Actions：

```text
Sync Feishu Media to Cloudflare R2
```

参数：

```text
What to mirror: all
Refresh Feishu data before mirroring media: 勾选
R2 orphan cleanup: report
```

运行后脚本会：

```text
读取 api/*.json
找到飞书临时媒体链接
下载媒体
计算 SHA-256
已存在的复用
新增或变更的上传到 R2
把 api/*.json 中的飞书链接替换为 R2 链接
生成 api/r2-media-manifest.json
提交回 GitHub
触发 Cloudflare Pages 自动部署
```

为什么这一步能避免 12 小时刷新：

- 飞书临时链接只是用来下载原始媒体。
- 下载后媒体对象保存在 R2。
- 网站访问的是 R2 链接，不再访问飞书临时链接。
- 所以不需要为了链接续期反复刷新。

官方依据：

- 飞书开放平台文档说明，获取媒体临时下载 URL 的有效期为 24 小时。
- Cloudflare R2 官方文档说明，R2 可用于 Web 内容和媒体存储；公开 bucket 可通过公共地址或自定义域名访问。
- Cloudflare 官方文档建议生产使用 R2 自定义域名，以获得缓存、规则和分析能力。

## 9. 第六步：视频加载怎么选

### 少量视频

建议：

```text
GitHub 保存网页代码
Cloudflare Pages 发布网站
Cloudflare R2 保存视频
Cloudflare DNS 开橙云代理和缓存规则
```

优点：

- 结构简单。
- 视频不占 GitHub Pages 访问压力。
- Cloudflare 可以在边缘网络缓存视频资源。

缺点：

- 免费额度和实际访问量要持续观察。
- `r2.dev` 更适合测试，正式建议绑定自己的媒体域名。

### 很多视频

建议评估：

```text
腾讯云 COS + CDN
阿里云 OSS + CDN
```

适合：

- 视频数量很多。
- 单个视频很大。
- 中国大陆访问占比高。
- 需要备案、日志、流量包、账单、客服支持。

利弊：

- 好处是更贴近国内视频分发和备案体系。
- 坏处是配置、费用、防盗链、CDN 缓存规则会更复杂。

## 10. 第七步：域名和 DNS

域名注册推荐：

- 腾讯云：适合已经在腾讯云备案、用 COS/CDN、需要腾讯云发票和账号体系的人。
- 阿里云：适合已经在阿里云备案、用 OSS/CDN、需要阿里云发票和账号体系的人。

域名注册商和 DNS 托管可以分开：

```text
域名在腾讯云或阿里云注册
NS 服务器改到 Cloudflare
DNS 记录在 Cloudflare 管理
```

Cloudflare DNS 推荐：

```text
mycys.top      CNAME  eason-webs.pages.dev   橙云代理
www.mycys.top  CNAME  eason-webs.pages.dev   橙云代理
```

如果以后给 R2 绑定媒体域名：

```text
media.mycys.top -> R2 Bucket 自定义域名
```

优点：

- 网站和缓存统一在 Cloudflare 管理。
- 域名仍然可以在国内注册商续费。

缺点：

- 腾讯云/阿里云 DNS 页面上的解析记录不再生效。
- DNS 生效需要等待全球递归缓存更新。

## 11. 第八步：Cloudflare 缓存规则

目标：让静态文件和视频更快，同时避免 JSON 和 HTML 太旧。

建议：

| 内容 | 缓存策略 | 原因 |
| --- | --- | --- |
| `.css`、`.js`、图片、字体 | 长缓存 | 文件不常变，适合边缘缓存 |
| `.mp4`、`.webm` | 长缓存 | 视频大，缓存收益高 |
| `/api/*.json` | 短缓存，例如 5 分钟 | 内容来自飞书，不能太旧 |
| HTML 页面 | 默认或短缓存 | 页面入口要及时更新 |

不要直接全站 `Cache Everything`。它可能让首页、文章页、JSON 长时间不更新。

如果 CSS 没更新，定向清理：

```text
https://mycys.top/styles.css
https://www.mycys.top/styles.css
https://eason-webs.pages.dev/styles.css
```

## 12. 第九步：日常更新怎么做

### 只改文字、顺序、分类

```text
飞书修改
  -> GitHub Actions 手动运行 Auto Refresh Feishu Portfolio
  -> GitHub 自动提交 api/*.json
  -> Cloudflare Pages 自动部署
```

### 新增图片、附件、视频

```text
飞书修改
  -> GitHub Actions 手动运行 Sync Feishu Media to Cloudflare R2
  -> R2 上传新增/变更媒体
  -> api/*.json 替换为 R2 长期链接
  -> GitHub 自动提交
  -> Cloudflare Pages 自动部署
```

### 删除飞书内容

```text
飞书删除内容
  -> 运行 R2 同步，cleanup_mode=report
  -> 查看孤儿文件报告
  -> 确认无误后再运行 cleanup_mode=delete
```

不要默认自动删除 R2 文件。先报告、再确认、再删除。

## 13. 上传 GitHub 前检查

每次提交前执行：

```powershell
cd E:\文档\webs\virtual-portfolio-demo
git fetch origin
git status --short --branch
git rebase origin/main
git diff --check
rg -n "T[O]DO" docs skills .github
rg -n "stream/download/authcode" api
```

再人工确认：

- 本次只提交需要的文件。
- 没有提交截图、缓存、测试产物、`.wrangler/`、`__pycache__/`。
- 没有提交任何真实密钥。
- 文档没有把腾讯 COS 写成当前主线。
- R2 删除默认仍然是 `report`。
- GitHub 直连方案和 Cloudflare/R2 方案的利弊都写清楚。

## 14. 当前项目的建议状态

当前这个网站有视频作品，并且已经接入 Cloudflare Pages 和 R2，所以建议采用：

```text
飞书维护内容
GitHub Actions 同步数据和媒体
Cloudflare Pages 发布网站
Cloudflare R2 保存媒体长期链接
Cloudflare DNS 管理 mycys.top
```

不建议回到“只用 GitHub Pages + 12 小时刷新”的方案，除非临时排障。这个方案适合没有视频、媒体很少的网站。

如果未来视频数量明显增多，再评估：

```text
腾讯云 COS/CDN
阿里云 OSS/CDN
```

## 15. 官方文档入口

- GitHub Pages：`https://docs.github.com/en/pages`
- GitHub Pages 发布源：`https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site`
- GitHub Pages 自定义域名：`https://docs.github.com/articles/about-supported-custom-domains`
- Cloudflare Pages Git 集成：`https://developers.cloudflare.com/pages/get-started/git-integration/`
- Cloudflare Pages 配置：`https://developers.cloudflare.com/pages/configuration/git-integration/`
- Cloudflare R2：`https://developers.cloudflare.com/r2/`
- Cloudflare R2 Public Buckets：`https://developers.cloudflare.com/r2/buckets/public-buckets/`
- Cloudflare R2 缓存：`https://developers.cloudflare.com/cache/interaction-cloudflare-products/r2/`
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

## 16. 备份

重要同步脚本、配置说明和验证结果备份到：

```text
F:\OneDrive\个人文件\网站素材\日常备份\YYYY-MM-DD
```

建议备份：

```text
refresh.py
sync_feishu_media_to_r2.py
.github/workflows/refresh.yml
.github/workflows/sync-r2.yml
docs/cloudflare-pages-r2-workflow.md
docs/feishu-github-cloudflare-personal-site-full-workflow.md
skills/feishu-github-cloudflare-personal-site-workflow/
reports/r2-media-sync-*.json
reports/r2-orphans-*.json
```

备份前同样检查：只备份说明、脚本、报告，不备份任何密钥值。
