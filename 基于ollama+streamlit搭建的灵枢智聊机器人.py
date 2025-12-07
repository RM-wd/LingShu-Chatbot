import streamlit as st
import requests
import json
import time

# 设置页面配置
st.set_page_config(
    page_title="灵枢智聊机器人",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
    }
    .chat-message.user {
        background-color: #f5f5f5;
    }
    .chat-message.assistant {
        background-color: #e6f7ff;
    }
    .chat-message .avatar {
        min-width: 40px;
        max-width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .chat-message.user .avatar {
        background-color: #ff6b6b;
        color: white;
    }
    .chat-message.assistant .avatar {
        background-color: #165DFF;
        color: white;
    }
    .typing-animation {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background-color: #165DFF;
        animation: typing 1.4s infinite ease-in-out;
        margin-left: 5px;
    }
    @keyframes typing {
        0%, 100% { transform: scale(0); }
        50% { transform: scale(1); }
    }
    .sidebar-content {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.markdown("<h1 style='text-align: center; color: #165DFF;'>灵枢智聊机器人</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>基于Ollama平台的Qwen2-1.5B模型</p>", unsafe_allow_html=True)

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

# Ollama API配置
OLLAMA_BASE_URL = "http://localhost:11434"  # 默认Ollama服务地址
MODEL_NAME = "qwen2"  # Ollama中Qwen2模型的名称

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(f"""
        <div class="chat-message {message["role"]}">
            <div class="avatar">{message["role"][0].upper()}</div>
            <div class="message-content">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

# 处理用户输入
if prompt := st.chat_input("很高兴为您服务，请输入您的问题..."):
    # 保存用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(f"""
        <div class="chat-message user">
            <div class="avatar">U</div>
            <div class="message-content">{prompt}</div>
        </div>
        """, unsafe_allow_html=True)

    # 生成回答
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # 显示正在输入动画
        message_placeholder.markdown(f"""
        <div class="chat-message assistant">
            <div class="avatar">A</div>
            <div class="message-content">
                <p>AI正在思考中<span class="typing-animation"></span></p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            # 构建请求数据
            messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "stream": True
            }

            # 调用Ollama API
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                stream=True
            )

            # 处理流式响应
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        # 解析JSON行
                        data = json.loads(line.decode('utf-8'))
                        if 'message' in data and 'content' in data['message']:
                            content = data['message']['content']
                            full_response += content

                            # 更新UI
                            message_placeholder.markdown(f"""
                            <div class="chat-message assistant">
                                <div class="avatar">A</div>
                                <div class="message-content">{full_response}</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                full_response = f"API请求失败: HTTP {response.status_code}"

        except Exception as e:
            full_response = f"发生错误: {str(e)}"

        # 保存AI回答
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# 侧边栏
with st.sidebar:
    st.markdown("<h3 class='sidebar-content'>关于灵枢智聊机器人</h3>", unsafe_allow_html=True)
    st.info("""
    灵枢智聊机器人是一个基于Ollama平台Qwen2-1.5B模型的智能对话系统，
    可以回答问题、提供建议、进行闲聊等功能。
    """)

    st.markdown("<h3 class='sidebar-content'>使用指南</h3>", unsafe_allow_html=True)
    st.write("- 请确保Ollama服务正在运行")
    st.write("- 复杂问题可能需要更长的回答时间")
    st.write("- 如遇错误，请检查Ollama服务地址")

    # 高级设置
    with st.expander("高级设置"):
        OLLAMA_BASE_URL = st.text_input("Ollama服务地址", OLLAMA_BASE_URL)
        MODEL_NAME = st.text_input("模型名称", MODEL_NAME)

    if st.button("清空对话历史"):
        st.session_state.messages = []
        st.success("对话历史已清空")