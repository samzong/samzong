# 不会 PS 也能做图标？这个 AI 助手太香了！

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOYLBmYo2dYDYyq5lehbyvl6cpI9jg6FU9zDpNC7p8pYbGQs9SPeKoIbETD6bvogBpaGOtHuAdaY4Q/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=0)

随着搞的开源项目多起来之后，逐渐有一个头疼的事情，就是**给应用搞一个 Logo**，找了不少生成工具，要么费钱，要么需要一些设计基础；都不不是很顺手。

有一天突发奇想，现在大模型生图还是很方便的，能不能用 AI 搞一个图标生成器，直接生成一个图标。 这个项目就是诞生在这个背景之下。

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOYLBmYo2dYDYyq5lehbyvl6wtib6ckso87wDFdCGtH1IWmHPgLvaDRwzor1jKTRSr5NqvhYyaUlQoA/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=1)

An opensource icon generation tool based on LLMs.

项目地址：https://github.com/samzong/ai-icon-generator

展示下目前生成的图标 logo （清一色都是开源项目）：

![Image](https://mmbiz.qpic.cn/sz_mmbiz_png/tvXQtzDNVOYLBmYo2dYDYyq5lehbyvl6LotsauCSXAU3hXYic2N51qYbEubIFdCNFEL93x60tST1Dgbx64MdicSw/640?wx_fmt=png&from=appmsg&tp=webp&wxfrom=5&wx_lazy=1#imgIndex=2)

以上项目还有不少在实现中，有兴趣的可以关注我的 Github 账号

现在的流程就是先在 ai-logo-generator 生成一个满意的图标后，然后用 Figma 微调下就可以 （以 Tabboost 为例）

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**01**

功能介绍

一开始是基于 free-dall-e-proxy 使用免费 OpenAI 的 DALL-E。

https://github.com/Feiyuyu0503/free-dall-e-proxy

最近增加了多 LLM Backend 的选择，如果自己配置 LLM Backend 则所有调用均在本地，不会上传到云端，保证隐私安全。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

1.  使用起来非常的简单直接，比如你想要一个音乐播放器图标，就可以直接自然语言描述你想要的图标， AI 就能理解并生成，不需要复杂的操作。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

2.  提供了多种多样的样式选择，比如扁平化，3D 等快捷选择。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

3.  支持多种格式导出，常见的 PNG，JPEG，同时还支持 ICO，ICNS ；还可以选择导出背景以及是圆角，矩形亦或者圆形，所以无论是在网页，还是 App 应用都可以有合适的格式。
4.  自动保存生成的历史，多次生成后直接对比，避免浪费 API 调用。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

5.  支持自定义大模型的 API 后端和密钥，完全保存在浏览器本地，无需担心隐私安全。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

6.  一些基础能力，比如国际化支持。

**02**

部署方式

**01 在线体验**

我在 Vercel 长期托管了一个在线服务（免费），提供一定量的免费 Token 额度，用于方便大家快速体验。

https://ai-icon-generator-fawn.vercel.app/

支持一键部署到 Vercel ，你可以很方便的部署自己的 Vercel 平台 ，我在 READEME.md 放了一键部署按钮，感兴趣的可以点击下。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**02 本地部署**

支持 docker 部署，分分钟就可以有一个自己的图标生成服务。

```
# 拉取最新镜像
docker pull ghcr.io/samzong/ai-icon-generator:latest

# 运行容器
docker run -d -p 3000:3000 \
  -e OPENAI_API_KEY=your_api_key \
  ghcr.io/samzong/ai-icon-generator:latest
```

支持基础的限流能力，如果你希望开放给其他人使用，那么有个限流还是不错的，添加环境变量即可。

```
# OpenAI
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE_URL=https://api.openai.com/v1

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Rate Limiting
MAX_REQUESTS_PER_HOUR=50

# Image Size
DEFAULT_IMAGE_SIZE=512
MAX_IMAGE_SIZE=1024
```

**03**

🔥 hidream-i1-dev 免费体验

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)

**D.run 大模型服务平台**提供了 hidream-i1-dev 的 MaaS 服务，有兴趣的可以去体验下，多一个途径：

https://console.d.run

可以注册然后通过公众号消息联系我，获取 **50 元优惠券**（大概可以生成 100 张 logo 图片。

**04**

写在最后

目前 ai-icon-generator 基本满足我在搞新应用时对 logo 的需求了，算是觉得还可以拿出来分享给大家。

这也是我尝试利用 Cursor 这类工具 Vibe Conding 的全新体验，找机会给大家分享下我的使用体验，总之大模型还是很强的。

> > 我的其他开源项目（已发公众号文章）：

[不会吧？你还在手动编辑 ~/.ssh/config？](https://mp.weixin.qq.com/s?__biz=MzIzOTY3MTExMQ==&mid=2247483744&idx=1&sn=301dedac74b2b71171376515b4cc6164&scene=21#wechat_redirect)

[这个开源插件帮助我从 Arc 迁移到 Chrome](https://mp.weixin.qq.com/s?__biz=MzIzOTY3MTExMQ==&mid=2247483719&idx=1&sn=f6f5ec043e39874cd8b4cc7a7ed8960e&scene=21#wechat_redirect)

[一个效率 x10 的开源 Markdown 命令行工具](https://mp.weixin.qq.com/s?__biz=MzIzOTY3MTExMQ==&mid=2247483691&idx=1&sn=8b6a7d47044d68394ee7a20dd6678c99&scene=21#wechat_redirect)

[我开源了一个音乐播放软件工具](https://mp.weixin.qq.com/s?__biz=MzIzOTY3MTExMQ==&mid=2247483678&idx=1&sn=2cc5a1d74629ead351f0875c3499e394&scene=21#wechat_redirect)

> > 更多项目，欢迎**关注我 Github** 获取我最新的开源项目进展。

![Image](data:image/svg+xml,%3C%3Fxml version='1.0' encoding='UTF-8'%3F%3E%3Csvg width='1px' height='1px' viewBox='0 0 1 1' version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'%3E%3Ctitle%3E%3C/title%3E%3Cg stroke='none' stroke-width='1' fill='none' fill-rule='evenodd' fill-opacity='0'%3E%3Cg transform='translate(-249.000000, -126.000000)' fill='%23FFFFFF'%3E%3Crect x='249' y='126' width='1' height='1'%3E%3C/rect%3E%3C/g%3E%3C/g%3E%3C/svg%3E)
