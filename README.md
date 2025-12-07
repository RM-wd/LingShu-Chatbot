# 灵枢智聊机器人

一个基于 Ollama 与 Streamlit 的本地智能聊天机器人，支持两种实现入口：
- `chat_main.py` + `chat_utils.py`：使用 Python `ollama` 包简单对话
- `基于ollama+streamlit搭建的灵枢智聊机器人.py`：使用 `requests` 调用 Ollama Chat API，支持流式输出与自定义样式
<img width="584" height="442" alt="image" src="https://github.com/user-attachments/assets/81e3d84c-c415-4386-a1d0-8ddedb2f4910" />


---

## 特性
- 本地部署，数据不出机，隐私安全
- 支持流式输出与对话历史记忆（会话态）
- 侧边栏可切换 Ollama 服务地址与模型名
- 简洁版与美化版双入口，满足不同场景需求

## 技术栈
- `Streamlit`：快速构建 Web 交互界面
- `Ollama`：本地大模型运行与推理服务
- `requests` / `ollama`：两种调用方式（HTTP 与 Python SDK）

## 目录结构
```
Chatbot/
├── chat_main.py                         # 简洁版 UI 入口（SDK）
├── chat_utils.py                        # Ollama 回复封装（SDK）
├── 基于ollama+streamlit搭建的灵枢智聊机器人.py   # 美化版 UI 入口（HTTP 流式）
└── 其余示例文件（Streamlit/Ollama 学习示例）
```

- `chat_utils.py` 中模型调用：`day_08/chat_utils.py:15-19`
- 简洁版页面与状态管理：`day_08/chat_main.py:1-39`
- 流式美化版页面与 API 调用：`day_08/基于ollama+streamlit搭建的灵枢智聊机器人.py:76-157`

---

## 快速开始

### 1. 安装依赖
- 安装 Python 3.10+ 与 pip
- 安装项目依赖：
```
pip install streamlit ollama requests langchain
```

### 2. 安装并启动 Ollama（Windows）
- 下载并安装 Ollama：https://ollama.com/download
- 启动服务后默认监听 `http://localhost:11434`

### 3. 拉取或准备模型
根据使用的入口选择模型：
- 简洁版（SDK）：`deepseek-r1:1.5b`
```
ollama pull deepseek-r1:1.5b
```
- 美化版（HTTP）：`qwen2:1.5b`（文件内默认名为 `qwen2`）
```
ollama pull qwen2:1.5b
```

### 4. 运行应用
- 运行简洁版入口：
```
streamlit run chat_main.py
```
- 运行美化版入口（支持流式与样式）：
```
streamlit run 基于ollama+streamlit搭建的灵枢智聊机器人.py
```

### 5. 切换模型或服务地址
- 简洁版：在 `day_08/chat_utils.py` 中修改 `model` 字段（`day_08/chat_utils.py:16`）
- 美化版：使用页面左侧侧边栏直接设置 `OLLAMA_BASE_URL` 与 `MODEL_NAME`（`day_08/基于ollama+streamlit搭建的灵枢智聊机器人.py:176-179`）

---

## 常见问题
- 无法连接 Ollama：确认服务在 `http://localhost:11434`，端口未被占用
- 模型不存在：先执行 `ollama pull <model>` 拉取模型
- 中文显示异常：确保终端/浏览器编码为 UTF-8
- 依赖缺失：重新执行 `pip install streamlit ollama requests langchain`

---

