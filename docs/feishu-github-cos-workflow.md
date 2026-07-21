# 飞书 + GitHub + 腾讯 COS 日常流程

## 分工

- 飞书: 维护项目、文章、客户、图片、视频和附件。
- GitHub: 保存源码、自动刷新飞书数据、记录版本、运行发布流程。
- 腾讯 COS: 承载长期媒体链接和正式静态网站文件。
- GitHub Pages: 保留为备用访问路径。

## 首次全量迁移

1. 在 GitHub Secrets 配置飞书和腾讯云密钥。
2. 在 GitHub Variables 配置 `COS_MEDIA_PREFIX=feishu-media`，`COS_SITE_PREFIX` 留空。
3. 打开 GitHub Actions。
4. 运行 `Sync Feishu Media to Tencent COS`。
5. 保持 `Refresh Feishu data before mirroring media` 为勾选。

首次运行会：

```text
刷新飞书数据
扫描 api/*.json 中的飞书临时媒体链接
下载所有未镜像过的媒体
按 SHA-256 上传到 COS
生成 api/media-manifest.json
把 api/*.json 中的飞书链接替换为 COS 链接
提交 JSON、清单和报告到 GitHub
上传整站静态文件到 COS
```

## 日常更新

### 只改文字、排序、分类

等待自动刷新，或手动运行：

```text
Auto Refresh Feishu Portfolio
```

自动刷新会复用已经镜像到 COS 的媒体，不主动上传新媒体。

### 新增或替换图片、视频、附件

运行：

```text
Sync Feishu Media to Tencent COS
```

它会刷新飞书数据，并且只上传新增或内容变更的媒体。已存在于 COS 的媒体会按内容 hash 复用。

### 只改网站代码

运行：

```text
Deploy Website to Tencent COS
```

它只上传网站静态文件，不刷新飞书、不处理媒体。

## 增量规则

媒体脚本以文件内容 SHA-256 作为 COS 对象身份：

- 内容相同: 复用已有 COS 对象，不重复上传。
- 内容新增: 上传到 `feishu-media/`。
- 内容变更: 生成新的 SHA-256 和新的 COS 对象。
- 飞书删除: 新 JSON 不再引用，COS 旧文件先保留，避免误删历史缓存。

当前公开 API JSON 不保存飞书附件 token，因此脚本需要下载飞书临时链接后才能计算 hash。它不会重复上传已存在的媒体。

## 输出文件

发布后会更新：

```text
api/portfolio.json
api/clients.json
api/zhixing.json
api/curation.json
api/media-manifest.json
reports/cos-media-sync-YYYY-MM-DD.json
```

整站部署脚本还会在 Actions 日志中输出上传、跳过和失败统计。

## 域名切换

`mycys.top` 备案期间，先用 COS 默认域名测试。

备案完成后：

1. 在 COS 或 CDN 绑定正式域名。
2. 配置 CNAME。
3. 配置 HTTPS 证书。
4. 把 GitHub Secret `COS_PUBLIC_BASE_URL` 改为正式域名。
5. 重新运行 `Sync Feishu Media to Tencent COS`。

新生成的 JSON 会使用正式域名下的 COS 长期链接。
