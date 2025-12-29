# 这个开源插件帮助我从 Arc 迁移到 Chrome

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOZEia34rq0nRjcGkfB2yukmyZEn2ibaJfJazcoMAmuVYzLQxiaNl0Aa4F1eibB2vA6hJkOav9RoIanSJQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

**一个旨在提高浏览器标签页效率的 Chrome 扩展，灵感来源于 Arc 浏览器。**

今天给大家带来我的第三个开源项目 chrome-tabboost，也是我第一个正式上架 Chrome Webstore 的浏览器插件。

https://github.com/samzong/chrome-tabboost

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOZEia34rq0nRjcGkfB2yukmyMxav3FtTKjicCTO0iaCD3lnwgB9EgsicsvxNXkuRa7z2ibLfZvWeQ9iaVUA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

你可以在 Chrome 插件商店快速安装 TabBoost，也可以下载插件源码在本地加载。一般情况下 Github 的更新快，Chrome 审核会慢些。

https://chromewebstore.google.com/detail/tabboost/pnpabkdhbbjmahfnhnfhpgfmhkkeoloe

**01**

**缘起**

我在 2023 年 7 月分享过一个浏览器 Arc Browser，相信不少的朋友也用过，此后 1 年多也一直在使用 Arc，算是早期内测阶段的用户。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

与此同时，我作为一名长期 Google 产品的用户，Google 账号多端同步一直是我主要使用的功能；Arc 中的一些独特设计，尤其是针对用户体验的细节优化，非常打动我，所以经常需要切换两者。在经历频繁切换的痛楚之后；2025 年元旦假期，我决定将我在 Arc 中最常用的功能复刻到 Chrome 上。

在一开始，我将目标瞄准在了 快速复制当前标签页 和 快速复制当前网页网址 这两个比较简单的功能上。完成后体验非常好。本着希望造福更多用户的淳朴想法，我决定玩个大的：上架到 Chrome Webstore。

**02**

**功能介绍**

TabBoost 定位是汲取 Arc 的惊艳用户体验，将其在 Chrome 中实现；目前主要关注在 Tab 场景，当前提供的主要功能有：

- _v1.0_
  - 快速复制当前标签页，快捷键 CMD/Ctrl + M
  - 快速复制当前标签页网址到剪切板，快捷键 CMD/Ctrl + Shift + C
- _v2.2_
  - 外链网页内弹窗展示，快捷键 CMD/Ctrl + 点击外链
  - 外链网页内分屏展示，快捷键 CMD/Ctrl + Shift + 点击外链
  - 上架到 Chrome Webstore
- _v2.3_ CMD/Ctrl + S 快捷键拦截，避免误触浏览器保存，支持国际化
- _v2.4_ 🔥 **升级 iframe 技术方案**，实现 **100%** 弹窗/分屏成功

快速复制当前标签页 和 快速复制当前网页网址 这两个功能比较简单，这里不赘述，大家可以自行体验下，也支持自定义快捷键。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**🔥** **2.1** **当前页弹窗 - POPUP**

在 Arc 中，按住 Command 然后去点击网页中对应的超链接文本，此时 Arc 会采用弹窗预览的形式，这样就不用离开当前网页。而在 Chrome 中是新开页的方式，当 Tab 和 Window 比较多，重新找到之前的 Tab 比较麻烦。

TabBoost 带来的体验与 Arc 一致，点击链接会在当前页面弹窗的形式出现，滚动查找等浏览器原生属性也保留。使用快捷键 CMD/Ctrl + 点击链接文本

- 若需要新开页可以点击右上角 Open In New Tab 打开

- 若不需要查看，支持快捷键 Esc 一键关闭，继续浏览

- 并且弹窗支持配置大小，默认 80%，可选配 90%，或自定义窗口大小

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**🔥** **2.2** **当前页分屏 - SplitView**

**Arc** 另一个非常重要的体验优化是分屏查看；如下方的效果，对经常需要用多 Tab 的用户还是非常友好的。而 Chrome 下多数的分屏工具，都是基于当前电脑屏幕将 2 个 Tab 快速布局，缺点就是 2 个 Tab 在切换后无法同时恢复。

TabBoost 现在也将这个分屏能力带到了 Chrome ，实现了单 Tab 快速一分为二的能力。使用快捷键 CMD/Ctrl + Shift + 点击链接文本。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**技术说明**

弹窗和分屏的技术实现是基于 iframe 完成，在 v2.4.0 之前，是基于网页响应体中的 X-Frame-Options 和 CSP 来判断是否可以进行弹窗和分屏，成功率较低。

五一期间研究了 _Manifest V3_ 提供的 declarativeNetRequest API 能力，支持在响应体中将 iframe 的限制移除，实现了基本 100% 的 iframe 效果。

目前该版本还在 Chrome 审核中，强烈建议从下方源码下载的方式体验，也可以等待审核通过再体验（更新：已审核通过）。

**03**

**Chrome Webstore**

自从 _v2.0_ 版本上架到 Chrome Webstore 之后，已经陆续有些用户使用了，也是我这里发出来跟大家分享的主要原因，欢迎大家来体验。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

发现除了我推荐的朋友之外，有不少其他国家的人也在使用，所以我在最近的版本中，一口气增加了 10 种语言的国际化（利用 Chrome 翻译）。

**04**

**安装方法**

直接在 Chrome/Edge(应该也可以) 插件市场搜索 TabBoost。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

Github 下载 Release 源码，然后 Chrome 插件启用开发者模式，加载解压缩的插件源码目录：

https://github.com/samzong/chrome-tabboost/releases

> 国内下载加速

https://github.abskoop.workers.dev/https://github.com/samzong/chrome-tabboost/releases/download/v2.4.0/chrome-tabboost-v2.4.0.zip

**05**

**后续发展**

TabBoost 从开始开发到现在经历了小半年，我作为用户也深度使用了小半年，目前从主要功能上已经满足了我的日常使用，也会逐渐趋于稳定。

但绝非意味着 TabBoost 目前是一款成熟且完善的插件，后续还有不少要优化的，如对分屏的增强，动态拖动分屏比例，上下分屏，三分屏等。

欢迎大家的体验并反馈，如果你有更好的建议，请一定联系我。

如果你对一个产品经理如何做到这些的事情有兴趣，或希望了解这背后是如何实现的？欢迎关注我的公众号。

如果你对我其他的开源项目感兴趣，可以直接点开下面的文章继续查看。

- 🔥 [一个效率 x10 的开源 Markdown 命令行工具](https://mp.weixin.qq.com/s?__biz=MzIzOTY3MTExMQ==&mid=2247483691&idx=1&sn=8b6a7d47044d68394ee7a20dd6678c99&scene=21#wechat_redirect)
- 🔥 [我开源了一个音乐播放软件工具](https://mp.weixin.qq.com/s?__biz=MzIzOTY3MTExMQ==&mid=2247483678&idx=1&sn=2cc5a1d74629ead351f0875c3499e394&scene=21#wechat_redirect)
