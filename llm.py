import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from mysql_message import MySQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv
load_dotenv()
chat_model = ChatOpenAI(
    api_key=os.getenv("QWEN_API_KEY1"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-vl-plus",
    streaming=True,
    temperature=0.7
)

def system_prompt(assistant_name, major, style):
    prompt_tem = PromptTemplate.from_template("""
    你是一个{major}专业的{assistant_name}，
    回答风格是{style}。
    你的任务是帮助用户解决学习问题，使用中文回答。
    """)
    return prompt_tem.format(assistant_name=assistant_name, major=major, style=style)

def get_session_history(session_id):
    return MySQLChatMessageHistory(session_id)


def llm_io(input, assistant_name, major, style, session_id):
    sysprompt = system_prompt(assistant_name, major, style)
    chatprompt = ChatPromptTemplate.from_messages(
        [
            ("system", sysprompt),
            MessagesPlaceholder(variable_name="history"),
            MessagesPlaceholder(variable_name="input"),
        ]
    )
    chat_chain = chatprompt | chat_model
    chain_with_history = RunnableWithMessageHistory(
        chat_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    return chain_with_history.stream(
        {"input": [HumanMessage(content=input)]},
        config={"configurable": {"session_id": session_id}}
    )