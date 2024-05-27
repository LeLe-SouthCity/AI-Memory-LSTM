import json
import os
import mysql.connector

from mysql.connector import Error

import datetime
class MY_SQL_API:
    """
    
    # 使用示例
    db = MY_SQL_API('localhost', 'your_username', 'your_password', 'your_database')

    # 插入数据
    insert_query = "INSERT INTO your_table (column1, column2) VALUES (%s, %s)"
    db.insert(insert_query, ('value1', 'value2'))

    # 查询数据
    select_query = "SELECT * FROM your_table"
    results = db.select(select_query)
    for result in results:
        print(result)

    # 更新数据
    update_query = "UPDATE your_table SET column1 = %s WHERE column2 = %s"
    db.update(update_query, ('new_value', 'value2'))

    # 删除数据
    delete_query = "DELETE FROM your_table WHERE column2 = %s"
    db.delete(delete_query, ('value2',))
    
    """
    def __init__(self, host, user, password, database=None):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()
            
    def connect(self):
        """
        数据库连接
        """
        try:
            if self.database:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
            else:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password
                )
        except Error as e:
            print(f"Error: '{e}'")

    def create_database(self, database_name):
        """
        数据库创建
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"CREATE DATABASE {database_name}")
            print(f"Database `{database_name}` created successfully")
        except Error as e:
            print(f"Error: '{e}'")
        finally:
            cursor.close()
            
    def execute_query(self, query, params=None):
        """
        数据库 —— 执行任何传递给它的 SQL 查询。这个方法可以用来创建、读取、更新或删除数据库中的数据。方法的参数说明如下：
        """
        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            print(f""" Query successful""")
        except Error as e:
            print(f"Error: '{e}'")
        finally:
            cursor.close()

    def insert(self, query, val):
        """向数据库表中插入一条新记录。"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, val)
            self.connection.commit()
            print("Record inserted successfully")
        except Error as e:
            print(f"Error: '{e}'")

    def select(self, query):
        """从数据库表中检索数据"""
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Error as e:
            print(f"Error: '{e}'")
            return None

    def update(self, query, val):
        """更新数据库表中的现有记录。"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, val)
            self.connection.commit()
            print("Record updated successfully")
        except Error as e:
            print(f"Error: '{e}'")

    def delete(self, query, val):
        """从数据库表中删除记录。"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, val)
            self.connection.commit()
            print("Record deleted successfully")
        except Error as e:
            print(f"Error: '{e}'")


class MYSQL_Utils(MY_SQL_API):
    
    def __init__(self,mysql_host, mysql_user, mysql_password, mysql_database):
        self.db = MY_SQL_API(host=mysql_host, user=mysql_user, password=mysql_password,database= mysql_database)
    
    def create_table(self):
        """创建表"""
        create_table_query1 = """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_input TEXT,
                gpt_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.db.execute_query(create_table_query1)
    
    # 保存聊天记录到数据库
    def save_chathistory_to_db(self,user_input, gpt_response):
        """保存聊天记录到数据库"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        insert_query = """
            INSERT INTO chat_history (user_input, gpt_response, timestamp)
            VALUES (%s, %s, %s)
        """
        self.db.execute_query(insert_query, (user_input, gpt_response, timestamp))    
     
    # 从数据库获取聊天历史
    def get_chat_history(self):
        """从数据库获取聊天历史"""
        select_query = "SELECT user_input, gpt_response, timestamp FROM chat_history"
        try:
            results = self.db.select(select_query)
            return results if results is not None else []
        except Exception as e:
            print(f"An error occurred: {e}")
            return [] 
     
    # 定义一个函数来处理 datetime 对象，使其可被 JSON 序列化
    def json_serializable(obj):
        """定义一个函数来处理 datetime 对象，使其可被 JSON 序列化"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")

    def save_chat_history_from_db_to_json(self,file_path='chat_history.json'):
        """# 从数据库获取聊天历史并保存到 JSON 文件"""
        new_chat_history = []
        try:
            chat_history_tuples = self.get_chat_history()
            # 将元组转换为字典列表
            new_chat_history = [
                {
                    'user_input': record[0],
                    'gpt_response': record[1],
                    'timestamp': str(record[2])
                }
                for record in chat_history_tuples
            ]
            # st.info(new_chat_history)
        except Exception as e:
            print(f"mysql对话历史记录获取失败: {e}")
            return

        try:
            # 如果文件存在，读取旧聊天历史
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    existing_chat_history = json.load(json_file)
            else:
                existing_chat_history = []
                
            
            # 将新数据追加到旧数据中
            combined_chat_history  = existing_chat_history + new_chat_history

            # 根据时间戳排序聊天历史 (降序，即最新的记录在前)
            sorted_chat_history = sorted(combined_chat_history, key=lambda x: x['timestamp'], reverse=True)
            
            # 保存更新后的聊天历史到 JSON 文件
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(sorted_chat_history, json_file, default=self.json_serializable, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"An error occurred while saving to JSON: {e}")
    