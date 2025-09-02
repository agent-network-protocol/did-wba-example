# DID WBA 客户端与服务器示例

这是一个使用FastAPI和Agent_Connect库实现的DID WBA方法示例，同时支持客户端和服务器功能。

详细的技术说明，可以参考[技术说明文档.md](/doc/技术说明文档.md)

## 功能特点

### 服务器功能
- 支持DID WBA认证协议
- 实现了两类鉴权方式:
  - DID WBA首次鉴权
  - Bearer Token鉴权
- 提供ad.json端点，并进行鉴权

### 客户端功能
- 自动生成DID文档和私钥，或加载已有的DID
- 向服务器发起DID WBA认证请求
- 接收并处理访问令牌
- 使用令牌发送后续请求

## 安装方法

### 环境准备

1. 克隆项目
2. 创建环境配置文件
   ```
   cp .env.example .env
   ```
3. 编辑.env文件，设置必要的配置项

### 使用 uv 安装依赖

[uv](https://github.com/astral-sh/uv) 是一个快速的 Python 包管理器和解析器，使用 Rust 编写。

```bash
# 安装 uv (如果尚未安装)
curl -sSf https://astral.sh/uv/install.sh | sh

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装项目依赖
uv pip install -e .
```

更多 uv 使用说明请参考 [UV 使用指南](README-uv.md)

## 运行示例

### 重要提示：需要先启动服务器，再启动客户端

要看到完整的交互效果，必须先启动一个服务器模式，然后再启动客户端模式。因为客户端需要连接到一个已运行的服务器进行认证和交互。

#### 第一步：启动服务器

```bash
# 确保虚拟环境已激活
source .venv/bin/activate

# 在第一个终端窗口启动服务器
python did_server.py
```

#### 第二步：启动客户端

```bash
# 在第二个终端窗口启动客户端，指定不同端口
python did_server.py --client --port 8001
```

#### 其他命令选项

```bash
# 指定端口运行服务器
python did_server.py --port 8001

# 使用特定id运行客户端
python did_server.py --client --unique-id your_unique_id
```

服务器将在指定端口(默认8000)启动，可以通过`http://localhost:8000/docs`访问API文档。

## API端点

- `GET /agents/example/ad.json`: 获取代理描述信息
- `GET /ad.json`: 获取广告JSON数据，需要进行鉴权
- `POST /auth/did-wba`: DID WBA首次鉴权
- `GET /auth/verify`: 验证Bearer Token
- `GET /wba/test`: 测试DID WBA认证
- `GET /wba/user/{user_id}/did.json`: 获取用户DID文档
- `PUT /wba/user/{user_id}/did.json`: 保存用户DID文档

## 工作流程

### 服务器流程
1. 启动服务器，监听请求
2. 接收DID WBA认证请求，验证签名
3. 生成并返回访问令牌
4. 处理后续使用令牌的请求

### 客户端流程
1. 生成或加载DID文档和私钥
2. 向服务器发送带有DID WBA签名头的请求
3. 接收令牌并保存
4. 使用令牌发送后续请求

## 鉴权说明

示例实现了两种鉴权方式：

1. **首次DID WBA鉴权**：根据DID WBA规范进行签名验证
2. **Bearer Token鉴权**：通过JWT令牌进行后续请求鉴权

详细的鉴权流程请参考代码实现和[DID WBA规范](https://github.com/agent-network-protocol/AgentNetworkProtocol/blob/main/chinese/03-did%3Awba%E6%96%B9%E6%B3%95%E8%A7%84%E8%8C%83.md)

