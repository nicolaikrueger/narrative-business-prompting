import streamlit as st
import io
import pymysql
import paramiko
import uuid
from openai import OpenAI
from sshtunnel import SSHTunnelForwarder

ssh_key_str = st.secrets["ssh_key"]

ssh_key_fileobj = io.StringIO(ssh_key_str)
ssh_key_paramiko = paramiko.Ed25519Key.from_private_key(ssh_key_fileobj)

server = SSHTunnelForwarder(
    (st.secrets["ssh_host"], 22),
    ssh_username=st.secrets["ssh_username"],
    ssh_pkey=ssh_key_paramiko,
    remote_bind_address=(st.secrets["db_host"], 3306),
)

def query_db(query, params=None):
    server.start()  # Start the SSH tunnel
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user=st.secrets["db_user"], 
            password=st.secrets["db_password"],
            db=st.secrets["db_name"],
            port=server.local_bind_port,
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn:
            with conn.cursor() as cursor:
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
    except Exception as e:
        print(f"Database query failed: {e}")
        return None
    finally:
        if conn: 
            try:
                conn.close()
            except Exception as e:
                print(f"Failed to close the database connection: {e}")
        server.stop()

def choose_random_task():
    result = query_db("SELECT uuid FROM tasks ORDER BY RAND() LIMIT 1")
    return result[0]["uuid"]

def homepage():
    st.title("Narrative Business Prompting")
    st.write("In this experiment, you will use a narrative Business Prompting Engine and experience its effects. This experiment will help develop and prove the use value of an assisted narrative business prompt engineering framework.")
    st.write("Please tell us something about yourself and get familiar with our data privacy policy (written in the sidebar).")

    #sidebar
    with st.sidebar:
        st.title("Data privacy policy")
        st.write("Put the legal stuff here...")

    # questions regarding the user
    tech_savviness = st.slider('Tech Savviness', 1, 5, 3)
    storytelling_experience = st.slider('Storytelling Experience', 1, 5, 3)
    casestudy_experience = st.slider('Case Study Experience', 1, 5, 3)

    age = st.number_input('Age', min_value=16)

    role = st.selectbox(
        'Role',
        ('Student', 'Lecturer / Professor / etc.', 'Professional', 'Other')
    )

    # Textbox for "Other" role
    other_role = ""  # Initialize an empty string for the "Other" role
    if role == 'Other':
        other_role = st.text_input('Please specify your role')

    if st.button("I agree to the terms, let's start the experiment"):
        task_id = choose_random_task()
        conversation_uuid = str(uuid.uuid4())
        st.session_state['task_id'] = task_id
        st.session_state['conversation_uuid'] = conversation_uuid
        sql = """
        INSERT INTO conversations 
        (uuid, task_id, start_time, end_time, accepted_tos, age, tech_savviness, storytelling_experience, casestudy_experience, role) 
        VALUES 
        (%s, %s, NOW(), null, true, %s, %s, %s, %s, %s);
        """
        values = (conversation_uuid, task_id, age, tech_savviness, storytelling_experience, casestudy_experience, role if role != 'Other' else other_role)
        rows_affected = query_db(sql, values)
        if rows_affected is None:
            st.error("Failed to start the experiment. Please try again.")
        else:
            st.session_state['page'] = 'experiment'
            st.rerun()


def experiment():
    query = query_db("SELECT * FROM tasks WHERE uuid = %s", st.session_state['task_id'])
    st.title("Narrative Business Prompting")

    # Set OpenAI API key from Streamlit secrets
    client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
                
    #sidebar
    with st.sidebar:
        st.title("Instructions")
        st.write(query[0]["description"])
        st.write(query[0]["goal"])

        if st.button("Submit my solution"):
            # Check if there are any messages in the chat history
            if st.session_state.messages and len(st.session_state.messages) > 0:
                st.session_state['page'] = 'finished_prompting'
                st.rerun()
            else:
                st.error('Please prompt your story first...')


def assess_your_story():
    st.title("Please assess your story.")
    st.write('Read your story and evaluate in terms of a) creativity/ innovation (generic v. Unique) b) applicability (once/ very specific / Needs Work v. General/ directly deployable ) c) how likely will you use this')
    st.write('0 = very low rank; 5 = very high rank')
    selfassessment = {}

    selfassessment["creativity"] = st.slider('Creativity', 0, 5, 3)

    selfassessment["innovaiton"] = st.slider('Innovation', 0, 5, 3)

    selfassessment["applicability"] = st.slider('Applicability', 0, 5, 3)

    selfassessment["actualuse"] = st.slider('How likely will you use this', 0, 5, 3)

    if st.button("Submit and finish experiment"):
        # TODO: Write to database
        st.session_state['page'] = 'checkout'
        st.rerun()


    with st.sidebar:
        st.title("Your Submission")
        st.write("Goes here")

def checkout():
    st.title("Thank you!")

    #ToDo remove restart button
    if st.button("Restart experiment"):
        st.session_state['page'] = 'Begin experiment'
        st.rerun()

def main():
    st.session_state.setdefault('page', 'Begin experiment')
    page = st.session_state['page']

    if page == 'Begin experiment':
        homepage()
    elif page == 'experiment':
        experiment()
    elif page == 'finished_prompting':
        assess_your_story()
    elif page == 'checkout':
        checkout()


if __name__ == "__main__":
    main()
