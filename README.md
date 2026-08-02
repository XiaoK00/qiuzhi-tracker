# Qiuzhi Tracker

一个面向 Codex Agent Skills 的通用求职信息整理工具。它根据简历、作品和求职限制建立真实企业池，核验具体岗位，并生成可行动的 Excel 求职追踪表。

## v1.1.0 核心能力

- 分级任务规模：轻量 20–40 / 5–10，标准 50–80 / 15–25，全面 100–150 / 30–50，支持自定义
- 标准档作为默认规模
- 分开判断硬性门槛、优先条件、岗位价值、契合指数和当前行动
- 检查岗位所属企业、过期截止日期、岗位新鲜度、来源等级和评分分项
- 生成求职总览、企业池、岗位清单和投递进度四张主表
- 更新旧表时保护投递日期、联系人、面试记录和复盘

## 安装

```text
$skill-installer install https://github.com/XiaoK00/qiuzhi-tracker/tree/main/skills/qiuzhi-tracker
```

也可以从 Release 下载 `qiuzhi-tracker-v1.1.0.skill`。

## 使用示例

```text
请使用 qiuzhi-tracker 读取我的简历和求职限制，按标准规模建立企业池，
核验具体岗位，分别判断硬性门槛、优先条件、岗位价值、契合指数和当前行动，
运行验证后生成 Excel 求职追踪表。
```

更多调用方式见 [`examples/example-prompts.md`](examples/example-prompts.md)。示例企业、岗位和人物均为虚构数据。

## 验证

```bash
python scripts/check_repo.py
python -m unittest discover -s tests -v
python scripts/privacy_scan.py
python scripts/build_release.py
```

## 信息可靠性

- 活跃岗位需要官方或官方关联来源。
- 第三方信息只作为待复核线索。
- 截止日期、核验日期和岗位新鲜度需要保持一致。
- 契合指数用于排序，不表示录用概率。

## 版本

当前版本：`v1.1.0`。变更见 [`CHANGELOG.md`](CHANGELOG.md)。

本项目使用 MIT License。
