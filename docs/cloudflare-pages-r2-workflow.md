# Cloudflare Pages + R2 工作流

## 当前配置

- Cloudflare Account ID: `512403c7bf64cbdb7e76993a25a8a55d`
- R2 Bucket: `mycys-media`
- R2 public base URL: `https://pub-a0425f41996c4db49bbd1eb2225d74f2.r2.dev`
- Cloudflare Pages: `https://eason-webs.pages.dev`

密钥只放 GitHub Actions Secrets，不写入仓库。

## GitHub Secrets

在 `Settings -> Secrets and variables -> Actions -> Secrets` 中配置：

| Secret | 说明 |
| --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账户 ID |
| `R2_ACCESS_KEY_ID` | R2 API 令牌的访问密钥 ID |
| `R2_SECRET_ACCESS_KEY` | R2 API 令牌的机密访问密钥 |
| `R2_BUCKET` | `mycys-media` |
| `R2_PUBLIC_BASE_URL` | `https://pub-a0425f41996c4db49bbd1eb2225d74f2.r2.dev` |

可选 GitHub Variable：

| Variable | 建议值 |
| --- | --- |
| `R2_MEDIA_PREFIX` | `feishu-media` |
| `R2_LOCAL_MEDIA_PREFIX` | `site-media` |

## 日常更新

### 只改文字、排序、分类

手动运行：

```text
Auto Refresh Feishu Portfolio
```

这个 workflow 不再定时执行。它会先从飞书重新生成 JSON，再复用已经镜像到 R2 的媒体链接。GitHub 更新后，Cloudflare Pages 会自动部署。

### 新增或替换图片、视频、附件

运行：

```text
Sync Feishu Media to Cloudflare R2
```

如果只想先迁移 GitHub 仓库中的页面视频，把 `What to mirror` 选为：

```text
local_videos
```

并取消勾选：

```text
Refresh Feishu data before mirroring media
```

它会：

```text
刷新飞书数据
扫描 api/*.json 中的飞书临时媒体链接
下载未镜像过的媒体
按 SHA-256 上传到 R2
扫描 assets/ 中的本地视频
把本地视频上传到 R2 的 site-media/ 前缀
生成 api/r2-media-manifest.json
把 api/*.json 中的飞书临时链接替换成 R2 长期链接
把页面中的本地视频引用替换成 R2 长期链接
扫描当前网站仍在引用的 R2 文件
生成已不再引用的 R2 孤儿文件报告
提交回 GitHub
触发 Cloudflare Pages 自动部署
```

### 清理飞书已删除内容对应的 R2 文件

`Sync Feishu Media to Cloudflare R2` 里有 `R2 orphan cleanup` 选项：

| 选项 | 含义 |
| --- | --- |
| `report` | 默认值。只生成 `reports/r2-orphans-YYYY-MM-DD.json`，不删除 R2 文件。 |
| `delete` | 同步后删除当前网站已经不再引用的 R2 文件，并从 manifest 移除。 |
| `off` | 不做孤儿文件检测。 |

建议日常先使用 `report`。确认报告中的文件确实来自飞书已删除内容后，再手动重跑一次并选择 `delete`。

## 增量规则

- 内容相同：复用已有 R2 对象。
- 内容新增：上传到 `feishu-media/`。
- 内容变更：生成新的 SHA-256 和新的 R2 对象。
- 飞书删除：新 JSON 不再引用；R2 旧文件暂时保留，避免误删缓存或历史引用。
- R2 孤儿文件：默认只写报告；选择 `delete` 后才真正删除。
- GitHub 仓库中的本地视频：上传到 `site-media/`，页面引用改为 R2 地址。

当前公开 JSON 不保存飞书附件 token，因此脚本需要下载飞书临时链接后计算 hash；但不会重复上传已存在内容。

## 触发规则

- GitHub 代码更新：Cloudflare Pages 自动部署。
- 飞书文字、排序、分类更新：手动运行 `Auto Refresh Feishu Portfolio`。
- 飞书新增或替换图片、视频、附件：手动运行 `Sync Feishu Media to Cloudflare R2`。
- GitHub 本地视频更新：手动运行 `Sync Feishu Media to Cloudflare R2`。

R2 已经解决媒体长期链接问题，因此不需要为了飞书临时链接过期而每 12 小时刷新一次。

## 验证

发布后检查：

- Cloudflare Pages 地址可打开：`https://eason-webs.pages.dev`
- `api/*.json` 可以访问。
- JSON 中媒体链接不再包含 `/stream/download/authcode/`。
- 媒体链接变成 `https://pub-a0425f41996c4db49bbd1eb2225d74f2.r2.dev/feishu-media/...`。
- 本地视频链接变成 `https://pub-a0425f41996c4db49bbd1eb2225d74f2.r2.dev/site-media/...`。
- GitHub Actions 日志中 `failed` 为 0。
- 如果启用默认清理报告，检查 `reports/r2-orphans-YYYY-MM-DD.json`。
