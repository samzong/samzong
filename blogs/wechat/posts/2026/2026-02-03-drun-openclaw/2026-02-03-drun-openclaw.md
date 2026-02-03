# OpenClaw + 飞书部署 on Console D.run

## 环境信息

- OS: Ubuntu 24.04 (GPU Container)
- Platform: console.d.run
- Node: 24.x
- Models: DeepSeek-R1
- Channel: Feishu (飞书)

## 1. 购买 GPU 容器实例

1. 访问 https://console.d.run
2. 算力云 → 创建实例
3. 选择 GPU 配置（推荐 RTX 4090/A100）
4. 操作系统：Ubuntu 24.04
5. 记录实例 IP 和 SSH 端口

## 2. SSH 连接容器

```bash
ssh root@<instance-ip> -P <ssh-port>
```

## 3. 配置镜像源

```bash
# 安装 chsrc
curl -LO https://gitee.com/RubyMetric/chsrc/releases/download/pre/chsrc_latest-1_amd64.deb
sudo apt install ./chsrc_latest-1_amd64.deb

# 配置 npm 镜像
chsrc set npm
```

## 4. 安装 Node.js 24
```bash
# 安装 Node.js 24
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# 验证版本
node --version  # v24.x
npm --version
```

## 5. 安装 OpenClaw
```bash
# 全局安装
npm install -g openclaw@latest

# 验证安装
openclaw --version
```

## 6. 配置端口映射

**在 console.d.run 控制台操作：**
1. 进入实例详情
2. 网络 → 自定义端口
3. 添加映射：`容器端口 18789` → `公网端口 <随机端口>`
4. 记录公网访问地址：`http://<公网IP>:<公网端口>`

## 7. 验证 OpenClaw
```bash
# 检查健康状态
openclaw health

# 检查网关状态
openclaw gateway run

# 测试本地访问
curl http://localhost:18789/health
```

## 8. 本地电脑访问

浏览器打开（替换为实际值）：
```
http://<公网IP>:<公网端口>/?token=<your-secure-token>
```

从 `~/.openclaw/openclaw.json` 获取 token。

## 8. 安装飞书 Channel 插件
```bash
openclaw plugins install moltbot-channel-feishu
```

## 9. 飞书后台配置

### 15.1 创建企业自建应用

1. 访问 https://open.feishu.cn/app
2. 创建企业自建应用
3. 记录 `App ID` 和 `App Secret`

### 15.2 配置应用权限

开通权限：
- `im:message`（接收消息）
- `im:message:send_as_bot`（发送消息）
- `im:chat`（群组消息）

### 15.3 启用长链接

1. 事件与回调 → 订阅方式 → 长链接
2. 订阅事件：
   - `im.message.receive_v1`（接收消息）

### 15.4 配置机器人

1. 机器人配置 → 启用机器人
3. 发布版本 → 全员可用

## 17. 配置 OpenClaw 识别飞书 Channel

```bash
# 创建飞书配置
cat >> ~/.openclaw/openclaw.json << 'EOF'
"channels": {
  "feishu": {
    "enabled": true,
    "appId": "cli_xxx",
    "appSecret": "xxxxxxxxxxxxx",
    "domain": "feishu",
    "dmPolicy": "pairing",
    "groupPolicy": "open"
  }
}
EOF

# 启动 OpenClaw
nohup openclaw gateway run >/dev/null 2>&1 &
```

## 18. 测试飞书机器人

### 18.1 群聊测试

1. 创建飞书群
2. 添加机器人到群
3. @机器人发送消息：`你好`

### 18.2 私聊测试

1. 在飞书搜索机器人名称
2. 发起私聊
3. 发送消息：`测试 DeepSeek-R1`

### 切换模型

在飞书对话中：

```
/help
```

## 完成

部署完成后访问路径：
- Web UI: `http://<公网IP>:<公网端口>/?token=<token>`
- 飞书群聊: @机器人对话
- 飞书私聊: 搜索机器人名称直接对话

关键文件位置：
- OpenClaw 配置: `~/.openclaw/`
- 飞书插件: `/root/.openclaw/extensions/moltbot-channel-feishu/`
