import streamlit as st
import io
import pymysql
import paramiko
from sshtunnel import SSHTunnelForwarder
import tiktoken
import json
from datetime import date, datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

ssh_key_str = st.secrets["ssh_key"]
print("loading tokenizer...")
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
print("done loading tokenizer")

ssh_key_fileobj = io.StringIO(ssh_key_str)
ssh_key_paramiko = paramiko.Ed25519Key.from_private_key(ssh_key_fileobj)

server = SSHTunnelForwarder(
    (st.secrets["ssh_host"], 22),
    ssh_username=st.secrets["ssh_username"],
    ssh_pkey=ssh_key_paramiko,
    remote_bind_address=(st.secrets["db_host"], 3306),
)

server.start()  # Start the SSH tunnel
conn = pymysql.connect(
    host='127.0.0.1',
    user=st.secrets["db_user"], 
    password=st.secrets["db_password"],
    db=st.secrets["db_name"],
    port=server.local_bind_port,
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

def query_db(query, params=None):
    if params is None:
        cursor.execute(query)
    else:
        cursor.execute(query, params)
    if query.strip().upper().startswith('SELECT'):
        result = cursor.fetchall()
        return result
    else:
        conn.commit()
        return cursor.rowcount

def export_data():
    query = "SELECT * FROM conversations"
    conversations = query_db(query)
    query = "SELECT * FROM tasks"
    tasks = query_db(query)

    for conversation in conversations:
        # append messages and task to the conversation
        for task in tasks:
            if task["uuid"] == conversation["task_id"]:
                conversation["task"] = task
        query = "SELECT * FROM messages WHERE conversation_uuid = %s"
        params = (conversation["uuid"],)
        messages = query_db(query, params)
        conversation["messages"] = messages
        # append ratings to the conversation
        query = "SELECT * FROM ratings WHERE conversation_uuid = %s"
        params = (conversation["uuid"],)
        ratings = query_db(query, params)
        conversation["ratings"] = ratings

    # write result to a json
    with open("conversations.json", "w") as f:
        print("Writing to conversations.json")
        json.dump(conversations, f, default=json_serial)
        print("Done writing to conversations.json")

if __name__ == "__main__":
    print("Exporting data...")
    export_data()