import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import shutil
import Multi_modal_process
import mysql_message
load_dotenv()

embedding = OpenAIEmbeddings(
    api_key=os.getenv("QWEN_API_KEY1"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="text-embedding-v3",
    check_embedding_ctx_length=False
)



def split_documents(docs, chunk_size=500, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", ".", "!", "?", ",", ""]
    )
    return text_splitter.split_documents(docs)


def vector_store(chunks, session_id):
    chunks = [
        doc for doc in chunks
        if isinstance(doc.page_content, str) and doc.page_content.strip()
    ]
    persist_dir = mysql_message.get_vector_path(session_id)
    if not chunks:
        raise ValueError("文档切片为空，无法创建向量存储")
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        vectordb = load_vector(session_id)
        if chunks:
            vectordb.add_documents(chunks)
    else:
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embedding,
            persist_directory=persist_dir
        )


def load_vector(session_id):
    persist_dir = mysql_message.get_vector_path(session_id)
    vectordb = Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding
    )
    return vectordb


def rag_prompt(user_input, vectordb, top_k=3):
    retriever_docs = vectordb.similarity_search(
        query=user_input,
        k=top_k
    )
    # retriever = vectordb.as_retriever(search_kwargs={"k": top_k})
    # retriever_docs = retriever.get_relevant_documents(user_input)  or  retriever.invoke(user_input)
    context_text = "\n\n".join([d.page_content for d in retriever_docs])
    text_prompt = f"请根据以下文档回答问题:\n{context_text}\n用户问题: {user_input}"
    return text_prompt
# def rag_chain(chat_model,vectordb, prompt):
#     chain = ConversationalRetrievalChain.from_llm(
#         llm=chat_model,
#         retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
#         return_source_documents=True,
#         combine_docs_chain_kwargs={"prompt": prompt}
#     )
#     return chain
def rag_file_process(user_files,session_id):
    all_docs = []
    for i in user_files:
        file_path = Multi_modal_process.file_stream_to_path(i)
        docs = Multi_modal_process.load_documents(file_path, i.name)
        all_docs.extend(docs)
    chunks = split_documents(all_docs)
    vector_store(chunks, session_id)