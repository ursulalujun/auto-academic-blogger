# 使用教程

**中文** | [English](./TUTORIAL.md)

这份教程演示的是：安装好 skill 之后，怎么通过 prompt 触发 skill，并完成一整套学术分享帖子的整理和发布流程。

重点是实操：

1. 用什么 prompt 触发 skill
2. prompt 里可以控制哪些参数
3. 怎么先预览再发布
4. 怎么避免单篇论文帖重复发布

## 开始前

请先确保你已经：

- clone 了仓库
- 把需要的 skill 链接到了 `$CODEX_HOME/skills`
- 按 [SETUP.zh-CN.md](/Users/ursula/Documents/Playground/academic_blogger/SETUP.zh-CN.md) 装好了依赖
- 如果要发小红书，已经在 Safari 登录了创作中心

## 主要会用到的 Skill

和学术分享帖子最相关的，一般是这三步：

1. 找论文
   - `arxiv-paper-screener`
   - 或 `huggingface-weekly-paper-digest`
2. 整理帖子
   - `xiaohongshu-post-preparer`
3. 发布帖子
   - `xiaohongshu-image-note-publisher`

## 怎么在 Prompt 里触发 Skill

最简单的方式，就是在 prompt 里直接点名 skill。

示例：

- `用 $arxiv-paper-screener 检索最近一个月的 spatial intelligence 论文`
- `用 $huggingface-weekly-paper-digest 整理 2026-W15 的 HF daily papers`
- `用 $xiaohongshu-post-preparer 把这 6 篇论文整理成小红书单篇解析帖`
- `用 $xiaohongshu-image-note-publisher 发布刚才准备好的单篇论文帖`

不需要每次都把所有细节说满，但这几个信息通常很有帮助：

- 要用哪个 skill
- 输入是什么
- 输出写到哪里
- 是总览帖还是单篇论文解析帖
- 是先预览还是直接发布

## Prompt 里可以控制哪些参数

下面是最常用、也最值得在 prompt 里明确说出来的参数。

## `arxiv-paper-screener`

常用参数：

- `field`
- `time window`
- `max results`
- `output directory`

示例：

```text
用 $arxiv-paper-screener 检索 spatial intelligence 方向 2026 年 3 月的 arXiv 论文，
最多保留 20 篇，输出到 /Users/ursula/Documents/Playground/daily_paper/arxiv_march
```

另一个示例：

```text
用 $arxiv-paper-screener 检索最近 30 天的 world model 论文，
按 skill 里的机构规则筛选，输出 markdown 和 json
```

## `huggingface-weekly-paper-digest`

常用参数：

- `week id`
- `themes`
- `output directory`
- 是否给 top paper 写单独分析

示例：

```text
用 $huggingface-weekly-paper-digest 整理 2026-W15 的 Hugging Face daily papers，
主题分成 spatial intelligence、agent、world model，
输出到 /Users/ursula/Documents/Playground/daily_paper/2026-W15
```

## `xiaohongshu-post-preparer`

常用参数：

- `post type`
  - `总览帖`
  - `单篇论文解析帖`
- 来源论文或来源 markdown
- 输出目录
- 只准备素材，还是同时整理文案和素材
- 标题规则
- tag 风格

总览帖示例：

```text
用 $xiaohongshu-post-preparer 把这周的 spatial intelligence 论文整理成小红书总览帖，
先写正文再定标题，标题控制在 20 字以内，
使用文字生成图片作为封面，
并给每篇论文准备 arXiv PDF 首页截图，
输出到 /Users/ursula/Documents/Playground/daily_paper/2026-W15
```

单篇论文帖示例：

```text
用 $xiaohongshu-post-preparer 为 OmniRoam 整理一篇小红书单篇论文解析帖，
按 HF upvote / PDF / 代码 / 问题 / 背景 / 动机 / 方法 / 启发 的结构写，
保留 emoji 小标题，保持客观口吻，不使用第一人称，
正文写完后再定标题，
标题要以方法名开头，并尽量概括整篇解析，
输出到 /Users/ursula/Documents/Playground/daily_paper/arxiv_march/spatial-intelligence
```

你可以在 prompt 里继续细化这些要求：

- 正文结构
- 标题风格
- 是否保留 emoji 分段
- 是否加 `#topic` 标签
- 是否保持客观口吻
- markdown 保存路径
- 图片素材保存路径

## `xiaohongshu-image-note-publisher`

常用参数：

- 是直接发布还是停在发布前
- `post type`
- 用于查重的原始论文标题
- markdown 路径，或直接给 title/body
- cover 图片路径
- 可选的第二张图路径
- 总览帖用的 `cover_text`

先预览的示例：

```text
用 $xiaohongshu-image-note-publisher 打开小红书发布页面，
加载这篇单篇论文解析帖，
先不要发布，停在预览页等我确认。
论文原始标题是 OmniRoam: World Wandering via Long-Horizon Panoramic Video Generation，
markdown 在 /Users/ursula/Documents/Playground/daily_paper/arxiv_march/spatial-intelligence/xhs_single_01_omniroam.md
```

正式发布的示例：

```text
用 $xiaohongshu-image-note-publisher 发布刚才确认过的 OmniRoam 单篇论文帖，
发布前先查重，
如果之前已经发过就不要重复发布，
发布成功后更新 single-paper log
```

## 完整流程示例

## 示例 A：总览帖

目标：把一周的论文整理成一篇小红书总览帖。

### Step 1：整理 weekly digest

```text
用 $huggingface-weekly-paper-digest 整理 2026-W15 的 HF daily papers，
聚焦 spatial intelligence、agent、world model，
输出到 /Users/ursula/Documents/Playground/daily_paper/2026-W15
```

### Step 2：整理成总览帖

```text
用 $xiaohongshu-post-preparer 把 W15 的 spatial intelligence 论文整理成一篇小红书总览帖，
列出全部论文并按 upvote 排序，
最后再写总结，
标题 20 字以内，
使用文字生成图片作为封面，
并准备每篇论文的 arXiv PDF 首页截图
```

### Step 3：先预览

```text
用 $xiaohongshu-image-note-publisher 把刚才的总览帖填到小红书创作中心，
先不要发布，停在预览页让我看一下
```

### Step 4：确认后发布

```text
用 $xiaohongshu-image-note-publisher 发布刚才确认过的总览帖
```

## 示例 B：单篇论文解析帖

目标：把一篇论文从检索一路整理到可发布状态。

### Step 1：先筛论文

```text
用 $arxiv-paper-screener 检索 2026 年 3 月的 spatial intelligence 论文，
最多保留 20 篇，输出到 /Users/ursula/Documents/Playground/daily_paper/arxiv_march
```

### Step 2：整理单篇解析帖

```text
用 $xiaohongshu-post-preparer 为 MV-RoMa 整理单篇论文解析帖，
按 skill 里的单篇模板写，
方法和动机尽量详细，
标题先不要抢写，等正文完成后再定，
封面优先用 HF paper 首页，
如果没有 HF 就用 arXiv PDF 首页，
再检查首页是否已经包含 teaser figure，
如果没有再补第二张 teaser 图
```

### Step 3：停在预览页，不要发布

```text
用 $xiaohongshu-image-note-publisher 打开小红书发布页并填好 MV-RoMa 这篇帖子，
这是单篇论文解析帖，
原始论文标题是 MV-RoMA: Multi-View Reconstruction-Oriented Matching Anything，
发布前先查重，
停在预览页，不要发布
```

### Step 4：正式发布并登记日志

```text
用 $xiaohongshu-image-note-publisher 发布刚才预览过的 MV-RoMa 单篇帖子，
发布成功后把链接写回 single-paper log
```

## 可以直接复用的 Prompt 模板

## 模板 1：检索论文

```text
用 $arxiv-paper-screener 检索 <领域> 方向 <时间段> 的 arXiv 论文，
最多保留 <N> 篇，输出到 <输出目录>
```

`<时间段>` 可以写成：

- `最近 7 天`
- `最近 30 天`
- `2026-03`

## 模板 2：整理一周论文

```text
用 $huggingface-weekly-paper-digest 整理 <week id> 的 Hugging Face daily papers，
聚焦 <theme1>、<theme2>、<theme3>，
输出到 <输出目录>
```

## 模板 3：整理总览帖

```text
用 $xiaohongshu-post-preparer 把 <论文集合> 整理成小红书总览帖，
正文先写完再定标题，
标题控制在 20 字以内，
使用文字生成图片作为封面，
并准备每篇论文的 arXiv PDF 首页截图，
输出到 <输出目录>
```

## 模板 4：整理单篇论文帖

```text
用 $xiaohongshu-post-preparer 为 <论文名> 整理单篇论文解析帖，
按 HF upvote / PDF / 代码 / 问题 / 背景 / 动机 / 方法 / 启发 的结构写，
保留 emoji 小标题，
加 #topic 标签，
保持客观口吻，
正文写完后再定标题，
标题以方法名开头，并尽量概括整篇解析，
输出到 <输出目录>
```

## 模板 5：先预览再说

```text
用 $xiaohongshu-image-note-publisher 打开小红书发布页面并填入准备好的内容，
先不要发布，停在预览页让我确认
```

## 模板 6：安全发布单篇论文帖

```text
用 $xiaohongshu-image-note-publisher 发布这篇单篇论文解析帖，
论文原始标题是 <paper title>，
发布前先查重，
如果已经发过就直接告诉我链接，
如果成功发布，就把结果登记到 single-paper log
```

## Prompt 里哪些信息最值得明确写出来

如果任务本身有歧义，这几项尤其建议显式写出来：

- 具体领域名
- 具体月份或滚动时间窗口
- 输出目录
- post type
- 论文原始标题
- 是只预览还是要真实发布
- 是否属于单篇论文帖并需要查重

如果你不写，Codex 有时也会从工作目录里猜出来，但想要稳定复现时，明确写出来会更稳。

## 推荐先跑一次完整但安全的测试

比较稳的首轮测试方式是：

1. 先跑 `arxiv-paper-screener`
2. 再用 `xiaohongshu-post-preparer` 整理一篇单篇论文帖
3. 用 `xiaohongshu-image-note-publisher` 进入预览模式
4. 手动检查 Safari 里的预览
5. 确认后再真实发布

这一轮会覆盖整条链路：

- 检索
- 写文案
- 准备素材
- 预览
- 查重
- 发布
- 更新日志
