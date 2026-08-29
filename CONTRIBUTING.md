# Contributing

欢迎提交能让迁移决策更准确、输出更轻量或验证更可靠的改进。

## 开发

本项目只依赖 Python 标准库。提交前运行：

```powershell
python -m unittest discover -s tests -v
python scripts\audit_project.py --root . --format json
```

如果本机安装了 Codex，继续运行 `skill-creator` 附带的 `quick_validate.py`。

## 变更要求

- 修复应描述可复现的误判或迁移失败，不为单个项目硬编码规则。
- 审计脚本保持只读，不执行目标仓库内容，不跟随链接，不上传数据。
- 修改 `SKILL.md` 时同步检查描述是否仍能准确触发且不会吸引普通功能开发。
- 新增 reference 时从 `SKILL.md` 明确说明何时读取，避免重复已有内容。
- PR 写明用户价值、范围、实际测试结果、AI 参与和人工复核范围。

使用 Conventional Commits，例如：

```text
fix(audit): detect nested GitHub workflow files
docs: clarify layered migration criteria
```
