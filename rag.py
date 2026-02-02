from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_community.chat_models.tongyi import ChatTongyi

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os


class ConversationHistory:
    """会话历史记录管理类"""

    def __init__(self, max_history: int = 10, storage_path: str = "conversation_history"):
        """
        初始化会话历史记录

        Args:
            max_history: 最大历史记录条数
            storage_path: 历史记录存储路径
        """
        self.max_history = max_history
        self.storage_path = storage_path
        self.conversations: Dict[str, List[Dict]] = {}

        # 创建存储目录
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        添加消息到历史记录

        Args:
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
            metadata: 附加元数据
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = []

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[session_id].append(message)

        # 限制历史记录长度
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        获取指定会话的历史记录

        Args:
            session_id: 会话ID
            limit: 返回的历史记录条数限制

        Returns:
            历史记录列表
        """
        if session_id not in self.conversations:
            return []

        history = self.conversations[session_id]
        if limit and len(history) > limit:
            return history[-limit:]

        return history.copy()

    def get_formatted_history(self, session_id: str, limit: Optional[int] = None) -> str:
        """
        获取格式化的历史记录字符串

        Args:
            session_id: 会话ID
            limit: 返回的历史记录条数限制

        Returns:
            格式化的历史记录字符串
        """
        history = self.get_history(session_id, limit)
        if not history:
            return "无历史对话记录"

        formatted = []
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}: {msg['content']}")

        return "\n".join(formatted)

    def get_langchain_messages(self, session_id: str, limit: Optional[int] = None) -> List[Any]:
        """
        获取LangChain格式的消息列表

        Args:
            session_id: 会话ID
            limit: 返回的历史记录条数限制

        Returns:
            LangChain消息列表
        """
        history = self.get_history(session_id, limit)
        messages = []

        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        return messages

    def clear_history(self, session_id: str):
        """清空指定会话的历史记录"""
        if session_id in self.conversations:
            self.conversations[session_id] = []

    def save_to_file(self, session_id: str):
        """保存会话历史到文件"""
        if session_id not in self.conversations:
            return

        filename = os.path.join(self.storage_path, f"{session_id}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.conversations[session_id], f, ensure_ascii=False, indent=2)

    def load_from_file(self, session_id: str):
        """从文件加载会话历史"""
        filename = os.path.join(self.storage_path, f"{session_id}.json")

        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                self.conversations[session_id] = json.load(f)


def print_prompt(prompt):
    """打印提示词用于调试"""
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)
    return prompt


class RagService(object):
    def __init__(self, session_id: str = "default_session"):
        """
        初始化RAG服务

        Args:
            session_id: 会话ID，用于区分不同用户的对话历史
        """
        self.session_id = session_id
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)
        )

        # 初始化历史记录管理器
        self.history_manager = ConversationHistory(max_history=10)

        # 加载历史记录（如果存在）
        self.history_manager.load_from_file(session_id)

        # 更新提示词模板，包含历史对话
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "你是一个专业的助手。请基于以下参考资料和历史对话记录来回答问题。\n"
                           "参考资料: {context}\n"
                           "历史对话记录: {history}"),
                ("user", "当前问题: {input}")
            ]
        )

        # 获取检索器
        self.retriever = self.vector_service.get_retriever()
        self.chat_model = ChatTongyi(model=config.chat_model_name)
        self.chain = self.__get_chain()

    def __get_chain(self):
        """获取最终的执行链"""

        def format_document(docs: list[Document]):
            """格式化文档"""
            if not docs:
                return "无相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段:{doc.page_content}\n文档元数据:{doc.metadata}\n\n"
            return formatted_str

        def get_history_str(history_limit: int = 5) -> str:
            """获取历史对话字符串"""
            return self.history_manager.get_formatted_history(
                self.session_id,
                history_limit
            )

        chain = (
                {
                    "input": RunnablePassthrough(),
                    "context": self.retriever | format_document,
                    "history": lambda x: get_history_str()
                }
                | self.prompt_template
                | print_prompt
                | self.chat_model
                | StrOutputParser()
        )
        return chain

    def invoke_with_history(self, query: str, save_history: bool = True) -> str:
        """
        带历史记录的查询方法

        Args:
            query: 用户查询
            save_history: 是否保存到历史记录

        Returns:
            模型回复
        """
        # 添加用户查询到历史记录
        self.history_manager.add_message(
            self.session_id,
            "user",
            query,
            {"type": "query"}
        )

        # 执行查询
        response = self.chain.invoke(query)

        # 添加助手回复到历史记录
        self.history_manager.add_message(
            self.session_id,
            "assistant",
            response,
            {"type": "response"}
        )

        # 保存历史记录到文件
        if save_history:
            self.history_manager.save_to_file(self.session_id)

        return response

    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        获取当前会话的历史记录

        Args:
            limit: 历史记录条数限制

        Returns:
            历史记录列表
        """
        return self.history_manager.get_history(self.session_id, limit)

    def clear_current_history(self):
        """清空当前会话的历史记录"""
        self.history_manager.clear_history(self.session_id)
        # 删除历史文件
        filename = os.path.join(
            self.history_manager.storage_path,
            f"{self.session_id}.json"
        )
        if os.path.exists(filename):
            os.remove(filename)

    def get_formatted_conversation(self, limit: Optional[int] = None) -> str:
        """
        获取格式化的对话历史

        Args:
            limit: 历史记录条数限制

        Returns:
            格式化的对话历史字符串
        """
        return self.history_manager.get_formatted_history(self.session_id, limit)


# 修改主函数以演示历史会话功能
if __name__ == '__main__':
    # 创建一个RAG服务实例，指定会话ID
    session_id = "user_001"  # 可以根据用户ID或其他标识来设置
    rag_service = RagService(session_id=session_id)

    print("=" * 50)
    print("RAG系统 - 带历史会话记录功能")
    print("=" * 50)

    # 示例对话
    queries = [
        "我身高190厘米，尺码推荐",
        "我喜欢运动风格的衣服",
        "预算是1000元以内"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n[第{i}轮对话]")
        print(f"用户: {query}")

        response = rag_service.invoke_with_history(query)
        print(f"助手: {response}")

        # 显示当前历史记录
        print(f"\n当前历史记录 ({len(rag_service.get_conversation_history())} 条):")
        history = rag_service.get_formatted_conversation()
        print(history)
        print("-" * 50)

    # 保存历史记录到文件
    rag_service.history_manager.save_to_file(session_id)

    # 测试重新加载历史记录
    print("\n" + "=" * 50)
    print("测试历史记录加载功能")
    print("=" * 50)

    # 创建新的服务实例，应该能加载之前的历史
    new_rag_service = RagService(session_id=session_id)
    loaded_history = new_rag_service.get_formatted_conversation()
    print("加载的历史记录:")
    print(loaded_history)