# 参与贡献

感谢你帮助改进 Qiuzhi Tracker。

## 可以提交什么

- 修复验证脚本错误
- 改进招聘状态判断规则
- 增加不同行业的检索方法
- 改进 Excel 模板的可读性
- 修复失效文档和安装说明
- 提交隐私安全问题

## 不应提交什么

- 真实用户简历或投递记录
- 未脱敏的手机号、邮箱、微信或联系人
- Cookie、Token、API Key 和登录凭证
- 无法追溯的招聘信息
- 把搜索摘要冒充官方招聘公告的数据

## 提交前检查

```bash
python scripts/check_repo.py
python -m unittest discover -s tests -v
python scripts/privacy_scan.py
```

修改 Skill 后重新打包：

```bash
python scripts/build_release.py
```

## Pull Request 要求

请说明：

1. 修改了什么
2. 为什么需要修改
3. 如何验证
4. 是否影响工作簿结构或数据格式
5. 是否包含任何真实个人信息
