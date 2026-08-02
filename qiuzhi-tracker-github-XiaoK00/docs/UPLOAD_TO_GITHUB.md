# 小白上传 GitHub 完整教程

本仓库已按 `XiaoK00` 配置完成。下面保留网页版上传和后续维护说明。

## 第一步：注册或登录 GitHub

打开 GitHub，登录自己的账号。记住用户名，例如：

```text
niki-lab
```

用户名不是昵称，而是个人主页链接中的那一段。

## 第二步：修改 README 中的用户名

用户名已经配置为 `XiaoK00`，无需再次替换。

## 第三步：新建仓库

1. 点击 GitHub 右上角 `+`。
2. 选择 `New repository`。
3. Repository name 填：`qiuzhi-tracker`。
4. Description 建议填：

```text
A Codex Agent Skill for verified company research, job-fit scoring, and actionable Excel job tracking.
```

5. 选择 `Public`，只有确定愿意公开源码时才这样做。
6. 不要勾选自动添加 README、`.gitignore` 或 License，因为压缩包中已经带齐。
7. 点击 `Create repository`。

## 第四步：上传文件

1. 解压 `qiuzhi-tracker-github-ready.zip`。
2. 进入解压后的 `qiuzhi-tracker-github-ready` 文件夹。
3. 在空仓库页面点击 `uploading an existing file`，或点击 `Add file` 后选择 `Upload files`。
4. 把文件夹里的全部内容拖进去，包括 `.github`、`skills`、`assets`、`docs` 和其他文件。
5. 不要只上传 ZIP，也不要再套一层多余文件夹。
6. Commit message 填：`Initial release v1.0.0`。
7. 点击 `Commit changes`。

## 第五步：等自动检查

打开仓库顶部的 `Actions`。正常情况下会出现 `Validate repository` 工作流。

绿色对勾表示：

- Skill 目录结构正确
- 验证脚本可运行
- 示例数据可通过
- 未发现常见个人信息或密钥
- `.skill` 可以重新打包

红色叉号时，点击失败步骤查看原因。首次上传最常见的问题是遗漏文件或误改 JSON。

## 第六步：填写 About 和 Topics

在仓库首页右侧 `About` 区域点击齿轮。

Description 填：

```text
A Codex Agent Skill for verified company research, job-fit scoring, and actionable Excel job tracking.
```

Topics 建议添加：

```text
agent-skills
codex
job-search
career
campus-recruitment
excel
job-tracker
career-tools
```

## 第七步：设置社交预览图

1. 进入 `Settings`。
2. 找到 `Social preview`。
3. 上传 `assets/social-preview.png`。

## 第八步：创建第一个 Release

1. 回到仓库首页。
2. 点击右侧 `Releases`。
3. 点击 `Create a new release`。
4. Tag 填：`v1.0.0`，并创建新标签。
5. Release title 填：`Qiuzhi Tracker v1.0.0`。
6. 说明可以复制 `CHANGELOG.md` 中的 `1.0.0` 内容。
7. 上传两个文件：
   - `dist/qiuzhi-tracker-v1.0.0.skill`
   - `dist/SHA256SUMS.txt`
8. 点击 `Publish release`。

## 第九步：测试安装

在 Codex 中输入：

```text
$skill-installer install https://github.com/XiaoK00/qiuzhi-tracker/tree/main/skills/qiuzhi-tracker
```

安装后重启 Codex。

## 第十步：以后怎么更新

最简单的方法：

1. 在仓库中打开要修改的文件。
2. 点击铅笔图标。
3. 修改后点击 `Commit changes`。
4. 大改版时更新 `VERSION`、`CHANGELOG.md`，重新生成 `.skill`，再创建新的 Release。

## 公开前最后确认

- [x] README 安装链接已配置为 `XiaoK00`
- [ ] 没有真实简历和投递记录
- [ ] 没有手机号、邮箱、微信、Cookie 或 Token
- [ ] Actions 显示绿色通过
- [ ] Release 已上传 `.skill`
- [ ] 安装链接可以打开
- [ ] 已理解 MIT 允许他人商业使用
