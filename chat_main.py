import streamlit as st
from chat_utils import get_response
from langchain.memory import ConversationBufferMemory

# 1. 主界面标题（添加表情符号）
st.title('灵枢智聊机器人 🤖')

# 2. 会话保持：用于存储会话记录
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好，我是灵枢智聊机器人，有什么可以帮您的吗？ 😊"}
    ]

# 3.  循环打印历史会话（添加角色图标）
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # 根据角色(user,assistant)创建对话信息
        icon = "🧑‍💻" if message["role"] == "user" else "🤖"
        # 打印该角色的具体会话信息
        st.write(f"{icon} {message['content']}")

# 4. 创建聊天输入框，提示用户录入他/她的问题，并接收
user_input = st.chat_input("遇事不决，就问灵枢... 🧐")

# 5. 处理用户输入，如果不为空，程序就往下运行
if user_input:
    # 6. 把用户录入的问题，添加到会话历史中
    st.session_state.messages.append({"role": "user", "content": user_input})
    # 7. 显示用户录入的问题
    st.chat_message("user").write(f"🧑‍💻 {user_input}")

    # 8. 获取AI思考过程
    with st.spinner("灵枢智聊正在思考中... ⏳"):
        # 9. 把问题传给大模型，获取大模型的回复信息
        response = get_response(st.session_state.messages)

    # 10. 把(大模型回复信息)添加到会话历史中，并显示到前段
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").markdown(f"🤖 {response}")
