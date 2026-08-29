# Vibe Project Migrator：仓库协作规则

## 范围与目标

- 本文件适用于整个仓库；用户当前要求和更近层级规则优先。
- 本仓库交付一个可独立安装的 Codex skill，目标是把任意软件项目迁移为项目适配、证据驱动的 AI 协作工程。
- 公共材料只能包含通用方法和本仓库事实，不得复制参考项目的内部地址、人员、产品规则或私有源码信息。

## 仓库地图

| 路径 | 职责 |
|---|---|
| `SKILL.md` | 自动发现、核心边界、迁移路由和交付要求 |
| `agents/openai.yaml` | UI 元数据与默认调用示例 |
| `scripts/audit_project.py` | 无第三方依赖的只读仓库画像 |
| `references/` | 迁移流程、材料内容契约与接受度指南 |
| `tests/` | 审计脚本的行为测试 |

## 修改原则

- 保持技能描述精确，避免吸引普通功能开发任务。
- `SKILL.md` 只保留所有迁移都需要的决策规则；条件性细节进入 `references/`。
- 审计脚本必须只读、不跟随符号链接、不执行目标仓库脚本、不输出凭据或文件内容。
- 新增固定要求前说明它避免的真实失败；优先项目适配，不累积针对单个案例的万能规则。
- README 面向使用者解释问题、功能、安全边界、证据和安装方式，不能把流程数量当价值。

## 验证

```powershell
python -m unittest discover -s tests -v
python scripts\audit_project.py --root . --format json
python "$env:CODEX_HOME\skills\.system\skill-creator\scripts\quick_validate.py" .
git diff --check
```

`quick_validate.py` 只用于技能开发；公共用户不依赖该脚本运行技能。

## Git 与发布

- 使用标准 Conventional Commits，标题说明单一意图。
- 不提交缓存、临时审计输出、凭据或本机绝对路径。
- commit、push、创建仓库、发布或改变可见性需要用户明确授权。
- 最终回执区分本地验证、GitHub CI、未执行项和人工判断。
