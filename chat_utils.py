import ollama


def get_response(messages):
    """
    从历史消息中提取最新用户提问，调用ollama模型获取回复
    :param messages: 历史消息列表
    :return: 模型生成的回复
    """
    # 提取最新的用户消息
    # user_prompt = next((msg['content'] for msg in reversed(messages) if msg['role'] == 'user'), '')

    try:
        # 调用ollama API
        response = ollama.chat(
            model='deepseek-r1:1.5b',
            messages=messages[-20:]  # 只显示最后20条聊天记录
        )
        return response['message']['content']
    except Exception as e:
        return f"😔 调用模型时出错了: {str(e)}"


if __name__ == '__main__':
    # 简单测试脚本
    while True:
        user_input = input('请输入您要表达的内容（输入q退出）：')
        if user_input.lower() == 'q':
            break
        response = get_response([{"role": "user", "content": user_input}])
        print(f"🤖 {response}")
