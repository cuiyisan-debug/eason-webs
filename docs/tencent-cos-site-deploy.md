# 腾讯 COS 网站部署说明

## 当前配置

- COS_BUCKET: `mycys-1442289218`
- COS_REGION: `ap-beijing`
- 域名 `mycys.top` 当前仍在 ICP 备案中。

备案完成前，GitHub Actions 可以先使用 COS 默认公开域名测试：

```text
https://mycys-1442289218.cos.ap-beijing.myqcloud.com
```

备案完成并绑定自定义域名或 CDN 后，把 GitHub Secret `COS_PUBLIC_BASE_URL` 改成正式域名，例如：

```text
https://www.mycys.top
```

或：

```text
https://static.mycys.top
```

## GitHub Secrets

在 `Settings -> Secrets and variables -> Actions -> Secrets` 中配置：

| Secret | 说明 |
| --- | --- |
| `TENCENT_SECRET_ID` | 腾讯云 CAM 子用户 SecretId |
| `TENCENT_SECRET_KEY` | 腾讯云 CAM 子用户 SecretKey |
| `COS_BUCKET` | `mycys-1442289218` |
| `COS_REGION` | `ap-beijing` |
| `COS_PUBLIC_BASE_URL` | 备案完成前可留空；完成后填正式域名 |

不要把腾讯云密钥写入网页代码、JSON、文档正文或仓库文件。

## GitHub Variables

在 `Settings -> Secrets and variables -> Actions -> Variables` 中配置：

| Variable | 建议值 |
| --- | --- |
| `COS_MEDIA_PREFIX` | `feishu-media` |
| `COS_SITE_PREFIX` | 留空 |

`COS_SITE_PREFIX` 留空表示网站发布到 COS 根目录。

## COS 桶设置

- 权限: 公有读私有写。
- 静态网站: 开启。
- 默认首页: `index.html`。
- 错误页面: `index.html`。
- 备案完成后绑定自定义域名并配置 HTTPS。
- 如果视频仍慢，再给正式域名接入 CDN。

## 发布按钮

仓库中提供三个 Actions：

| Workflow | 用途 |
| --- | --- |
| `Auto Refresh Feishu Portfolio` | 自动刷新飞书数据，复用已有 COS 媒体 |
| `Sync Feishu Media to Tencent COS` | 日常手动发布，刷新飞书、增量同步媒体、部署整站 |
| `Deploy Website to Tencent COS` | 只部署当前 GitHub 网站文件到 COS |

日常新增图片、视频、附件后，优先使用：

```text
Sync Feishu Media to Tencent COS
```

如果只是改了 HTML、CSS、JS，可以只运行：

```text
Deploy Website to Tencent COS
```

## 验证

发布后检查：

- 首页是否可打开。
- `api/portfolio.json`、`api/clients.json`、`api/zhixing.json`、`api/curation.json` 是否可访问。
- JSON 中是否还有 `/stream/download/authcode/`。
- 图片和视频 URL 是否已经变成 COS 长期链接。
- GitHub Actions 日志中 `uploaded`、`skipped`、`failed` 计数是否正常。

