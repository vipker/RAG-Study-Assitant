from mysql_db import execute, fetch_all, fetch_one
from datetime import datetime
import json
import streamlit as st
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, messages_from_dict, messages_to_dict
import gc
import os
import shutil
import time

def new_session_id():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def to_json(data):
    return json.dumps(data, ensure_ascii=False)


def from_json(json_data):
    if json_data is None:
        return None
    return json.loads(json_data)


def new_config():
    config = {"assistant_name": "Python编程", "major": "Python编程", "style": "简洁专业", "rag_switch": True}
    return config


def create_session():
    session_id = new_session_id()
    vector_path = f"./chroma_db/{session_id}"
    sql_sessions = """
        INSERT INTO sessions
        (session_id, vector_path)
        VALUES
        (%s, %s)
        """
    execute(sql_sessions, (session_id, vector_path))
    config = new_config()
    config_json = to_json(config)
    sql_config = """
        INSERT INTO session_config (session_id, config_json)
        VALUES (%s, %s)
        """
    execute(sql_config, (session_id, config_json))
    return session_id

def get_vector_path(session_id):
    sql = """
    SELECT vector_path
    FROM sessions
    WHERE session_id = %s
    """
    row = fetch_one(sql, (session_id,))
    return row["vector_path"]

def get_config(session_id):
    sql = """
    SELECT config_json
    FROM session_config
    WHERE session_id = %s
    """
    row = fetch_one(sql, (session_id,))
    return from_json(row["config_json"])


def config_to_ui(config):
    st.session_state.assistant_name = config.get("assistant_name", "学习导师")
    st.session_state.major = config.get("major", "Python编程")
    st.session_state.style = config.get("style", "简洁专业")
    st.session_state.rag_switch = config.get("rag_switch", True)


def get_ui_messages(session_id):
    sql = """
    SELECT message_json
    FROM ui_messages
    WHERE session_id = %s
    ORDER BY id ASC
    """
    rows = fetch_all(sql, (session_id,))
    if not rows:
        return []
    return [from_json(row["message_json"]) for row in rows]


def save_ui_message(session_id, data):
    data_json = to_json(data)
    sql = """
    INSERT INTO ui_messages (session_id, message_json)
    VALUES (%s, %s)
    """
    execute(sql, (session_id, data_json))


def save_config(session_id, config):
    config_json = to_json(config)
    sql = """
    UPDATE session_config
    SET config_json = %s
    WHERE session_id = %s
    """
    execute(sql, (config_json, session_id))

def renew_update(session_id):
    sql = """
    UPDATE sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE session_id = %s
    """
    execute(sql, (session_id,))

def get_session_list():
    sql = """
    SELECT session_id
    FROM sessions
    ORDER BY updated_at DESC
    """
    rows = fetch_all(sql)
    return [row["session_id"] for row in rows]

def get_latest_session_id():
    sql = """
    SELECT session_id
    FROM sessions
    ORDER BY updated_at DESC
    LIMIT 1
    """
    row = fetch_one(sql)
    if row is None:
        return None
    return row["session_id"]


def init_session_state():
    if "session_id" in st.session_state:
        return
    session_id = get_latest_session_id()
    if session_id is None:
        session_id = create_session()
        st.session_state.session_id = session_id
        st.session_state.ui_messages = []
        config = new_config()
        config_to_ui(config)
    else:
        st.session_state.session_id = session_id
        config = get_config(st.session_state.session_id)
        config_to_ui(config)
        st.session_state.ui_messages = get_ui_messages(st.session_state.session_id)

def save_ui(msg,air,session_id):
    save_ui_message(session_id, msg)
    save_ui_message(session_id, {"role": "assistant", "content": air})
    config = {"assistant_name": st.session_state.assistant_name,"major": st.session_state.major , "style": st.session_state.style, "rag_switch":st.session_state.rag_switch}
    save_config(session_id,config)
    renew_update(session_id)


def new_session():
    config = {"assistant_name": st.session_state.assistant_name, "major": st.session_state.major,
              "style": st.session_state.style, "rag_switch": st.session_state.rag_switch}
    save_config(st.session_state.session_id, config)
    renew_update(st.session_state.session_id)
    session_id = create_session()
    st.session_state.session_id = session_id
    st.session_state.ui_messages = []
    config = new_config()
    config_to_ui(config)


def swicth_session(session_id):
    st.session_state.session_id = session_id
    config = get_config(st.session_state.session_id)
    config_to_ui(config)
    st.session_state.ui_messages = get_ui_messages(st.session_state.session_id)

def delete_session(session_id):
    vector_path = get_vector_path(session_id)

    if st.session_state.get("session_id") == session_id:
        new_id = create_session()
        st.session_state.session_id = new_id
        st.session_state.ui_messages = []
        config = new_config()
        config_to_ui(config)

    sql = """
    DELETE FROM sessions
    WHERE session_id = %s
    """
    execute(sql, (session_id,))
    gc.collect()
    time.sleep(0.1)

    if vector_path and os.path.exists(vector_path):
        try:
            shutil.rmtree(vector_path)
        except PermissionError:
            st.warning("向量库文件暂时被 Chroma 占用，请刷新或重启 Streamlit 后再删除。")
    



class MySQLChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id):
        self.session_id = session_id
    @property
    def messages(self):
        sql = """
        SELECT message_json
        FROM chat_history
        WHERE session_id = %s
        ORDER BY id ASC
        """
        rows = fetch_all(sql, (self.session_id,))
        if not rows:
            return []

        messages_dict = [from_json(row["message_json"]) for row in rows]
        return messages_from_dict(messages_dict)
    def add_message(self, message):
        message_json = to_json(messages_to_dict([message])[0])

        sql = """
        INSERT INTO chat_history (session_id, message_json)
        VALUES (%s, %s)
        """
        execute(sql, (self.session_id, message_json))
    def clear(self):
        sql = """
        DELETE FROM chat_history
        WHERE session_id = %s
        """
        execute(sql, (self.session_id,))