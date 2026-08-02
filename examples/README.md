# 示例文件

本目录所有企业、岗位和人物均为虚构，不代表真实招聘信息。

- `sample-resume.md`：虚构简历输入
- `example-prompts.md`：调用提示词
- `example-tracker-data.json`：验证脚本输入
- `example-output-redacted.xlsx`：脱敏示例工作簿

运行示例验证：

```bash
python skills/qiuzhi-tracker/scripts/validate_tracker_data.py   examples/example-tracker-data.json   --min-companies 6 --min-jobs 4
```
