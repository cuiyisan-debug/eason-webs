# 飞书附件长期链接：GitHub Actions + 腾讯 COS

网站仍由 GitHub Pages 托管；飞书数据刷新仍由 `refresh.py` 负责。
刷新后，`sync_feishu_media_to_cos.py` 会把 API JSON 中的飞书临时附件链接下载到 COS，再替换为 COS 的稳定链接。

## GitHub Secrets

在仓库 `Settings -> Secrets and variables -> Actions` 新建以下 **Secrets**：

| 名称 | 内容 |
| --- | --- |
| `TENCENT_SECRET_ID` | 腾讯云 CAM 子用户的 SecretId |
| `TENCENT_SECRET_KEY` | 腾讯云 CAM 子用户的 SecretKey |
| `COS_BUCKET` | 完整存储桶名称，例如 `mycys-1234567890` |
| `COS_REGION` | 存储桶地域，例如 `ap-beijing` |
| `COS_PUBLIC_BASE_URL` | COS 公开访问根地址；备案和 CDN 完成后改为 `https://static.mycys.top` |

CAM 子用户只需对该存储桶的媒体前缀拥有 `GetObject`、`PutObject`、`HeadObject` 权限。不要把以上信息放进网页代码、JSON 或仓库文件。

## COS 设置

- 桶权限：`公有读私有写`。
- 给 `feishu-media/*` 设置长期缓存；脚本已同时写入 `Cache-Control`。
- 在 GitHub Pages 阶段，`COS_PUBLIC_BASE_URL` 可先填 COS 桶公开域名。
- 域名备案并开通 CDN 后，仅修改该 Secret 为 CDN 域名并手动运行一次刷新，即可让新 JSON 使用 CDN 链接。

## 刷新顺序

1. 修改飞书多维表格或文章附件。
2. 在 GitHub Actions 运行 `Auto Refresh Feishu Portfolio`，或等待定时刷新。
3. `refresh.py` 生成最新 JSON。
4. COS 镜像步骤上传新增或变更的附件，并把临时链接改为长期 COS 链接。
5. Actions 自动提交四个 API JSON 文件，GitHub Pages 发布新内容。

`refresh.py` 不参与 COS 逻辑，保持原样。
