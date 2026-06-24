# Svenstar Skills

这是我的个人 skill 仓库。

用途：

- 存放我长期维护的 Codex / agent skills
- 通过 GitHub 做跨机器同步和备份
- 作为未来新增、调整、归档 skill 的统一入口

这个仓库默认按“自用”维护，不以对外分发为目标。

## 目录结构

```text
skills/
  <skill-name>/
    SKILL.md
    scripts/
    assets/
    references/
```

约定：

- 每个 skill 使用独立目录
- `SKILL.md` 是入口文件
- `scripts/` 放可复用脚本
- `assets/` 放模板、图片或静态资源
- `references/` 放说明文档、参考资料或补充指引

并不是每个 skill 都必须包含所有子目录，只保留实际需要的部分。

## 新增 Skill 约定

新增 skill 时尽量保持以下规则：

- 目录名使用稳定、清晰的英文 slug
- skill 说明优先写清触发场景、边界和执行规则
- 能脚本化的编辑尽量脚本化，减少手工改动
- 优先复用已有模式，不随意发散目录结构

## Git 约定

- 本仓库主要用于同步和备份
- 本地缓存、虚拟环境、编辑器配置等不提交
- 大文件、敏感信息、临时调试产物不进入仓库

## 当前 Skills

- `svenstar-workflow-installer`

