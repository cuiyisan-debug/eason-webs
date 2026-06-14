# 飞书 API 配置与“新建云文档”页面接入说明

本文档整理当前作品集网站中已经使用的飞书 API 配置、数据源、接口、环境变量，以及后续新增“新建飞书云文档”页面时建议采用的接入方式。

> 安全原则：不要把 `LARK_APP_SECRET`、`tenant_access_token`、`user_access_token` 写入前端 JS、HTML、公开 JSON 或 Git 仓库。当前网站部署在 GitHub Pages，属于纯静态站点，不能安全地直接从浏览器创建飞书云文档。

## 1. 当前项目位置

- 本地目录：`E:\文档\webs\virtual-portfolio-demo`
- GitHub 仓库：`cuiyisan-debug/eason-webs`
- GitHub Pages 域名：`mycys.top`
- 自动刷新脚本：`refresh.py`
- GitHub Actions：`.github/workflows/refresh.yml`
- 输出数据：
  - `api/portfolio.json`
  - `api/zhixing.json`
  - `api/curation.json`

## 2. 当前飞书应用认证配置

当前项目使用飞书自建应用的服务端鉴权方式。

### GitHub Secrets

这些值保存在 GitHub Actions Secrets 中，不应写入仓库：

| Secret 名称 | 用途 | 是否必须 |
| --- | --- | --- |
| `LARK_APP_ID` | 飞书自建应用 App ID | 必须 |
| `LARK_APP_SECRET` | 飞书自建应用 App Secret | 必须 |
| `LARK_BASE_TOKEN` | 主作品项目库 Base token | 必须 |
| `LARK_TABLE_ID` | 主作品项目库 table id | 必须 |
| `LARK_ZHIXING_TABLE_ID` | 知行表 table id；为空时脚本自动选择 | 可选 |
| `LARK_CURATION_TABLE_ID` | 策展表 table id；为空时脚本自动选择 | 可选 |

### 仓库中明文配置

以下不是应用密钥，但属于数据源标识，当前写在 workflow 和 `refresh.py` 中：

| 配置项 | 当前值 | 用途 |
| --- | --- | --- |
| `LARK_ZHIXING_BASE_TOKEN` | `Vn7hbNMygaDrSMseVgycCCJen1e` | 知行文章 Base |
| `LARK_CURATION_BASE_TOKEN` | `CtqgbzQHVazUyhsSiOEcIrxfnSd` | 策展文章 Base |

如后续迁移表格，只需要更新这两个 token 或改为 GitHub Secrets。

## 3. 当前使用的飞书 API

### 3.1 获取 tenant_access_token

用途：用 `APP_ID + APP_SECRET` 换取服务端访问 token。

```http
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Content-Type: application/json

{
  "app_id": "LARK_APP_ID",
  "app_secret": "LARK_APP_SECRET"
}
```

当前代码位置：`refresh.py -> tenant_access_token()`

### 3.2 获取多维表格列表

用途：当没有显式指定 table id 时，脚本会遍历 Base 下的表，自动选择最像数据表的那一张。

```http
GET https://open.feishu.cn/open-apis/bitable/v1/apps/{base_token}/tables
Authorization: Bearer {tenant_access_token}
```

当前代码位置：`refresh.py -> list_tables()`

### 3.3 读取多维表格记录

用途：读取作品、知行文章、策展文章的所有记录。

```http
GET https://open.feishu.cn/open-apis/bitable/v1/apps/{base_token}/tables/{table_id}/records?page_size=500
Authorization: Bearer {tenant_access_token}
```

当前代码位置：`refresh.py -> fetch_records()`

### 3.4 获取飞书附件临时下载链接

用途：把多维表格附件字段、飞书文档图片中的 `file_token` 转成可在网页中显示的临时 URL。

```http
GET https://open.feishu.cn/open-apis/drive/v1/medias/batch_get_tmp_download_url?file_tokens={file_token}
Authorization: Bearer {tenant_access_token}
```

多维表格附件会附加：

```json
{
  "bitablePerm": {
    "tableId": "table_id"
  }
}
```

当前代码位置：`refresh.py -> resolve_urls()`

注意：这些临时 URL 会过期，所以项目通过 GitHub Actions 每 12 小时自动刷新 JSON。

### 3.5 读取飞书 Docx 文档纯文本

用途：从文章正文链接读取飞书文档文字内容。

```http
GET https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/raw_content
Authorization: Bearer {tenant_access_token}
```

当前代码位置：`refresh.py -> fetch_feishu_doc_content()`

### 3.6 读取飞书 Docx 文档块

用途：读取文档中的段落、图片、表格等块结构，用于文章详情页按原文顺序渲染图文。

当前脚本尝试三种方式：

```http
GET /open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/descendant
GET /open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children
GET /open-apis/docx/v1/documents/{document_id}/blocks
```

当前代码位置：

- `refresh.py -> fetch_feishu_descendant_blocks()`
- `refresh.py -> fetch_feishu_child_blocks()`
- `refresh.py -> fetch_feishu_doc_blocks()`
- `refresh.py -> build_doc_content_blocks()`

## 4. 当前字段约定

### 4.1 主作品表字段

| 字段变量 | 默认字段名 | 用途 |
| --- | --- | --- |
| `LARK_FIELD_TITLE` | `项目名称` | 项目标题 |
| `LARK_FIELD_CATEGORY` | `前台分类` | 分类 |
| `LARK_FIELD_SUMMARY` | `项目简介` | 简介 |
| `LARK_FIELD_IMAGES` | `图片` | 项目图片附件 |
| `LARK_FIELD_COVER` | `封面` | 封面图，优先于图片附件 |
| `LARK_FIELD_YEAR` | `年份` | 项目年份 |
| `LARK_FIELD_FEATURED` | `首页轮播` | 值为“是”时进入首页轮播 |
| `LARK_FIELD_VIDEO_URL` | `视频链接` | 外部视频链接 |
| `LARK_FIELD_VIDEO_BV` | `视频BV号` | B站 BV 号 |
| `LARK_FIELD_ROLE` | `角色` | 项目角色 |
| `LARK_FIELD_TAGS` | `二级标签` | 标签 |
| `LARK_FIELD_STATUS` | `项目状态` | 状态 |
| `LARK_FIELD_ORDER` | `序号` | 排序 |

### 4.2 文章表字段

知行和策展共用文章字段候选：

| 字段用途 | 候选字段名 |
| --- | --- |
| 标题 | `标题`、`文章标题`、`名称`、`主题`、`Title`、`title` |
| 简介 | `简介`、`摘要`、`说明`、`描述`、`Summary`、`summary` |
| 正文 | `正文`、`正文内容`、`内容`、`详细内容`、`文章内容`、`文章正文`、`全文`、`Body`、`Content` |
| 正文链接 | `正文链接`、`文章链接`、`原文链接`、`外部链接`、`链接`、`URL`、`Link` |
| 附件/图片 | `附件`、`图片`、`封面`、`视频`、`媒体`、`素材` |
| 附件顺序 | `附件顺序`、`图片顺序`、`媒体顺序` |

规则：

- 如果有“正文链接”，并且链接是飞书 Docx，脚本会尝试读取文档正文和文档图片。
- 如果表格附件字段有图片，图片会进入 `media`。
- 如果 Docx 文档中有图片，图片会进入 `contentBlocks`，并按文档顺序显示。
- `cover` 默认取第一张可用图片。

## 5. 当前 GitHub Actions 自动刷新

文件：`.github/workflows/refresh.yml`

触发方式：

- push 到 `main`
- 每 12 小时定时刷新：`0 */12 * * *`
- 手动触发：`workflow_dispatch`

刷新流程：

1. Checkout 仓库
2. 安装 Python
3. 执行 `python refresh.py`
4. 提交更新后的：
   - `api/portfolio.json`
   - `api/zhixing.json`
   - `api/curation.json`

## 6. 现有前端数据消费

### 6.1 作品数据

- `script.js` 读取：`api/portfolio.json`
- `project.js` 读取：`api/portfolio.json`

### 6.2 文章列表

- `articles.js` 根据页面上的 `data-article-source` 读取：
  - `api/zhixing.json`
  - `api/curation.json`

### 6.3 文章详情

- `article.js` 读取：
  - `article.html?source=zhixing&id=...`
  - `article.html?source=curation&id=...`

文章详情渲染优先级：

1. 如果有 `contentBlocks`，按块渲染段落、图片、表格。
2. 如果没有 `contentBlocks`，回退到 `media + body`。

## 7. 新建“飞书云文档”页面的推荐架构

你想新增一个网页页面，用于“新建飞书云文档”。这里不能直接在前端调用飞书 API，因为前端会暴露密钥。

推荐架构：

```mermaid
flowchart LR
  A["网站页面 create-doc.html"] --> B["安全后端接口 / Serverless Function"]
  B --> C["飞书 tenant_access_token"]
  C --> D["创建飞书 Docx 文档"]
  D --> E["向文档写入块内容"]
  E --> F["返回 document_id / url 给网页"]
```

### 方案 A：Serverless API，推荐

适合后续长期使用。

可选平台：

- Vercel Functions
- Netlify Functions
- Cloudflare Workers
- 自己的轻量服务器

优点：

- 可以安全保存 `APP_SECRET`
- 页面提交表单后实时创建飞书文档
- 可以继续扩展上传图片、写入表格、写入模板

### 方案 B：GitHub Actions 手动/接口触发，不推荐做实时页面

可以通过 GitHub Actions 保存密钥并创建文档，但它不是实时 API，适合批处理，不适合网页按钮即时创建。

## 8. 新建飞书 Docx 云文档需要的 API

### 8.1 创建 Docx 文档

官方接口：

```http
POST https://open.feishu.cn/open-apis/docx/v1/documents
Authorization: Bearer {tenant_access_token}
Content-Type: application/json

{
  "title": "新文档标题",
  "folder_token": "可选，目标文件夹 token"
}
```

返回结果中会包含 `document_id`。后续写入内容时使用这个 `document_id`。

### 8.2 创建文档块

用于向文档中插入标题、段落、图片、表格等块。

```http
POST https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children
Authorization: Bearer {tenant_access_token}
Content-Type: application/json

{
  "children": [
    {
      "block_type": 2,
      "text": {
        "elements": [
          {
            "text_run": {
              "content": "段落内容"
            }
          }
        ]
      }
    }
  ]
}
```

具体 `block_type` 和结构需要按飞书官方文档映射。

### 8.3 上传图片/素材到文档

用于把图片上传到飞书文档块中。

```http
POST https://open.feishu.cn/open-apis/drive/v1/medias/upload_all
Authorization: Bearer {tenant_access_token}
Content-Type: multipart/form-data
```

返回 `file_token` 后，再把这个 token 写入图片块。

## 9. 新建云文档页面建议字段

页面文件建议：`create-doc.html`

表单字段：

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| `title` | 文本 | 文档标题 |
| `category` | 下拉 | 文档类型：策展、知行、项目复盘、工具说明 |
| `summary` | 多行文本 | 文档简介 |
| `body` | 多行文本 | 正文初稿 |
| `folderToken` | 文本，可选 | 目标飞书文件夹 |
| `cover` | 文件，可选 | 封面图 |
| `images` | 文件，可选 | 正文图片 |
| `createMode` | 下拉 | 空白文档 / 带模板文档 |

## 10. 建议后端接口设计

前端页面不要直接请求飞书，而是请求自己的安全接口。

```http
POST /api/create-feishu-doc
Content-Type: application/json

{
  "title": "文档标题",
  "summary": "简介",
  "body": "正文",
  "category": "策展",
  "folderToken": "可选"
}
```

后端处理流程：

1. 从环境变量读取 `LARK_APP_ID`、`LARK_APP_SECRET`
2. 获取 `tenant_access_token`
3. 调用创建 Docx 文档接口
4. 调用创建块接口写入标题、简介、正文
5. 返回：

```json
{
  "documentId": "xxx",
  "url": "https://my.feishu.cn/docx/xxx"
}
```

## 11. 新增功能所需飞书权限

当前读取类权限可能不够创建文档。新建云文档通常还需要补充：

| 能力 | 用途 |
| --- | --- |
| 获取 tenant_access_token | 服务端认证 |
| 创建 Docx 文档 | 新建云文档 |
| 编辑 Docx 文档块 | 写入正文、表格、图片 |
| 上传素材/图片 | 上传封面和正文图片 |
| 读取/写入云空间文件夹 | 如果要指定目标文件夹 |

具体权限名称以飞书开放平台后台为准。新增权限后，需要重新发布飞书应用版本。

## 12. 对当前项目的改造建议

建议新增这些文件：

```text
create-doc.html
create-doc.js
docs/feishu-api-config.md
```

如果采用 Serverless，再新增：

```text
api/create-feishu-doc.js
```

但当前 GitHub Pages 不能直接运行 `api/create-feishu-doc.js`。如果继续使用 GitHub Pages 托管前端，后端接口需要部署到 Vercel、Netlify、Cloudflare Workers 或其他服务。

## 13. 参考官方文档

- 飞书 Docx 概览：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/docx-overview>
- 创建 Docx 文档：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>
- 创建文档块：<https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create>
- 上传素材：<https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all>
- 多维表格概览：<https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview>

