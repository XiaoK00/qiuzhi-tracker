# 发布新版本

## 版本规则

- 修复文字或小错误：`1.0.1`
- 增加兼容功能但不破坏旧数据：`1.1.0`
- 大幅改变字段或数据结构：`2.0.0`

## 发布前

1. 修改 `VERSION`。
2. 更新 `CHANGELOG.md`。
3. 确认 `skills/qiuzhi-tracker/SKILL.md` 和模板同步。
4. 运行：

```bash
python scripts/check_repo.py
python -m unittest discover -s tests -v
python scripts/privacy_scan.py
python scripts/build_release.py
```

## GitHub Release

1. 新建与版本一致的 Tag，例如 `v1.1.0`。
2. 上传 `dist/qiuzhi-tracker-v1.1.0.skill`。
3. 上传 `dist/SHA256SUMS.txt`。
4. 从 `CHANGELOG.md` 复制本次变更说明。
5. 发布后再次测试 GitHub 目录安装。
