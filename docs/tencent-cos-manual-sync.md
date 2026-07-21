# 腾讯 COS 手动媒体同步

## 设计

- `Auto Refresh Feishu Portfolio` 继续按原计划更新 GitHub 中的飞书数据；它只复用已经存在于 COS 的媒体，绝不上传新的媒体文件。
- `Sync Feishu Media to Tencent COS` 只在手动触发时执行。
- 手动工作流会选择性先刷新飞书数据，再下载 JSON 内的飞书附件链接，上传到 COS，并把 API JSON 中的媒体链接改成 COS 长期链接。
- `refresh.py` 不作修改，COS 密钥只保存在 GitHub Actions Secrets。

## 首次配置

GitHub 仓库：`Settings -> Secrets and variables -> Actions -> New repository secret`

| Secret | 填写内容 |
| --- | --- |
| `TENCENT_SECRET_ID` | 腾讯云 API 密钥的 SecretId |
| `TENCENT_SECRET_KEY` | 腾讯云 API 密钥的 SecretKey |
| `COS_BUCKET` | COS 存储桶完整名称，例如 `mycys-125xxxxxxxx` |
| `COS_REGION` | 存储桶地域代码，例如 `ap-beijing` |
| `COS_PUBLIC_BASE_URL` | 已绑定 CDN/自定义域名时填写，例如 `https://static.mycys.top`；未绑定则留空 |

可选变量：`Settings -> Secrets and variables -> Actions -> Variables`

| Variable | 填写内容 |
| --- | --- |
| `COS_MEDIA_PREFIX` | 可选，默认 `feishu-media` |

COS 存储桶需允许对象公开读取，或使用已配置访问域名/CDN 的公开读取路径；否则网站访客无法加载媒体。

## 日常手动更新

1. 在飞书中新增或修改图片、视频、附件。
2. GitHub 仓库打开 `Actions`。
3. 选择 `Sync Feishu Media to Tencent COS`。
4. 点击 `Run workflow`，保持 `Refresh Feishu data before mirroring media` 为勾选。
5. 等待完成。工作流会把稳定 COS 地址提交回 GitHub，GitHub Pages 自动发布。

如果仅想把当前 GitHub JSON 中仍指向飞书的链接上传 COS，可取消勾选“先刷新飞书数据”。

## 注意

- 自动飞书刷新会继续保留已经镜像过的 COS 长期链接；新增附件会暂时使用飞书临时链接，直到你执行一次手动 COS 工作流。
- COS 对象按文件内容 SHA-256 去重，重复媒体不会反复上传或产生重复存储。
- 视频本体和网站代码部署到 COS/CDN属于下一阶段迁移；当前方案先解决飞书附件的长期可用与国内媒体加载。
