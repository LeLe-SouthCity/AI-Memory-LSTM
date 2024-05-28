from flask import Flask, request, jsonify
from utils.Vector import Knowledge2Vector
from utils.llm_utils import token_compute, LLM_Response
from utils.mysql_utils import MYSQL_Utils
from utils.file_utils import *

app = Flask(__name__)
# 数据库和文件配置
MYSQL_HOST = "localhost"  # 或者是远程服务器的IP地址/域名
MYSQL_USER = "lele"  # 你的 MySQL 用户名
MYSQL_PASSWORD = "Ogcloud123"  # 你的 MySQL 密码
MYSQL_DATABASE = "gptchat"  # 你想要连接的数据库名称

persist_dir = '/home/ubuntu/LSTM/src/testfile1_vecctor_db/chat_history_db'
filename = '/home/ubuntu/LSTM/src/testfile1/chat_history.docx'

# 实例化数据库工具
sql_utils = MYSQL_Utils(mysql_host=MYSQL_HOST, mysql_user=MYSQL_USER, mysql_password=MYSQL_PASSWORD, mysql_database=MYSQL_DATABASE)
get_ai_res = LLM_Response()

# 获取短期历史记录的函数
def getshort_history():
    history = []
    chat_history = sql_utils.get_chat_history()
    for user_input, gpt_response, timestamp in chat_history:
        history.append(f"User: {user_input}\nGPT: {gpt_response}\nTime: {timestamp}")
    return history

# 主处理函数
def process_user_input(user_input):
    # 实例化向量工具
    vector_utils = Knowledge2Vector(persist_dir=persist_dir, filename=filename)

    # 获取短期历史记录
    short_history = getshort_history()

    # 计算token数量
    tokens_limit = 10
    short_history_tokens = token_compute(messages=short_history)

    # 如果超过token限制，更新向量数据库并清空短期历史
    if short_history_tokens > tokens_limit:
        sql_utils.save_chat_history_from_db_to_json()
        vector_utils.vector_file(updata='true')  # 假设vector_file方法接受一个update参数
        convert_json_to_word(json_file_path='chat_history.json', word_file_path=filename)
        
        # 删除chat_history数据库中的短期数据
        delete_query = "DELETE FROM chat_history"
        sql_utils.db.execute_query(delete_query)

    # 查询长期历史记录
    long_history = vector_utils.query_question(input=user_input)

    # 构建系统设置和提示
    systemset = f"""
        下面是对话的历史记录
        {short_history}

        下面是与用户输入相关的额外提示
        {long_history}

        你需要根据上面我给出的提示和用户对话，尽可能回答用户问题,
        务必遵循以下几个规则：
        1、当对话的历史记录与额外提示发生冲突时,以对话的历史记录的信息为准
    """

    # 获取AI响应
    ai_response = get_ai_res.get_openai_response(systemset=systemset, prompt=user_input)

    # 保存聊天记录到数据库
    sql_utils.save_chathistory_to_db(user_input, ai_response)

    # 返回AI响应
    return ai_response


# 定义路由和视图函数
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('input')
    
    if not user_input:
        return jsonify({'error': 'No input provided'}), 400

    try:
        output = process_user_input(user_input)
        return jsonify({'response': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
