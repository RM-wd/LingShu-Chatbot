import time
import streamlit as st
from rag import RagService
import config_data as config

# 页面配置
st.set_page_config(
    page_title="灵枢智聊机器人",
    page_icon="🤖",
    layout="wide"
)

# 标题
st.title("🤖 灵枢智聊机器人")
st.divider()

# 侧边栏 - 会话管理
with st.sidebar:
    st.header("会话管理")

    # 会话ID设置
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = f"session_{int(time.time())}"

    session_id_input = st.text_input(
        "会话ID",
        value=st.session_state["session_id"],
        help="每个会话ID对应独立的对话历史"
    )

    # 更新会话ID
    if session_id_input != st.session_state["session_id"]:
        st.session_state["session_id"] = session_id_input
        st.session_state["rag"] = RagService(session_id=session_id_input)
        # 重置消息历史
        st.session_state["message"] = [{"role": "assistant", "content": "您好，我是新的会话助手，有什么可以帮助您？"}]
        st.rerun()

    st.divider()

    # 历史记录管理
    st.subheader("历史记录")

    # 显示当前会话信息
    if "rag" in st.session_state:
        history_count = len(st.session_state["rag"].get_conversation_history())
        st.info(f"当前会话历史: {history_count} 条记录")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 查看历史", use_container_width=True):
            if "rag" in st.session_state:
                history = st.session_state["rag"].get_formatted_conversation()
                if history == "无历史对话记录":
                    st.warning("暂无历史对话记录")
                else:
                    with st.expander("完整对话历史", expanded=True):
                        st.text(history)

    with col2:
        if st.button("🗑️ 清空历史", use_container_width=True):
            if "rag" in st.session_state:
                st.session_state["rag"].clear_current_history()
                st.session_state["message"] = [{"role": "assistant", "content": "历史记录已清空，有什么可以帮助您？"}]
                st.success("历史记录已清空")
                time.sleep(1)
                st.rerun()

    st.divider()

    # 模型设置
    st.subheader("模型设置")

    # 历史记录长度设置
    if "history_limit" not in st.session_state:
        st.session_state["history_limit"] = 5

    history_limit = st.slider(
        "历史记录长度",
        min_value=0,
        max_value=10,
        value=st.session_state["history_limit"],
        help="设置使用多少轮历史对话作为上下文，0表示不使用历史"
    )

    if history_limit != st.session_state["history_limit"]:
        st.session_state["history_limit"] = history_limit

    # 显示当前模型信息
    st.info(f"""
    当前配置：
    - 模型：{config.chat_model_name}
    - 历史长度：{history_limit}轮
    - 会话ID：{st.session_state["session_id"][:15]}...
    """)

# 初始化会话状态
if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "您好，我是灵枢智聊机器人，有什么可以帮助您？"}]

if "rag" not in st.session_state:
    st.session_state["rag"] = RagService(session_id=st.session_state["session_id"])

# 显示历史消息
for message in st.session_state["message"]:
    avatar = "🤖" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 显示当前使用的历史记录（调试信息）
with st.expander("📋 当前使用的上下文", expanded=False):
    if st.session_state["history_limit"] > 0:
        history = st.session_state["rag"].get_formatted_conversation(
            limit=st.session_state["history_limit"]
        )
        st.text(history)
    else:
        st.info("当前未使用历史对话作为上下文")

# 用户输入
prompt = st.chat_input("请输入您的问题...")

if prompt:
    # 显示用户消息
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 添加到消息历史
    st.session_state["message"].append({"role": "user", "content": prompt})

    # 准备响应
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""

        # 获取历史记录
        history_limit = st.session_state.get("history_limit", 5)

        try:
            # 使用带历史记录的方法
            with st.spinner("正在思考..."):
                # 为了支持流式输出，这里需要稍微调整
                # 先获取完整响应
                response = st.session_state["rag"].invoke_with_history(prompt)

                # 模拟流式输出效果
                chunks = [response[i:i + 50] for i in range(0, len(response), 50)]
                for chunk in chunks:
                    full_response += chunk
                    time.sleep(0.05)  # 模拟流式输出的延迟
                    message_placeholder.markdown(full_response + "▌")

                # 最终显示
                message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"处理请求时出错: {str(e)}")
            full_response = "抱歉，处理您的请求时出现了问题。"
            message_placeholder.markdown(full_response)

    # 添加到消息历史
    st.session_state["message"].append({"role": "assistant", "content": full_response})

    # 显示本次使用的上下文信息
    with st.expander("📄 本次查询详情", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("历史记录使用", f"{history_limit}轮")
        with col2:
            st.metric("响应长度", f"{len(full_response)}字符")

        # 显示最近的历史记录
        st.caption("最近的历史对话：")
        recent_history = st.session_state["rag"].get_formatted_conversation(limit=3)
        st.text(recent_history)

# 页脚信息
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns(3)
with footer_col1:
    st.caption(f"会话ID: {st.session_state['session_id']}")
with footer_col2:
    if "rag" in st.session_state:
        history_count = len(st.session_state["rag"].get_conversation_history())
        st.caption(f"历史记录: {history_count}条")
with footer_col3:
    st.caption("Powered by LangChain & DeepSeek")