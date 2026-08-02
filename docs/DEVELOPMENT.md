# 开发说明

本仓库的 Python 工具只使用标准库。

## 检查仓库

```bash
python scripts/check_repo.py
```

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## 扫描隐私和密钥

```bash
python scripts/privacy_scan.py
```

## 构建 Release 文件

```bash
python scripts/build_release.py
```

生成的 `.skill` 本质上是 ZIP，内部顶层必须只有一个 `qiuzhi-tracker/` 文件夹。
