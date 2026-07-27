# Cloudflare Worker + Durable Object 访问统计

## 当前目标

替代前端不蒜子统计脚本，由 Cloudflare Worker 接收网站访问事件，再用 Durable Object 持久化 PV、UV 和最近访问记录。

旧不蒜子统计已作为历史基数叠加进公开展示：

| 指标 | 历史基数 |
| --- | ---: |
| PV | 1132 |
| UV | 811 |

Worker 返回给前端的是 `历史基数 + 新系统增量`。后台接口会同时返回 `site`、`rawSite` 和 `offsets`，便于区分公开展示值与新系统真实增量。

前端展示接口：

```text
https://mycys.top/api/visitor-stats
```

后台查询接口：

```text
https://mycys.top/api/visitor-stats/admin
```

后台查看页面：

```text
https://mycys.top/visitor-admin.html
```

这个页面不会保存密钥到源码。管理员在浏览器里输入 `VISITOR_ADMIN_TOKEN` 后，页面用 `Authorization: Bearer ...` 调用后台查询接口。

## GitHub Secrets

部署 Worker 需要在 GitHub Actions Secrets 中配置：

| Secret | 说明 |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | 允许部署 Workers、管理 Worker Routes、Durable Objects 的 Cloudflare API Token |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare 账户 ID |

后台查询需要在 Cloudflare Worker 中配置 Secret：

| Worker Secret | 说明 |
| --- | --- |
| `VISITOR_ADMIN_TOKEN` | 后台查询 Bearer Token |
| `VISITOR_IP_HASH_SALT` | 可选。用于生成 IP 哈希，建议配置为随机长字符串 |

## 部署

GitHub Actions 会在 `main` 分支中这些路径变化时自动部署：

```text
workers/visitor-counter/**
.github/workflows/deploy-visitor-counter.yml
```

也可以手动运行：

```text
Deploy Cloudflare Visitor Counter
```

本地有 Cloudflare 凭据时，可手动部署：

```powershell
npx --yes wrangler@latest deploy --config workers/visitor-counter/wrangler.toml
```

配置后台查询 token：

```powershell
npx --yes wrangler@latest secret put VISITOR_ADMIN_TOKEN --config workers/visitor-counter/wrangler.toml
npx --yes wrangler@latest secret put VISITOR_IP_HASH_SALT --config workers/visitor-counter/wrangler.toml
```

## 后台查询

### 网页后台

打开：

```text
https://mycys.top/visitor-admin.html
```

输入 `VISITOR_ADMIN_TOKEN` 后可以查看累计 PV/UV、新系统增量、访问路径、来源、国家、IP、IP Hash、User-Agent 和访问时间，并支持分页与 CSV 导出。

### PowerShell 查询

请求示例。`limit` 单次最多 200 条，返回的 `nextBefore` 可用于继续查询更早记录：

```powershell
$token = "只放本地，不写进文件"
Invoke-RestMethod `
  -Uri "https://mycys.top/api/visitor-stats/admin?limit=100&reveal=1" `
  -Headers @{ Authorization = "Bearer $token" }
```

`reveal=1` 会返回明文 IP。没有这个参数时，后台只返回脱敏 IP、IP 哈希、国家、页面、来源、User-Agent 和时间。

继续翻页：

```powershell
Invoke-RestMethod `
  -Uri "https://mycys.top/api/visitor-stats/admin?limit=100&before=上一页返回的nextBefore&reveal=1" `
  -Headers @{ Authorization = "Bearer $token" }
```

## 隐私边界

- Worker 记录的是统计接口收到的访问，不等于每一个真实自然人。
- VPN、代理、公司网关会改变出口 IP。
- `VISITOR_STORE_FULL_IP` 当前为 `true`，会保存访问记录中的明文 IP，后台接口必须保持鉴权。
- 访问记录按递增编号保存，后台按页查询。长期全量保存会占用 Durable Object 存储；如果访问量增长，建议再接 D1 或 R2 做日志归档。
