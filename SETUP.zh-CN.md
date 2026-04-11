# 安装说明

**中文** | [English](./SETUP.md)

这份文档提供一个可直接照着走的安装路径，帮助你把仓库里的 skill 跑起来。

## 1. 克隆仓库

```bash
git clone https://github.com/ursulalujun/auto-academic-blogger.git
cd auto-academic-blogger
```

## 2. 安装 Python 依赖

这些辅助脚本依赖几个 Python 包：

```bash
python3 -m pip install --user PyMuPDF Pillow pypdf
```

它们分别用于：

- PDF 渲染
- PDF 文本提取
- 图片 contact sheet 和素材生成

## 3. 把 Skill 链接到 Codex

如果你通过 `$CODEX_HOME/skills` 使用本地 skill，可以把需要的目录做成 symlink。

示例：

```bash
ln -sfn /path/to/auto-academic-blogger/skills/arxiv-paper-screener ~/.codex/skills/arxiv-paper-screener
ln -sfn /path/to/auto-academic-blogger/skills/huggingface-weekly-paper-digest ~/.codex/skills/huggingface-weekly-paper-digest
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-post-preparer ~/.codex/skills/xiaohongshu-post-preparer
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-image-note-publisher ~/.codex/skills/xiaohongshu-image-note-publisher
```

## 4. 准备本地输出目录

这个仓库默认把生成结果放在类似下面的工作目录里：

```text
./daily_paper
```

如果你使用别的目录结构，可以在 prompt 或脚本参数里改掉输出路径。

## 5. 小红书发布相关浏览器设置

小红书发布流程依赖 macOS + Safari。

需要满足：

- 使用普通 Safari 窗口
- 在 [小红书创作服务平台](https://creator.xiaohongshu.com) 保持登录
- 发布过程中不要把创作中心相关页面关掉

Safari 里需要打开：

- `Allow JavaScript from Apple Events`

如果菜单没显示，通常要先：

1. 打开 Safari 的 Develop 菜单
2. 再启用 `Allow JavaScript from Apple Events`

## 6. macOS 权限

根据你的环境，可能需要给 Terminal 或 Codex 打开这些权限：

- Automation
  - 让 Apple Events 可以控制 Safari
- Screen Recording
  - 让脚本可以抓预览截图

## 7. 单篇论文帖查重日志

单篇论文解析帖依赖两个日志文件：

- `daily_paper/xiaohongshu_single_paper_log_full.json`
- `daily_paper/xiaohongshu_single_paper_dedup_index.json`

发布 skill 会在发单篇帖之前查重，发布成功后自动更新这两个文件。

## 8. 建议先做一次安全测试

建议先跑一遍 dry run，而不是直接发真实帖子：

1. 准备一篇单篇论文 markdown
2. 用 `xiaohongshu-post-preparer` 准备素材
3. 用 `xiaohongshu-image-note-publisher` 的预览模式先停在发布前

这样可以先验证：

- 标题和正文长度
- 图片上传顺序
- 预览渲染结果
- 浏览器权限是否正常

## 9. 常见可自定义项

你大概率会根据自己的需求去改这些地方：

- arXiv 检索关键词
- 机构白名单
- 输出目录
- 发帖文风
- 标题规则

这些内容大多都放在对应的 skill 目录里，默认就是可修改的。
