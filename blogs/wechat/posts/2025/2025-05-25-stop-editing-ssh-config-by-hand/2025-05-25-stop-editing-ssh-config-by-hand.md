# 不会吧？你还在手动编辑 ~/.ssh/config？

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOZicFEePShjJGpuMjvMclYvxtTelnEaJyI45J5Vezia4Q3g4RwE2fsjqwDW7Wdg7RQPOvvQ9jmJAoUQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

一个简单高效的 SSH 和 Kuberenetes 连接管理工具

在实际工作中经常需要远程服务器和 Kubernetes，对于我这种 CLI 选手，不太喜欢一些图形化工具，尤其是工具之间会有不兼容和迁移成本的问题。但当服务器和集群的数量多了之后，通过编辑文本的方式管理连接信息，非常不方便且容易出错。

所以，我打造了 ConfigForge，一个专为 macOS 用户设计的开源 SSH 和 Kubernetes 连接管理工具。

https://github.com/samzong/configforge

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOZicFEePShjJGpuMjvMclYvxUHT213UV6DYOia5zhTzTyzVElazX8U5VtT6WmGqOOWXLa0ZgbTZRZhQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

**ConfigForge** 的**核心不是接管你的终端**，而且提供更优的连接信息的管理形式。

**01**

**核心功能**

**1.1 UI 配置管理**

![Image](https://mmbiz.qpic.cn/sz_mmbiz_gif/tvXQtzDNVOZicFEePShjJGpuMjvMclYvxdRck2AJY41G0aqTAoK14QrhPM2tSD774gJwn8mOwGy434K8daFVVyQ/640?wx_fmt=gif&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

ConfigForge 为管理 `~/.ssh/config` 文件提供了图形界面，具有以下关键特性：

- 可视化界面 用于查看和编辑 SSH 配置条目

- 搜索和排序 功能，快速定位特定的 SSH 连接

- 基于表单的编辑 无需手动编写复杂的 SSH 配置语法

- 一键终端连接 直接从应用程序连接到 SSH 主机

对于 Kubernetes 用户，ConfigForge 提供：

- 配置文件浏览 查看和管理多个 kubeconfig 文件
- 一键切换 在不同的 Kubernetes 配置之间切换，并自动备份
- 内置编辑器 用于修改 kubeconfig 文件内容
- 配置验证 确保文件格式正确

**1.2 命令行界面**

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

ConfigForge 包含一个名为 **`cf`** 的综合 CLI 工具，提供对相同功能的终端访问：

- SSH 操作 从终端列出和连接到 SSH 主机

- Kubernetes 管理 查看和切换上下文

- 无缝集成与桌面应用程序共享相同的配置数据

CLI 采用子命令结构处理 SSH 和 Kubernetes 操作，使用 Swift Argument Parser 进行命令处理。

`cf` 默认是 `ssh` 子命令，实现快速 SSH 连接到服务器：

```
(base) x in ~ λ cf lAvailable SSH hosts:  1. *  2. blog  3. sf  4. dev-156
Use 'cf c <number>' or 'cf c <hostname>' to connectUse 'cf s <number>' or 'cf s <hostname>' to show details(base) x in ~ λ cf c 2Connecting to 2. blog...
Welcome to Alibaba Cloud Elastic Compute Service !
```

`cf` 提供了查看多 kubeconfig 的方式，实现了快速切换当前的 K8s 连接信息。

```
(base) x in ~ λ cf k -hOVERVIEW: Manage Kubernetes configurationsCommands for managing Kubernetes contexts and configurationsUSAGE: cf kube <subcommand>OPTIONS:  -h, --help              Show help information.SUBCOMMANDS:  current, cur            Show current active Kubernetes configuration  list, ls, l             List all Kubernetes configurations  set                     Set the active Kubernetes configuration  See 'cf help kube <subcommand>' for detailed help.(base) x in ~ λ cf k lAvailable Kubernetes configurations:* 1. card4090-1year-kubeconfig.yaml (active)  2. new-config-5-16-25,_13-18.yamlUse 'cf k set <number>' or 'cf k set <filename>' to switch configurationUse 'cf k current' to show current active configuration(base) x in ~ λ cf k set 2Selected configuration 2: new-config-5-16-25,_13-18.yamlSuccessfully switched active Kubernetes configuration to 'new-config-5-16-25,_13-18.yaml'
```

**02**

**如何使用**

目前应用基于 Homebrew 分发，同时提供了适配 M 系列和 Intel 芯片的 2 个版本。

```
brew tap samzong/tapbrew install configforge
```

> **如果工具对你来说有用，欢迎\*\***点个 Star\***\*，超过** **30 个\*\***就可以推送到 Homebrew 主仓库。\*\*

不是苹果开发者，所以没签名，首次启用会提示文件损坏，使用如下命令激活即可。

```
xattr -dr com.apple.quarantine /Applications/ConfigForge.app
```

为什么不支持 Windows ？

1.  Windows 几乎都是使用图形化工具为主，所以用户需求不大

2.  我不知道怎么写 Windows 的应用，最近尝试做使用跨平台的应用（Electron）

**03**

**写在最后**

_为什么选择开源？_

ConfigForge 管理的是**核心的服务器和 Kubernetes 的连接信息**，如果没有确保足够的用户隐私和透明度，我自己都不敢用，所以所有代码都可公开审查。
