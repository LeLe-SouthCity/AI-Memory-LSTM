import os
from utils.Vector import Knowledge2Vector
from utils.llm_utils import token_compute,LLM_Response
from utils.mysql_utils import MYSQL_Utils
from utils.file_utils import *
import streamlit as st

MYSQL_HOST = "localhost"  # 或者是远程服务器的IP地址/域名
MYSQL_USER = "lele"  # 你的 MySQL 用户名
MYSQL_PASSWORD = "Ogcloud123"  # 你的 MySQL 密码
MYSQL_DATABASE = "gptchat"  # 你想要连接的数据库名称

persist_dir='/home/ubuntu/LSTM/src/testfile1_vecctor_db/chat_history_db'
filename='/home/ubuntu/LSTM/src/testfile1/chat_history.docx'
sql_utils = MYSQL_Utils(mysql_host=MYSQL_HOST, mysql_user=MYSQL_USER, mysql_password=MYSQL_PASSWORD, mysql_database=MYSQL_DATABASE)      
get_ai_res = LLM_Response()
vector_utils = Knowledge2Vector(persist_dir=persist_dir,filename=filename)

# sql_utils.create_table()
# 初始化会话状态
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
# token计算
if 'tokens_compute' not in st.session_state:
    st.session_state['tokens_compute'] = 0
# 短期记忆记录
if 'short_history' not in st.session_state:
    st.session_state['short_history'] = []
# 用户输入记录
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = None
#长期记忆向量获取
if 'LsTM_Vector_get' not in st.session_state:
    st.session_state['LsTM_Vector_get'] = None
#总prompt计算
if 'eleven_total_prompt' not in st.session_state:
    st.session_state['eleven_total_prompt'] = None
# 初始化会话状态
if 'eleven_stream_chat_history' not in st.session_state:
    st.session_state['eleven_stream_chat_history'] = []
# token限制
if 'tokens_limit' not in st.session_state:
    st.session_state['tokens_limit'] = 10
 
 
  
# 处理用户输入和AI响应
def handle_chat(user_input,Ai_res):
    
    # 将用户输入添加到历史记录中并显示
    st.session_state['eleven_stream_chat_history'].append({'label': 'user', 'message': user_input})
    
    st.session_state['eleven_stream_chat_history'].append({'label': 'AI', 'message': Ai_res})




def show_STM():
    # 侧边栏显示聊天历史
    with st.sidebar:
        chat_history = sql_utils.get_chat_history()
        for user_input, gpt_response, timestamp in chat_history:
            
            st.session_state['chat_history'].append(user_input)
            st.session_state['chat_history'].append(gpt_response)
            # 短期记忆 添加
            st.session_state['short_history'].append(f"User: {user_input}\nGPT: {gpt_response}\nTime: {timestamp}")
        st.write(chat_history)    

  
# 显示聊天历史
def display_history():
    for message in st.session_state['eleven_stream_chat_history']:
        with st.chat_message(message["label"]):
            st.markdown(message["message"])
                
# Streamlit 应用
def main():
    
    st.title("Chat with GPT")
    
    # 使用 number_input 获取整数输入，并设置默认值为 1000
    tokens_limit = st.sidebar.number_input("短期 token 上限", min_value=1, value=st.session_state['tokens_limit'], step=1)
    # 避免切页失去数据
    if tokens_limit!=st.session_state['tokens_limit']:
        st.session_state['tokens_limit'] = tokens_limit
        
    if st.session_state['chat_history']:
        # 计算 tokens
        st.session_state['tokens_compute'] = token_compute(st.session_state['short_history'])

    # 聊天界面
    user_input = st.chat_input("Say something to GPT:")
    if st.session_state['tokens_compute'] > tokens_limit:
        
        
        # 1、保存----你可以在合适的地方调用这个函数，例如在会话结束时或定期保存聊天记录
        sql_utils.save_chat_history_from_db_to_json()
        delete_directory(directory_path=persist_dir)
        convert_json_to_word(json_file_path='chat_history.json',word_file_path=filename)
        # 2、删除chat_history数据库中的短期数据
        delete_query = "DELETE FROM chat_history"
        sql_utils.db.execute_query(delete_query)
        #3、清空网页的短期记忆
        st.session_state['short_history']=[]
        
    if st.session_state['tokens_compute']:
        st.sidebar.header(f"""Chat History tokens:{st.session_state['tokens_compute']}""")
    
    show_STM()   
            
    if user_input:
        # 用户输入
        st.session_state['user_input'] = user_input
        
        #向量数据获取
        info=vector_utils.query_question(input=st.session_state['user_input'] )
        
        # content = chat_completion.choices[0].message.content
        st.session_state['LsTM_Vector_get']=info
        
        st.session_state['LTM_Vector_get_all'] = info
        #总prompt 
        st.session_state['eleven_total_prompt'] = f"""
        

            下面是对话的历史记录
            {st.session_state['short_history']}
            
            下面是与用户输入相关的额外提示
            {st.session_state['LsTM_Vector_get']}
            
            你需要根据上面我给出的提示和用户对话，尽可能回答用户问题,
            务必遵循以下几个规则：
            1、当对话的历史记录与额外提示发生冲突时,以对话的历史记录的信息为准
        """
        ai_response = get_ai_res.get_openai_response(systemset =st.session_state['eleven_total_prompt'] , prompt=user_input)

        # 保存聊天记录到数据库
        sql_utils.save_chathistory_to_db(user_input, ai_response)
        handle_chat(user_input = user_input,Ai_res=ai_response)
        
    
if __name__ == "__main__":
    
    
    main()
    display_history()


        
        
        