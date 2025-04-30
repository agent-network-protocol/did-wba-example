如果你是小白，可以通过如下方式从零开始运行：
# Windows
在设置Python开发环境时，通常会有一些工具需要全局安装，而其他工具则适合在项目的虚拟环境中安装。以下是一个理想的安装顺序和建议：

## 全局安装
1. pip : 通常已经随Python安装一起提供，用于安装和管理Python包。
2. pipx : 用于全局安装和管理独立的Python应用程序。适合安装像 poetry 这样的工具。
   
   ```bash
   pip install pipx
   python -m pipx ensurepath
    ```
3. poetry : 用于依赖管理和打包的工具，建议通过 pipx 全局安装，以便在多个项目中使用。
   
   ```bash
   pipx install poetry
   pipx ensurepath
    ```
## 虚拟环境安装
1. .venv : 在项目目录下创建虚拟环境，用于隔离项目的依赖。
   
   ```bash
   python -m venv .venv
    ```
2. 项目依赖 : 在激活虚拟环境后，检查python是否指向虚拟环境，然后通过 poetry 安装项目的依赖。
   
   ```bash
   .venv\Scripts\Activate.ps1
   where.exe python
   poetry install
    ```
3. 退出虚拟环境:

   ```bash
   deactivate
    ```
通过这种方式，你可以确保全局工具的独立性和项目依赖的隔离性，避免不同项目之间的依赖冲突。

## 运行项目 
1. 克隆项目
2. 创建环境配置文件
   ```
   cp .env.example .env
   ```
3. 编辑.env文件，设置必要的配置项
4. 启动服务器
   ```bash
   python did_server.py
   ```
5. 启动客户端
   ```bash
     # 在第二个终端窗口启动客户端，指定不同端口
   python did_server.py --client --port 8001
   ```




# Mac

本项目要求 python 版本在 3.10 以上。

在设置Python开发环境时，通常会有一些工具需要全局安装，而其他工具则适合在项目的虚拟环境中安装。以下是一个理想的安装顺序和建议：

## 全局安装
1. pip : 通常已经随Python安装一起提供，用于安装和管理Python包。
2. pipx : 用于全局安装和管理独立的Python应用程序。适合安装像 poetry 这样的工具。
   
   ```bash
   pip install pipx
   pipx ensurepath
    ```
3. poetry : 用于依赖管理和打包的工具，建议通过 pipx 全局安装，以便在多个项目中使用。
   
   ```bash
   pipx install poetry
   pipx ensurepath
    ```
## 虚拟环境安装
1. .venv : 在项目目录下创建虚拟环境，用于隔离项目的依赖。（也可以跳过此步，poetry install 会自动创建）
   
   ```bash
   python3 -m venv .venv
    ```
2. 项目依赖 : 在激活虚拟环境后，检查python是否在虚拟环境中，通过 poetry 安装项目的依赖。
   
   ```bash
   source .venv/bin/activate
   where python
   poetry install
    ```
3. 等实验结束后可退出虚拟环境:

   ```bash
   deactivate
    ```
通过这种方式，你可以确保全局工具的独立性和项目依赖的隔离性，避免不同项目之间的依赖冲突。

## 运行项目 
1. 克隆项目
2. 创建环境配置文件
   ```
   cp .env.example .env
   ```
3. 编辑 .env 文件，设置必要的配置项，如 OPENROUTER_API_KEY，可到 [open router 官网](https://openrouter.ai/) 生成 API key，本 demo 使用免费模型，无需充值。
4. 启动服务器。初次启动可能要创建 logs 目录，使用了 sudo 命令，需要输入管理员密码。
   ```bash
   python did_server.py
   # 启动成功后执行
   start server
   ```
5. 启动客户端
   ```bash
     # 在第二个终端窗口启动客户端，指定不同端口
   python did_server.py --client --port 8001
   ```

启动客户端后会自动连接 server 并发送问候信息，如果发送成功会看到提示。然后就可以根据 help 命令中的提示进一步探索与其他 agent 交互的场景。