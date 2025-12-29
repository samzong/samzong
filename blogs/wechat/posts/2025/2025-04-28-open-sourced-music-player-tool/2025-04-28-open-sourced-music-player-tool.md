# 我开源了一个音乐播放软件工具

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVObQickqknx76W8ejcK12EAXjSrcHS8oTC535BtUMibBYwLNhbFaEjftnYKyCC6xUeseuLuZ9Uic3AqrQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

**A clean, lightweight music player for macOS.**

**今天**，终于可以正式地分享下，我的一个小玩意儿～

https://github.com/samzong/macmusicplayer

一直以来，选择一款合适的音频工具对我来说都是个麻烦事儿，折腾过各类付费音乐平台、开源工具，总有些感觉差强人意的地方：

1.  主流音乐平台的软件中有大量无关的功能，如社交，皮肤等。
2.  几款开源的基本都需要考虑跨平台基于 RN 开发，性能问题。
3.  需要账户、离线支持不完善。

**01**

去年年底，我就在想要不自己做一个吧～

于是，我开始认真思考用户（我）需求是什么？

一款**纯离线**、**极简、MacOS 原生开发**的音频工具，**MacMusicPlayer** 就这么诞生了 （不花钱也是需求之一）

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVObQickqknx76W8ejcK12EAXjHKt7rEQFq1fflzLmgoiazG4eqAdq1dN4bz1fCCbjTcEOtKqA47gplibg/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

功能介绍

**MacMusicPlayer** 发展的三个阶段：

- v0.1 实现最基础的核心功能
- v0.2 支持多音乐库、均衡器模式、集成 yt-dlp 下载功能
- v0.3 集成 yt-search-api 支持在线搜索音乐

**02**

**功能介绍**

**1.** **播放器核心功能** 就是播放功能，首次安装会提示选择本地音频文件夹，默认是在 Music 目录，之后添加到该目录的 .mp3 文件会自动识别。

- 支持音乐播放/暂停，上一首、下一首
- 支持列表随机、单曲循环、顺序播放的播放模式
- 适配系统媒体控制键，可搭配任意有线、无线耳机，支持第三方适配
- 支持音频通道占用后的自动暂停及自动恢复播放

**2.** **多音乐库管理** 的背景是需要给我家娃播放音乐听以及如何简单支持不同歌单的需求，实现原理上是对应到系统的不同文件夹的方式。

- 默认安装会自动创建一个音乐库，支持创建不限数量的音乐库

- 支持自定义音乐库路径

- 支持音乐库重命名功能

- 支持实时切换音乐库，自动识别新列表播放

- 支持下载音乐时，指定音乐库功能

**3.** **均衡器** 的功能来源于我收藏了一部分钢琴曲、大提琴的歌曲；希望增加一个高中低音调节的功能，顺便也增加一些预设模式。（不过这个功能用得比较少，并未仔细打磨）

4.  **保持系统唤醒** 的功能其实有不少工具，实现并不复杂，这个是最早期增加的功能，主要是希望减少 MacOS MenuBar 的常驻图标数量，就内置了。

**03**

**下载音乐**

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**v0.1** 的时候是不想做音乐下载的，只想做一个纯粹的播放器，后续来实际体验中发现下载音乐有点麻烦，经常需要在终端内执行 yt-dlp 的命令，不是很方便。

在 **v0.2** 时第一个增加的功能就是集成 yt-dlp。只需要在窗口中输入音乐地址，就可以直接下载并加载到播放列表；依托于 yt-dlp 强大的网站适配能力，支持非常多的网站。

> 有兴趣的可以去看下： https://github.com/yt-dlp/yt-dlp/

但是在使用过程中发现，每次都需要打开 bilibili 或 Youtube 找到对应的视频链接。

所以，在 **v0.3** 时最大的改进，集成了通过关键字搜索并下载的功能。

但是，在 UI 交互之中仍旧保持克制；用了一个巧妙的方式，复用了已有的地址输入框，**动态检测是直接解析链接还是走关键词搜索**。

而在搜索能力实现上，开始尝试了 yt-dlp 的搜索功能的方式，但是有点慢。最后，我选择了更快的官方 API，并将检索的能力剥离出来实现了独立的 yt-search-api。

> yt-search-api 是我的另外一个项目，以后可以单独介绍

**04**

**如何使用**

目前应用基于 Homebrew 分发，同时提供了适配 M 系列和 Intel 芯片的 2 个版本。

```
brew tap samzong/tapbrew install yt-dlp ffmpeg # 下载音乐brew install mac-music-player
```

安装后，首次启用会提示文件损坏，这个问题是因为目前还不是 Apple 开发者（要付钱的），所以使用如下命令激活即可。

```
xattr -dr com.apple.quarantine /Applications/MacMusicPlayer.app
```

_注： 安装 brew、 yt-dlp、ffmpeg 还是有一定的使用门槛的；如果有任何问题，欢迎联系我。_

**05**

**写在最后**

如果大家对这个项目有兴趣，也希望一起研究，欢迎联系我 ～

目前，音乐在线搜索使用 yt-search-api，我托管了一个**免费的**在线服务，只需要在 MacMusicPlayer 中配置下即可。

```
url: https://yt-search-api-stable.vercel.app
```

密钥 Key： _macmusicplayer_ e
