import os
import bs4
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import getpass

# 设置环境变量，用于存储OpenAI的API密钥
os.environ["OPENAI_API_KEY"] = os.environ.get('OPENAI_API_KEY')


class Knowledge2Vector():
### 构造检索器 ###
# 初始化一个WebBaseLoader，用于从指定的网页路径加载文档
# loader = WebBaseLoader(
#     web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
#     bs_kwargs=dict(
#         parse_only=bs4.SoupStrainer(
#             class_=("post-content", "post-title", "post-header")
#         )
#     ),
# )

    def __init__(self,persist_dir,filename:str='/home/ubuntu/LSTM/src/testfile1/Levi Ackerman.pdf' ):
        """
        persist_dir :持久化向量数据库保存的地址
        filename : 文件路径
        """
        self.persist_dir = persist_dir
        self.filename = filename
        # 初始化一个基于GPT-3.5-turbo模型的聊天AI，并设置温度参数为0.7
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        self.embeddings=OpenAIEmbeddings()

    def load_file(self,filename):
        """
        分析并加载数据
        """
        # 判断文件类型
        if filename.lower().endswith(".pdf"):  # 如果文件是 PDF 格式
            loader = UnstructuredFileLoader(filename)   # 使用 UnstructuredFileLoader 加载器来加载 PDF 文件
            # text_splitor = CharacterTextSplitter()      # 使用 CharacterTextSplitter 来分割文件中的文本
            text_splitor =RecursiveCharacterTextSplitter(
                chunk_size = 200,
                chunk_overlap = 50
            )
            docs = loader.load_and_split(text_splitor)  # 加载文件并进行文本分割
        else:          # 如果文件不是 PDF 格式
            loader = UnstructuredFileLoader(filename, mode="elements")  # 使用 UnstructuredFileLoader 加载器以元素模式加载文件
            # text_splitor = CharacterTextSplitter()      # 使用 CharacterTextSplitter 来分割文件中的文本
            text_splitor =RecursiveCharacterTextSplitter(
                chunk_size = 200,
                chunk_overlap = 50
            )
            docs = loader.load_and_split(text_splitor)  # 加载文件并进行文本分割
        return docs    # 返回处理后的文件数据

    def vector_file(self):
        
        """向量化文档"""
        if os.path.exists(self.persist_dir): 
            vectorstore = Chroma(persist_directory=self.persist_dir, embedding_function=self.embeddings)
        else:
            # 加载要向量化的文档
            docs = self.load_file(filename=self.filename)

            # 初始化一个文本分割器，将文档分割为大小为1000字符的块，块之间重叠200字符
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            # 分割文档
            splits = text_splitter.split_documents(docs)
            # 使用Chroma和OpenAIEmbeddings将分割后的文本转换为向量，并创建检索器# 并持久化向量存储
            vectorstore = Chroma.from_documents(documents=splits, embedding=self.embeddings,persist_directory=self.persist_dir)
        return vectorstore
    
    
    def query_question(self,input):
        retriever = self.vector_file().as_retriever()

        ### 上下文化问题 ###
        # 定义一个系统提示，用于将聊天历史和最新的用户问题转换为一个独立的问题
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        # 创建一个聊天提示模板
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        # 创建一个考虑聊天历史的检索器
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        ### 回答问题 ###
        # 定义一个系统提示，用于指导AI助手使用检索到的上下文信息回答问题
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        # 创建一个聊天提示模板
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        # 创建一个处理文档的链条
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # 创建一个检索和回答问题的链条
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        ### 有状态地管理聊天历史 ###
        # 初始化一个存储，用于保存会话历史
        store = {}

        # 定义一个函数，用于获取指定会话ID的聊天历史
        def get_session_history(session_id: str) -> BaseChatMessageHistory:
            if session_id not in store:
                store[session_id] = ChatMessageHistory()
            return store[session_id]

        # 创建一个有状态的检索和生成回答的链条
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )

        
        res = conversational_rag_chain.invoke(
        {"input": input},
        config={
            "configurable": {"session_id": "abc123"}
        },  # constructs a key "abc123" in `store`.
        )["answer"]

        return res


    
    # 字典查询记录




# vector = Knowledge2Vector(persist_dir='/home/ubuntu/LSTM/src/testfile1_vecctor_db/Levi',filename='/home/ubuntu/LSTM/src/testfile1/Levi Ackerman.pdf')

# print(vector.query_question("兵长"))