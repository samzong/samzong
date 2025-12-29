# 一个效率 x10 的开源 Markdown 命令行工具

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOarNsadiagm9iaHEia625jO0PYooEaWM76ClZzLjiaPa6azrC6WU8RpGA4j7HKt1XSr4HJx1tQRuamrqA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

**🔥 An AI-powered CLI tool to enhance your Markdown workflow。**

作为一名产品经理，日常在工作和开源参与时，有许多与文档打交道的时候。

主要打交道的是 **Markdown**；最近几年通过维护公司文档站(https://docs.daocloud.io) 的构建工作，积累一些经验。

所以，分享下我的第二款开源软件 https://github.com/samzong/mdctl ，帮您提升 10 倍效率*（玄学）*。

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOarNsadiagm9iaHEia625jO0PY5ya12jibsNQSezicGOZpaZXGPkbANFN2Tz7arqibqrPjWcPhkSrNM6sCQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

**01**

mdctl 是一个**全平台的 Markdown 命令行工具**，我最开始要做 Markdown 的批量功能时，先在 Github 找了不少，但都不太合适；然后临时使用一些 Python 脚本解决；目前可以看到现在 DaoCloud-docs 的仓库还有大量脚本存在。

偶然发现有一个叫 cobra 的构建 CLI 工具库，简单了解下来发现非常方便，所以就萌发了使用 Golang 把这些脚本的能力聚合起来的想法。

> Python 脚本在传播其他小伙伴使用太麻烦，尝试把解释器打包进去又太大...

经过小半年的打磨，mdctl 目前已经具备不少的功能。

- _v0.0.1_ 支持 downlaod，自动索引 md 文件内的远端图片地址，下载并替换。
- v0.0.2 支持 translate，利用 llm 翻译 Markdown 到多语言，适配 OpenAI 协议。
- _v0.0.5_ 适配全平台，支持使用 Homebrew 安装和升级。
- _v0.0.9_ 优化 translate 命令适配 deepseek-r1 带来的 **<think>** 模式。
- _v0.0.10_ 支持 upload，检测 md 文件中的本地图片并上传到云端 (S3 协议)。
- _v0.0.11_ 支持 export，适配静态网站构建工具 mkdocs 等，导出 Word 等格式。
- _v0.1.0_ 支持 llmstxt，利用网站 sitemap.xml 自动转为大模型友好的 llms.txt。
- _v0.1.1_ 自动构建 images, 可在 Github Action 等 CI 场景直接使用。

**02**

**功能介绍**

mdctl 已有不少(10 个以内 😂) 用户的反馈，目前终端下的使用体验还不错。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

以下是一些主要功能的介绍，可以下载来体验下。

### 🔥 1. **下载图片(download)**

```
Examples:  mdctl download -f post.md  mdctl download -d content/posts  mdctl download -f post.md -o assets/images
```

### 🔥 2. **利用大模型翻译(translate)**

```
Supported AI Models:  - OpenAI (Current)  - DeepSeek R1 (Current)  - Llama (Current)
Supported Languages:  ar (العربية), de (Deutsch), en (English), es (Español), fr (Français),  hi (हिन्दी), it (Italiano), ja (日本語), ko (한국어), pt (Português),  ru (Русский), th (ไทย), vi (Tiếng Việt), zh (中文)
Examples:  # Translate a single file to Chinese  mdctl translate -f README.md -l zh
  # Translate a directory to Japanese  mdctl translate -f docs -l ja
  # Force translate an already translated file  mdctl translate -f README.md -l ko -F
  # Format markdown content after translation  mdctl translate -f README.md -l zh -m
  # Translate to a specific output path  mdctl translate -f docs -l fr -t translated_docs
```

### 🔥 3. **上传图片到云存储(upload)**

```
# Upload images from a filemdctl upload -f post.md
# Upload images from a directorymdctl upload -d docs/
```

### 🔥 4. **导出为文档(export)**

```
# Export to DOCXmdctl export -f input.md -o output.docx -t templates/1.docx
# Export to Word with table of contentsmdctl export -d docs/ -o output.docx -F docx --toc --toc-depth 3
```

### 🔥 4. **生成 llms.txt（llmstxt)**

```
# Standard mode (titles and descriptions)mdctl llmstxt https://example.com/sitemap.xml -o llms.txt
# Full-content modemdctl llmstxt -f https://example.com/sitemap.xml -o llms-full.txt
```

**03**

**安装方法**

目前应用提供了多种使用方式:

💻 在 MacOS 可以直接使用 Homebrew 安装和更新:

```
# Installbrew tap samzong/tapbrew install mdctl
# Upgradebrew updatebrew upgrade mdctl
```

其他平台如 Linux or Windows，可以在 Github 下载构建好的安装包使用。

https://github.com/samzong/mdctl/releases

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

当然也可以通过镜像的方式使用，下方是一个在 Github Action 使用的示例

```
name: Use mdctl in GitHub Actionson:  push:    branches: [ main ]  pull_request:    branches: [ main ]  workflow_dispatch:jobs:  process-markdown:    runs-on: ubuntu-latest    container:      image: ghcr.io/samzong/mdctl:latest
    steps:      - name: Checkout code        uses: actions/checkout@v4
      - name: Run mdctl        run: |          # 直接使用 mdctl 命令，因为我们在 mdctl 容器内运行          mdctl --version
          # 示例：下载 Markdown 中的图片          mdctl download -f README.md -o images/
          # 示例：翻译 Markdown 文件          # mdctl translate -f README.md -t zh-CN -o README_zh.md
```

> 如果您感兴趣或遇到任何问题，欢迎联系我

**04**

**后续规划**

接下来的功能发展，主要以满足实际工作使用为主，同时不断优化当前的能力。

- 集成 markdown-lint 的实现自动语法修复的能力
- 支持扫描翻译国际化文档的翻译进度

另外在功能设计也有了一些扩展点，如果有兴趣一起开发，也可以针对需要进一步扩展：

- internal/storage/ 中增加新的云端存储，只需要实现一个 Provider 即可。
- internal/translator/ 也可以很方便增加新的模型调用方，比如 Gemini。
- internal/exporter/sitereader/ 扩充其他静态网站构建工具，如 Hugo 等。
