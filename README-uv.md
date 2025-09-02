# DID WBA Server with uv

This project uses [uv](https://docs.astral.sh/uv/) as the Python package manager.

## Prerequisites

- Install [uv](https://docs.astral.sh/uv/)
- Python 3.9 or later

## Setup

1. Install Python (if not already installed):
   ```bash
   uv python install 3.9
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

## Running the Application

```bash
uvicorn did_server:app --reload
```

## Development

- To add a new dependency:
  ```bash
  # 1. 安装新包
  uv pip install package_name
  
  # 2. 更新 pyproject.toml 中的 dependencies 列表
  
  # 3. 重新安装项目依赖
  uv pip install -e .
  ```

- To update all dependencies:
  ```bash
  # 更新所有包到最新版本
  uv pip install --upgrade -e .
  ```

## Cleaning Up

To remove the virtual environment:

```bash
rm -rf .venv
```
