# MacMusicPlayer v0.5 发布：探索音乐的"随便听听"

![封面图](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVObQickqknx76W8ejcK12EAXjSrcHS8oTC535BtUMibBYwLNhbFaEjftnYKyCC6xUeseuLuZ9Uic3AqrQ/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

距离上次发布 MacMusicPlayer 已经过去大半年了，这段时间我一直在悄悄地打磨这个小工具。今天，很高兴地和大家分享 **v0.5** 版本的更新。

https://github.com/samzong/macmusicplayer

**01**

**这次更新了什么？**

先说我最喜欢的新功能——**"随便听听"（Feeling Lucky）**。

用快捷键 `⌘L` 就能随机跳转到一首歌，非常适合我这种选择困难症患者。不用纠结听什么，让软件帮你决定。

**02**

**歌曲搜索窗口（Song Picker）**

播放列表里歌越来越多，找一首特定的歌变得很麻烦。现在按 `⌘F` 会弹出一个简洁的搜索窗口，实时过滤歌曲名，回车直接播放。

这个窗口的设计我花了不少心思：

- **极简交互**：打开就是搜索框，输入立即过滤
- **键盘优先**：Tab 切换、回车播放、Esc 关闭
- **深色模式适配**：跟随系统主题，看起来很原生
- **启动可选**：在设置中可以开启"启动时打开歌曲搜索窗口"

**03**

**技术升级**

这个版本在底层做了一次大重构，把播放引擎从 `AVAudioPlayer` 迁移到了 `AVQueuePlayer`。这意味着什么？

- **无缝播放**：下一首歌会预加载，切歌更流畅
- **更好的播放状态**：媒体控制键和耳机控制更加稳定
- **顺序播放循环**：播完最后一首自动回到第一首继续

代码架构也做了分离，引入了 `QueuePlayerController` 和 `PlaylistStore`，代码更易维护。

**04**

**多语言 & 更多格式**

现在 MacMusicPlayer 支持 **5 种语言**：
- 英语
- 简体中文
- 繁体中文
- 日语
- 韩语

音频格式支持也扩展了，除了 mp3 之外，还支持：
- M4A
- WAV
- FLAC
- AAC
- OGG
- AIFF

基本上常见的无损和有损格式都能播放了。

**05**

**做减法**

这个版本我移除了**均衡器（Equalizer）**功能。

说实话，这个功能我自己用得很少，而且实现得不够好。与其留着一个半成品，不如先砍掉，保持软件的简洁。

如果未来有更好的实现方案，可能会重新加回来。

**06**

**快速上手**

安装还是推荐用 Homebrew：

```
brew install samzong/tap/mac-music-player
```

如果需要下载音乐功能，还需要安装依赖：

```
brew install yt-dlp ffmpeg
```

首次启动如果提示"文件已损坏"，是因为我还没有苹果开发者证书，执行下面的命令即可：

```
xattr -dr com.apple.quarantine /Applications/MacMusicPlayer.app
```

**07**

**常用快捷键**

| 快捷键 | 功能 |
|--------|------|
| ⌘F | 打开歌曲搜索窗口 |
| ⌘L | 随便听听（随机播放） |
| ⌘D | 打开下载窗口 |
| ⌘S | 打开设置 |
| ⌘R | 刷新当前音乐库 |

**08**

**写在最后**

MacMusicPlayer 依然定位是一个**纯离线、极简的 macOS 原生音乐播放器**。

不做社交、不做皮肤、不做会员——只专注于把本地音乐播好。

项目完全开源，欢迎 Star：

https://github.com/samzong/macmusicplayer

如果有任何问题或建议，欢迎在 GitHub 上提 Issue，或者直接联系我。
