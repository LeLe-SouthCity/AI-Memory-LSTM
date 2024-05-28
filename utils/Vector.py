import os
import shutil
import bs4
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import getpass

# 设置环境变量，用于存储OpenAI的API密钥
os.environ["OPENAI_API_KEY"] = os.environ.get('OPENAI_API_KEY')


class Knowledge2Vector():
    
    def __init__(self,persist_dir,filename:str ):
        """
        persist_dir :持久化向量数据库保存的地址
        filename : 文件路径
        """
        self.persist_dir = persist_dir
        self.filename = filename
        # 初始化一个基于GPT-3.5-turbo模型的聊天AI，并设置温度参数为0.7
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        self.embeddings=OpenAIEmbeddings()
        
    def delete_file_vector(self):
        if os.path.exists(self.persist_dir):
            for filename in os.listdir(self.persist_dir):
                file_path = os.path.join(self.persist_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
    def load_file(self):
        """
        分析并加载数据
        """
        # 判断文件类型
        if self.filename.lower().endswith(".pdf"):  # 如果文件是 PDF 格式
            loader = UnstructuredFileLoader(self.filename)   # 使用 UnstructuredFileLoader 加载器来加载 PDF 文件
            # text_splitor = CharacterTextSplitter()      # 使用 CharacterTextSplitter 来分割文件中的文本
            text_splitor =RecursiveCharacterTextSplitter(
                chunk_size = 200,
                chunk_overlap = 50
            )
            docs = loader.load_and_split(text_splitor)  # 加载文件并进行文本分割
        else:          # 如果文件不是 PDF 格式
            loader = UnstructuredFileLoader(self.filename, mode="elements")  # 使用 UnstructuredFileLoader 加载器以元素模式加载文件
            # text_splitor = CharacterTextSplitter()      # 使用 CharacterTextSplitter 来分割文件中的文本
            text_splitor =RecursiveCharacterTextSplitter(
                chunk_size = 200,
                chunk_overlap = 50
            )
            docs = loader.load_and_split(text_splitor)  # 加载文件并进行文本分割
        return docs    # 返回处理后的文件数据

    def vector_file(self,updata='false'):
        
        """向量化文档"""
        if updata == 'false':
            vectorstore = Chroma(persist_directory=self.persist_dir, embedding_function=self.embeddings)
        else:
            # 加载要向量化的文档
        
            docs = self.load_file()

            # 更新 metadata 数据
            new_docs = []             # 初始化一个空列表来存储新文档
            for doc in docs:
                # 更新文档的 metadata，将 "source" 字段的值替换为不包含 DATASETS_DIR 的相对路径
                doc.metadata = {"source": doc.metadata["source"].replace(self.persist_dir, "")} 
                print("文档2向量初始化中, 请稍等...", doc.metadata)  # 打印正在初始化的文档的 metadata
                new_docs.append(doc)  # 将文档添加到新文档列表
            
            # 使用Chroma和OpenAIEmbeddings将分割后的文本转换为向量，并创建检索器# 并持久化向量存储
            vectorstore = Chroma.from_documents(documents=new_docs, embedding=self.embeddings,persist_directory=self.persist_dir)
        return vectorstore
    
    
    def query_question(self,input):
        retriever = self.vector_file().as_retriever(
                        search_type="mmr",
                        search_kwargs={'k': 3, 'lambda_mult': 0.5}
                    )
        documents=retriever.invoke(input = input)
        # 使用列表推导式提取所有的 page_content
        page_contents = [doc.page_content for doc in documents]

        # 将所有的 page_content 合并成单一的字符串
        full_content = "\n".join(page_contents)
        return full_content


    
    # 字典查询记录




vector = Knowledge2Vector(persist_dir='/home/ubuntu/LSTM/src/testfile1_vecctor_db/test2',filename='/home/ubuntu/LSTM/src/testfile1/chat_history.docx')
while True:
        question = input("请输入内容：")
        print(vector.query_question(question))
