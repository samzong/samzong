# 使用 Homebrew 发布自己的项目

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOb9KAxovlxyyJ0a0mBdic5PTScUicABgnTia4Tn7gVs33hmuORg4Jb6as2Qmz12ibF1J2k0G0vPooiaDBw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

Homebrew 是 macOS 上知名的包管理器，可以方便地安装、卸载、更新和列出软件包。

在 Mac 中，我所有的软件几乎都是使用 Homebrew 管理，前段时间我开发了一个 Mac 上的音乐播放器 MacMusicPlayer[1]，
在分发软件安装以及更新时，比较麻烦，我就想着提交到 Homebrew 中，方便使用。

*https://github.com/Homebrew/homebrew-core/pull/191346*

此时发现，想要发布到 Homebrew 的官方库中，需要满足 **Github Repo Star 数量大于 50** 的条件，我这个项目才刚发布，所以暂时不满足条件。

官方维护者推荐，可以先创建自己的 Tap， 先自己维护，等项目成熟了，再提交到官方库中。

## 创建自己的 Tap

然后我就创建了 https://github.com/samzong/homebrew-tap 这个仓库，
并将我自己开发的几个软件聚合到了这里，方便使用。

这篇文章记录了，如何创建自己的 Tap，以及如何管理和发布项目，如果你有兴趣可以参考。

### 项目结构介绍

```
x in ~/git/samzong/homebrew-tap on main λ tree -L 3 -a -I .git
.
├── .github
│   └── workflows
│       ├── auto-merge.yml
│       └── pr-review.yml
├── .gitignore
├── Casks
│   ├── configforge.rb
│   ├── hf-model-downloader.rb
│   ├── mac-music-player.rb
│   ├── prompts.rb
│   └── saveeye.rb
├── DEVELOPMENT.md
├── Formula
│   ├── gmc.rb
│   ├── mdctl.rb
│   └── mm.rb
├── LICENSE
└── README.md
```

- Casks 目录下是存放 GUI 软件，比如 MacMusicPlayer
- Formula 目录下是存放 CLI 软件，比如 mdctl
- x.rb 文件是软件的描述文件，比如 mac-music-player.rb
- .github/workflows/pr-review.yml 是 PR 的审核流程，目前支持校验 SHASUM 和 安装测试
- .github/workflows/auto-merge.yml 是 PR 自动 Merge ，默认会在 PR 检测 Pass 后执行

### 应用描述文件示例

```
cask "mac-music-player" do
  version "0.4.2"
  on_arm do
    url "https://github.com/samzong/MacMusicPlayer/releases/download/v#{version}/MacMusicPlayer-arm64.dmg"
    sha256 "40672f5bfa48571ecfe1ac39034dd231175e5bf30969aa1399d8e8a7fdbf6d90"
end

  on_intel do
    url "https://github.com/samzong/MacMusicPlayer/releases/download/v#{version}/MacMusicPlayer-x86_64.dmg"
    sha256 "6526ab4d8fbb8e8b0805e42d6413874308a1c096bb7024f2c707b5b0755696a9"
end

  name "MacMusicPlayer"
  desc "Simple and elegant music player"
  homepage "https://github.com/samzong/MacMusicPlayer"
  auto_updates true

  livecheck do
    url :url
    strategy :github_latest
end

  depends_on macos:">= :monterey"
  depends_on formula: ["yt-dlp", "ffmpeg"]

  app "MacMusicPlayer.app"

  postflight do
    system_command "xattr", args: ["-cr", "#{appdir}/MacMusicPlayer.app"]
end

  zap trash: [
    "/Library/Logs/DiagnosticReports/MacMusicPlayer*",
    "~/Library/Application Support/MacMusicPlayer",
    "~/Library/Caches/com.samzong.macmusicplayer",
    "~/Library/Containers/com.samzong.macmusicplayer",
    "~/Library/Group Containers/group.com.samzong.macmusicplayer",
    "~/Library/HTTPStorages/com.samzong.macmusicplayer",
    "~/Library/LaunchAgents/com.samzong.macmusicplayer.plist",
    "~/Library/Logs/MacMusicPlayer",
    "~/Library/Preferences/ByHost/com.samzong.macmusicplayer.*.plist",
    "~/Library/Preferences/com.samzong.macmusicplayer.plist",
    "~/Library/Saved Application State/com.samzong.macmusicplayer.savedState",
    "~/Library/WebKit/com.samzong.macmusicplayer",
  ]
end
```

- `url` 是软件的下载地址
- `sha256` 是软件的 SHA256 校验码
- `name` 是软件的名称
- `desc` 是软件的描述
- `homepage` 是软件的主页
- `auto_updates` 是软件是否自动更新
- `livecheck` 是版本检测，默认走 github release
- `depends_on` 是声明软件依赖的 OS 或者其他 formula
- `app` 是软件的安装路径
- `postflight` 是 Homebrew 提供的在安装后的执行指令
- `zap trash` 是软件的卸载路径

### 添加和更新应用

根据软件是 GUI 还是 CLI 软件，选择对应的目录，然后添加对应的描述文件， 建议通过 PR 的方式提交，方便审核。

## 使用 Tap 安装应用

Homebrew 提供了专门的三方库管理的能力，你可以方便添加在自己的 Mac 中。

```
brew tap samzong/tap
```

然后就可以使用 `brew install` 安装自己维护的软件了。

```
brew install mac-music-player
brew install mdctl
```

### 更新应用

Homebrew 会在更新是同步更新三方 Tap，你也可以执行 `brew update` 主动更新

如果你希望查看更新信息，可以使用如下命令

```
brew update -v
```

## 应用发布新版本时自动更新

如果每次应用发布新版本时，都需要手动更新 Tap，那将是一件非常麻烦的事情，
所以你可以在自己的应用中，添加一个自动更新 Tap 的 Workflow.

我在 MacMusicPlayer 项目中，添加了一个自动更新 Tap 的 Workflow，
当应用发布新版本时，会自动更新 Tap，并提交到 Github，方便审核。

```
# ...
    # 触发 Homebrew 更新
    -name:TriggerHomebrewUpdate
      if:success()# 只在前面的步骤都成功时才触发
      uses:peter-evans/repository-dispatch@v2
      with:
        token:${{secrets.GH_PAT}}
        event-type:trigger-homebrew-update
        client-payload:'{"version": "${{ env.VERSION }}"}'
# ...
```

- 具体实现可以参考 MacMusicPlayer Update Homebrew[2]
- 也可以维护在 Makefile[3] 中，通过 `make update-homebrew` 命令触发
- 需要自己创建一个 `GH_PAT` 的 secret，默认的 GH_TOKEN 无法跨仓库

## PR 自动合并

目前已经为 PR 增加了自动合并的 Workflow，具体的实现方式就是在 `PR Review` 任务完成后检测是否满足合并条件，没问题后通过 `github.rest.pulls.merge` 实现自动合并。

github/workflows/auto-merge.yml#L110-L119[4]

```
// Performthemergeoperation
try {
awaitgithub.rest.pulls.merge({
    owner:context.repo.owner,
    repo:context.repo.repo,
    pull_number:prNumber,
    merge_method:'merge'
  });

console.log(`SuccessfullymergedPR#${prNumber}`);
...
```

## 后续

- 增强 PR Review 的能力，目前基本是在 `macos-latest` 中运行，Homebrew 有更多和更严格的检查流程，可以继续优化
- 将合适的应用提交到官方的 homebrew-core （如有必要的话）。

#### 引用链接

`[1]` MacMusicPlayer: *https://github.com/samzong/MacMusicPlayer*
`[2]` MacMusicPlayer Update Homebrew: *https://github.com/samzong/MacMusicPlayer/blob/main/.github/workflows/update-homebrew.yml*
`[3]` Makefile: *https://github.com/samzong/mdctl/blob/main/Makefile*
`[4]` github/workflows/auto-merge.yml#L110-L119: *https://github.com/samzong/homebrew-tap/blob/main/.github/workflows/auto-merge.yml#L110-L119*
