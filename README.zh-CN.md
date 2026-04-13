<table>
  <tr>
    <td width="110">
      <img src="./assets/logo.png" alt="论文的再现 logo" width="92" />
    </td>
    <td>
      <h1>论文的再现<br/>Echoes of Paper</h1>
    </td>
  </tr>
</table>

**中文** | [English](./README.md)

这个仓库是小红书账号 [论文的再现 / Echoes of Paper](https://www.xiaohongshu.com/user/profile/6512d3ff000000002402f626) 的运营源代码。

它把“找论文、筛论文、写分享、配图、发帖”整理成一套可复用的 workflow、skill 和辅助脚本。

仓库本身尽量保持轻量，详细说明分别放在 setup 和 tutorial 文档里。

## 包含哪些 Skill

- `arxiv-paper-screener`
  - 按领域和时间检索 arXiv
  - 按机构规则筛选
  - 按 GitHub star 或引用数排序
- `huggingface-weekly-paper-digest`
  - 把 Hugging Face 每周论文页整理成主题 digest
- `xiaohongshu-post-preparer`
  - 整理总览帖和单篇论文解析帖
  - 准备封面、PDF 首页图、teaser/framework 图
- `xiaohongshu-image-note-publisher`
  - 从 Safari 发布准备好的小红书图文帖
  - 对单篇论文帖做查重并更新发布日志

## 建议先看

- 环境和安装说明：[SETUP.zh-CN.md](./SETUP.zh-CN.md)
- Prompt 示例和完整工作流：[TUTORIAL.zh-CN.md](./TUTORIAL.zh-CN.md)

英文版本：

- [README.md](./README.md)
- [SETUP.md](./SETUP.md)
- [TUTORIAL.md](./TUTORIAL.md)

## 快速开始

1. clone 仓库
2. 按 [SETUP.zh-CN.md](./SETUP.zh-CN.md) 安装 Python 依赖
3. 把需要的 skill 链接到 `$CODEX_HOME/skills`
4. 如果要发小红书，在 Safari 登录创作中心，并打开所需权限

示例：

```bash
git clone https://github.com/ursulalujun/auto-academic-blogger.git
cd auto-academic-blogger
python3 -m pip install --user PyMuPDF Pillow pypdf

ln -sfn /path/to/auto-academic-blogger/skills/arxiv-paper-screener ~/.codex/skills/arxiv-paper-screener
ln -sfn /path/to/auto-academic-blogger/skills/huggingface-weekly-paper-digest ~/.codex/skills/huggingface-weekly-paper-digest
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-post-preparer ~/.codex/skills/xiaohongshu-post-preparer
ln -sfn /path/to/auto-academic-blogger/skills/xiaohongshu-image-note-publisher ~/.codex/skills/xiaohongshu-image-note-publisher
```

## 常见流程

1. 用 `arxiv-paper-screener` 或 `huggingface-weekly-paper-digest` 找论文
2. 用 `xiaohongshu-post-preparer` 整理文案和图片素材
3. 用 `xiaohongshu-image-note-publisher` 预览或发布

示例 prompt：

```text
用 $arxiv-paper-screener 检索最近 30 天的 spatial intelligence 论文，并保存到 ./daily_paper/arxiv_march
```

```text
用 $xiaohongshu-post-preparer 把这些论文整理成一篇小红书总览帖，先写正文再定标题，并准备每篇论文的 PDF 首页截图
```

```text
用 $xiaohongshu-image-note-publisher 把准备好的帖子填到小红书创作中心，先不要发布，停在预览页让我确认
```

## 说明

- 单篇论文帖会使用 `daily_paper/` 下的查重日志，避免重复发布。
- 发布流程基于 Safari，默认使用已经登录的普通 Safari 窗口。
- 这些 skill 本来就是为了让你按自己的领域、机构名单、写作风格和输出目录继续改的。
