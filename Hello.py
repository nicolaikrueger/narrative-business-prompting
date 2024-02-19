import streamlit as st
import io
import pymysql
from openai import OpenAI
from sshtunnel import SSHTunnelForwarder

ssh_key_str = st.secrets["ssh_key"]

ssh_key_fileobj = io.StringIO(ssh_key_str)

server = SSHTunnelForwarder(
    (st.secrets["ssh_host"], 22),
    ssh_username=st.secrets["ssh_username"],
    ssh_pkey=ssh_key_fileobj,
    remote_bind_address=(st.secrets["db_host"], 3306),
)

def query_db(query):
    server.start()  # Start the SSH tunnel
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            user=st.secrets["db_user"], 
            password=st.secrets["db_password"],
            db=st.secrets["db_name"],
            port=server.local_bind_port
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                return result
    except Exception as e:
        print(f"Database query failed: {e}")
        return None
    finally:
        conn.close() if 'conn' in locals() or 'conn' in globals() else None
        server.stop()  # Stop the SSH tunnel

def homepage():
    st.title("Narrative Business Prompting")
    st.write("In this experiment, you will use a narrative Business Prompting Engine and experience its effects. This experiment will help develop and prove the use value of an assisted narrative business prompt engineering framework.")

    if st.button("Begin experiment"):
        st.session_state['page'] = 'experiment'
        st.rerun()


def experiment():
    query = query_db("SELECT * FROM tasks")
    st.write(query)
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
        st.write("Your text/instructions go here...")

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
