"""DID WBA Example with both Client and Server capabilities."""
import os
import json
import logging
import uvicorn
import asyncio
import secrets
import argparse
import signal
import threading
import sys
import time
import httpx

from pathlib import Path

from core.config import settings
from core.app import create_app
from auth.did_auth import (
    generate_or_load_did, 
    send_authenticated_request,
    send_request_with_token,
    DIDWbaAuthHeader
)
from utils.log_base import set_log_color_level

# Create FastAPI application
app = create_app()


@app.get("/", tags=["status"])
async def root():
    """
    Root endpoint for server status check.
    
    Returns:
        dict: Server status information
    """
    return {
        "status": "running",
        "service": "DID WBA Example",
        "version": "0.1.0",
        "mode": "Client and Server",
        "documentation": "/docs"
    }


async def client_example(unique_id: str = None):
    """
    Run the client example to demonstrate DID WBA authentication.
    
    Args:
        unique_id: Optional unique identifier
    """
    try:
        # 1. Generate or load DID document
        if not unique_id:
            unique_id = secrets.token_hex(8)
            
        logging.info(f"Using unique ID: {unique_id}")
        did_document, keys, user_dir = await generate_or_load_did(unique_id)
        did_document_path = Path(user_dir) / settings.DID_DOCUMENT_FILENAME
        private_key_path = Path(user_dir) / settings.PRIVATE_KEY_FILENAME
        
        logging.info(f"DID document path: {did_document_path}")
        logging.info(f"Private key path: {private_key_path}")
        
        # 2. Target server information
        target_host = settings.TARGET_SERVER_HOST
        target_port = settings.TARGET_SERVER_PORT
        base_url = f"http://{target_host}:{target_port}"
        test_url = f"{base_url}/wba/test"
        
        # 3. Create DIDWbaAuthHeader instance
        auth_client = DIDWbaAuthHeader(
            did_document_path=str(did_document_path),
            private_key_path=str(private_key_path)
        )
        
        # 4. Send request with DID WBA authentication
        logging.info(f"Sending authenticated request to {test_url}")
        status, response, token = await send_authenticated_request(test_url, auth_client)
        
        if status != 200:
            logging.error(f"Authentication failed! Status: {status}")
            logging.error(f"Response: {response}")
            return
            
        logging.info(f"Authentication successful! Response: {response}")
        
        # 5. If we received a token, use it for subsequent requests
        if token:
            logging.info("Received access token, trying to use it for next request")
            status, response = await send_request_with_token(test_url, token)
            
            if status == 200:
                logging.info(f"Token authentication successful! Response: {response}")
            else:
                logging.error(f"Token authentication failed! Status: {status}")
                logging.error(f"Response: {response}")
            # 进入命令行聊天模式
            chat_url = f"{base_url}/wba/chat"
            print("\n已认证，进入命令行聊天。输入 /q 退出。")
            async with httpx.AsyncClient(timeout=300) as client:
                while True:
                    user_msg = input("你: ").strip()

                    if user_msg == "/q":
                        print("已退出聊天。\n")
                        break
                    try:
                        resp = await client.post(
                            chat_url,
                            headers={"Authorization": f"Bearer {token}"},
                            json={"message": user_msg}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            answer = data.get("answer", "[无回复]")
                            print(f"助手: {answer}")
                        else:
                            print(f"[错误] 服务器返回: {resp.status_code} {resp.text}")
                    except Exception as ce:
                        print(f"[错误] 聊天请求失败: {ce}")
        else:
            logging.warning("No token received from server")
            
    except Exception as e:
        logging.error(f"Error in client example: {e}")


# 全局变量，用于存储服务器、客户端和聊天线程
server_thread = None
client_thread = None
chat_thread = None
server_running = False
client_running = False
chat_running = False
unique_id = None
server_instance = None  # 存储uvicorn.Server实例


def run_server():
    """在子线程中运行uvicorn服务器"""
    global server_running, server_instance
    try:
        config = uvicorn.Config(
            "did_server:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            # 关闭内部信号处理
            use_colors=True,
            log_level="info"
        )
        server_instance = uvicorn.Server(config)
        # 这一行很关键：关闭uvicorn自带的信号处理
        server_instance.install_signal_handlers = lambda: None
        server_running = True
        server_instance.run()
    except Exception as e:
        logging.error(f"服务器运行出错: {e}")
    finally:
        server_running = False


def run_client(port=None, unique_id_arg=None):
    """在子线程中运行客户端示例
    
    Args:
        port: 可选的目标服务器端口号
        unique_id_arg: 可选的唯一ID
    """
    global client_running
    try:
        # 等待2秒确保服务器已启动
        time.sleep(2)
        # 在新线程中创建事件循环运行客户端示例
        client_running = True
        # 如果提供了端口号，临时修改目标服务器端口设置
        original_port = None
        if port is not None:
            try:
                port_num = int(port)
                original_port = settings.TARGET_SERVER_PORT
                settings.TARGET_SERVER_PORT = port_num
                logging.info(f"使用自定义目标服务器端口: {port_num}")
            except ValueError:
                logging.error(f"无效的端口号: {port}，使用默认端口: {settings.TARGET_SERVER_PORT}")
        
        # 运行客户端示例
        asyncio.run(client_example(unique_id_arg))
        
        # 恢复原始端口设置
        if original_port is not None:
            settings.TARGET_SERVER_PORT = original_port
    except Exception as e:
        logging.error(f"客户端运行出错: {e}")
    finally:
        client_running = False


def start_server(port=None):
    """启动服务器线程
    
    Args:
        port: 可选的服务器端口号，如果提供则会覆盖默认端口
    """
    global server_thread, server_running
    if server_thread and server_thread.is_alive():
        print("服务器已经在运行中")
        return
    
    # 如果提供了端口号，则临时修改设置中的端口
    if port is not None:
        try:
            port_num = int(port)
            settings.PORT = port_num
            print(f"使用自定义端口: {port_num}")
        except ValueError:
            print(f"无效的端口号: {port}，使用默认端口: {settings.PORT}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"服务器已在 http://{settings.HOST}:{settings.PORT} 启动")


def stop_server():
    """停止服务器线程"""
    global server_thread, server_running, server_instance
    if not server_thread or not server_thread.is_alive():
        print("服务器未运行")
        return
    
    print("正在关闭服务器...")
    # 由于uvicorn没有优雅的关闭方法，我们需要设置server_instance的should_exit属性
    server_running = False
    
    # 确保server_instance存在并设置should_exit属性
    if server_instance: 
        server_instance.should_exit = True
    
    # 等待服务器线程结束
    server_thread.join(timeout=5)
    if server_thread.is_alive():
        print("服务器关闭超时，可能需要重启程序")
    else:
        print("服务器已关闭")
        server_thread = None
        server_instance = None


def start_client(port=None, unique_id_arg=None):
    """启动客户端线程
    
    Args:
        port: 可选的目标服务器端口号
        unique_id_arg: 可选的唯一ID
    """
    global client_thread, client_running, unique_id
    if client_thread and client_thread.is_alive():
        print("客户端已经在运行中")
        return
    
    if unique_id_arg:
        unique_id = unique_id_arg
    
    client_thread = threading.Thread(target=run_client, args=(port, unique_id), daemon=True)
    client_thread.start()
    print("客户端已启动")
    if port:
        print(f"使用目标服务器端口: {port}")


def stop_client():
    """停止客户端线程"""
    global client_thread, client_running
    if not client_thread or not client_thread.is_alive():
        print("客户端未运行")
        return
    
    print("正在关闭客户端...")
    client_running = False
    client_thread.join(timeout=5)
    if client_thread.is_alive():
        print("客户端关闭超时，可能需要重启程序")
    else:
        print("客户端已关闭")
        client_thread = None


async def run_chat():
    """运行LLM聊天线程 - 直接调用OpenRouter API"""
    global chat_running
    try:
        # 检查OpenRouter API密钥是否配置
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not openrouter_api_key:
            print("[错误] 未配置OpenRouter API密钥，请在环境变量中设置OPENROUTER_API_KEY")
            chat_running = False
            return
            
        # OpenRouter API配置
        openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json"
        }
        
        print("\n已启动LLM聊天线程。输入消息与AI对话，输入 /q 退出。")
        logging.info("聊天线程启动 - 直接调用OpenRouter API")
        
        # 进入聊天模式
        async with httpx.AsyncClient(timeout=30) as client:
            chat_running = True
            while chat_running:
                user_msg = input("你: ").strip()
                
                if user_msg.lower() == "/q":
                    print("退出聊天线程。\n")
                    break
                    
                try:
                    # 准备请求数据
                    payload = {
                        "model": "deepseek/deepseek-chat-v3-0324:free",  # 免费模型
                        "messages": [{"role": "user", "content": user_msg}],
                        "max_tokens": 512
                    }
                    
                    # 发送请求到OpenRouter API
                    resp = await client.post(
                        openrouter_api_url,
                        headers=headers,
                        json=payload
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        answer = data['choices'][0]['message']['content']
                        print(f"助手: {answer}")
                    else:
                        print(f"[错误] OpenRouter API返回: {resp.status_code} {resp.text}")
                except Exception as ce:
                    print(f"[错误] 聊天请求失败: {ce}")
                    if not chat_running:  # 如果线程被外部终止
                        break
    except Exception as e:
        logging.error(f"聊天线程出错: {e}")
    finally:
        chat_running = False


def start_chat():
    """启动LLM聊天线程 - 直接调用OpenRouter API"""
    global chat_thread, chat_running
    if chat_thread and chat_thread.is_alive():
        print("聊天线程已经在运行中")
        return
    
    chat_thread = threading.Thread(target=lambda: asyncio.run(run_chat()), daemon=True)
    chat_thread.start()
    print("LLM聊天线程已启动")


def stop_chat():
    """停止LLM聊天线程"""
    global chat_thread, chat_running
    if not chat_thread or not chat_thread.is_alive():
        print("聊天线程未运行")
        return
    
    print("正在关闭聊天线程...")
    chat_running = False
    chat_thread.join(timeout=5)
    if chat_thread.is_alive():
        print("聊天线程关闭超时，可能需要重启程序")
    else:
        print("聊天线程已关闭")
        chat_thread = None


def show_status():
    """显示当前服务器、客户端和聊天状态"""
    server_status = "运行中" if server_thread and server_thread.is_alive() else "已停止"
    client_status = "运行中" if client_thread and client_thread.is_alive() else "已停止"
    chat_status = "运行中" if chat_thread and chat_thread.is_alive() else "已停止"
    
    print(f"服务器状态: {server_status}")
    print(f"客户端状态: {client_status}")
    print(f"聊天状态: {chat_status}")
    if unique_id:
        print(f"当前客户端ID: {unique_id}")


def show_help():
    """显示帮助信息"""
    print("可用命令:")
    print("  start server [port] - 启动服务器，可选指定端口号")
    print("  stop server - 停止服务器")
    print("  start client [port] [unique_id] - 启动客户端，可选指定目标服务器端口和唯一ID")
    print("  stop client - 停止客户端")
    print("  start chat - 启动LLM聊天线程")
    print("  stop chat - 停止LLM聊天线程")
    print("  status - 显示服务器、客户端和聊天状态")
    print("  help - 显示此帮助信息")
    print("  exit - 退出程序")


def main():
    """主函数，处理命令行输入"""
    global unique_id
    
    set_log_color_level(logging.INFO)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="DID WBA Example with Client and Server capabilities")
    parser.add_argument("--client", action="store_true", help="Run client example at startup")
    parser.add_argument("--server", action="store_true", help="Run server at startup", default=False)
    parser.add_argument("--unique-id", type=str, help="Unique ID for client example", default=None)
    parser.add_argument("--port", type=int, help=f"Server port (default: {settings.PORT})", default=settings.PORT)
    parser.add_argument("--target-port", type=int, help=f"Target server port for client (default: {settings.TARGET_SERVER_PORT})", default=None)
    
    args = parser.parse_args()
    
    if args.port != settings.PORT:
        settings.PORT = args.port
    
    if args.unique_id:
        unique_id = args.unique_id
    
    # 根据命令行参数启动服务
    if args.server:
        start_server()
    
    if args.client:
        start_client(args.target_port, args.unique_id)
    
    print("DID WBA 示例程序已启动")
    print("输入'help'查看可用命令，输入'exit'退出程序")
    
    # 主循环，处理用户输入
    while True:
        try:
            # 如果客户端或聊天线程正在运行，则等待其退出，不处理命令
            if client_running or chat_running:
                # 等待客户端或聊天线程退出
                while client_running or chat_running:
                    time.sleep(0.5)
                if not client_running and not chat_running:
                    print("客户端或聊天线程已退出，恢复命令行控制。")
            command = input("> ").strip().lower()
            
            if command == "exit":
                print("正在关闭服务...")
                stop_chat()
                stop_client()
                stop_server()
                break
            elif command == "help":
                show_help()
            elif command == "status":
                show_status()
            elif command.startswith("start server"):
                # 检查是否指定了端口号
                parts = command.split()
                if len(parts) > 2:
                    start_server(parts[2])
                else:
                    start_server()
            elif command.startswith("stop server"):
                stop_server()
            elif command.startswith("stop client"):
                stop_client()
            elif command.startswith("start client"):
                # 检查是否指定了port和unique_id
                parts = command.split()
                if len(parts) > 3:
                    # 同时指定了port和unique_id
                    start_client(parts[2], parts[3])
                elif len(parts) > 2:
                    # 只指定了port
                    start_client(parts[2])
                else:
                    # 没有指定参数
                    start_client()
                # 阻塞主进程直到 client_thread 结束，避免输入竞争
                if client_thread:
                    client_thread.join()
                print("客户端已退出，恢复命令行控制。")
                continue  # 跳过本轮命令输入
            elif command == "start chat":
                start_chat()
                # 阻塞主进程直到 chat_thread 结束，避免输入竞争
                if chat_thread:
                    chat_thread.join()
                print("聊天线程已退出，恢复命令行控制。")
                continue  # 跳过本轮命令输入
            elif command == "stop chat":
                stop_chat()
            else:
                print(f"未知命令: {command}")
                print("输入'help'查看可用命令")
                
        except KeyboardInterrupt:
            print("\n检测到退出信号，正在关闭...")
            stop_client()
            stop_server()
            break
        except Exception as e:
            print(f"错误: {e}")
    
    print("程序已退出")
    sys.exit(0)


if __name__ == "__main__":
    main()