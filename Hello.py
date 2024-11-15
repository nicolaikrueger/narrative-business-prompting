import streamlit as st
import io
import pymysql
import paramiko
import uuid
from openai import OpenAI
from sshtunnel import SSHTunnelForwarder
import tiktoken

ssh_key_str = st.secrets["ssh_key"]
tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")

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

def presenting_the_task():
    st.title("Narrative Business Prompting Research")
    st.write("In this experiment, you will create a case study with the help of a Large Language Model (LLM). This research will help develop and prove the use value of an assisted narrative business prompting framework.")
    
    # check participation code which shall be stored in secrets
    participation_code = st.text_input("Please enter the participation code that you received from your researcher" ,type="password")
    participation_codes = (st.secrets["participation_code_nk"], st.secrets["participation_code_is"])

    if st.button("Let's start the experiment"):
        if participation_code in participation_codes:
            st.success("Participation code is correct.")
            st.session_state['page'] = 'legal_stuff'
            st.rerun()
        else:
            st.error("Invalid participation code.")

def legal_stuff():
    st.set_page_config(layout="wide") 
    st.title("Data privacy policy")
    # load markdown from legal_disclaimer.md
    with open("legal_disclaimer.md", "r") as file:
        legal_text = file.read()
    
    st.markdown(legal_text)
    if st.checkbox('I consent to the collection, processing, storage, and disclosure of my data as described in the legal disclaimer.'):
        if st.button("Consent"):
            st.session_state['page'] = 'homepage'
            st.rerun()

def homepage():
    st.set_page_config(layout="centered")
    st.title("Narrative Business Prompting")
    st.write("Please tell us something about yourself.")

    #sidebar
    # with st.sidebar:
       # st.title("Data privacy policy")
       # st.write("Put the legal stuff here...")

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

    if st.button("Let's start the experiment"):
        # if the user agrees to the terms of service, start the experiment
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
            st.session_state['round'] = 1
            st.session_state['sequence'] = 1
            st.session_state['page'] = 'experiment'
            st.rerun()


def experiment():
    query = query_db("SELECT * FROM tasks WHERE uuid = %s", st.session_state['task_id'])
    st.title("Create your own Case Study")
    st.info("""
            The input field below is linked to openai's large
            language model.
            Use the AI to create a case study about """ + query[0]["company"] + """
            who produces """ + query[0]["product"] + """ in """ + query[0]["location"] + """. """ + query[0]["company"] + """ is
            faced with a disruptive event and employs a strategy
            to overcome the crisis.
            \n**Step 1:**
            \nYour case study needs a disruptive event or crisis, such
            as: massive power outage, natural disaster, cyber
            attack, health emergency, criminal activity, product
            recall, production problems, bad publicity, losing
            customers to competitors, or any other... It's your
            choice! Start a conversation with the AI on what could
            be the crisis in your case study about """ + query[0]["company"] + """.
            Which disruptive event would you like to incorporate
            into your case study?
            \n**Step 2:**
            \nLet the AI generate a list of possible strategies to solve
            the crisis from step 1 and choose your favorite
            strategy. You can also create your own disruptive
            event and strategy for step 1 + 2.
            \n**Step 3:**
            \nLet the AI formulate your case study based on these
            parameters:
            [[company]] + [[location]] + [[product]] + [[disruptive
            event/ crisis]] + [[strategy]].
            """)
    if st.session_state['round'] == 2:
        #TODO: Add a prompt for the second round
        st.info("This is the second round of the experiment. We have prepared a prompt for you: \n ", icon="ℹ️")
    # Set OpenAI API key from Streamlit secrets
    client = OpenAI(api_key=st.secrets.OPENAI_API_KEY)

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Put your prompt here. What would you like to ask the AI?"):
        token_cost = 0
        token_cost += len(tokenizer.encode(prompt))
        store_message("user", prompt, token_cost)
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            token_cost = 0
            for response in client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ):
                current_response = (response.choices[0].delta.content or "")
                full_response += current_response
                token_cost += len(tokenizer.encode(current_response))
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        store_message("assistant", full_response, token_cost)
                
    #sidebar
    with st.sidebar:
        st.write("""
            A case study is a research method that provides a detailed and contextualized analysis of a
            phenomenon with the goal of understanding the rationale behind decision-making processes and their
            resulting outcomes. Effective case studies are comprehensive and incorporate diverse perspectives,
            substantiated by evidence. They are presented in a compelling manner that engages the reader.
        """)

        st.write("When you are finished, proceed to the next step.")
        if st.button("Proceed to the next step"):
            # Check if there are any messages in the chat history
            if st.session_state.messages and len(st.session_state.messages) > 0:
                st.session_state['page'] = 'finished_prompting'
                st.rerun()
            else:
                st.error('Please prompt your story first...')


def store_message(role, content, token_cost=0):
        st.session_state.messages.append({"role": role, "content": content})
        sql = """
        INSERT INTO messages (uuid, conversation_uuid, token_cost, context, message, sequence, round)
        VALUES (UUID(), %s, %s, %s, %s, %s, %s);    
        """
        query_db(sql, (st.session_state["conversation_uuid"], token_cost, role, content, st.session_state["sequence"], st.session_state["round"]))
        st.session_state["sequence"] += 1

def assess_your_story():
    st.title("Please assess your story.")
    st.write('Read your story and evaluate in terms of a) accuracy to fit with the case, b) probability to use it in a hypothetic lecture, c) level of creativity and d) applicability for a hypothetic lecture dealing with that case.')
    st.write('0 = very low rank; 5 = very high rank')
    selfassessment = {}

    selfassessment["accuracy"] = st.select_slider('Accuracy', options=['very general', 'somewhat general', 'undecided', 'somewhat specific', 'very specific'])

    selfassessment["probability"] = st.select_slider('Probability', options=['very realistic', 'somewhat realistic', 'undecided', 'somewhat far-fetched', 'very far-fetched'])

    selfassessment["creativity"] = st.select_slider('Creativity', options=['very generic', 'somewhat generic', 'undecided', 'somewhat inspiring', 'very inspiring'])

    selfassessment["applicability"] = st.select_slider('Applicability', options=['ready to use', 'almost ready to use', 'undecided', 'needs some work', 'needs extensive work'])

    button_text = "Submit and finish experiment"
    if st.button(button_text):
        query_db("UPDATE conversations SET end_time = NOW() WHERE uuid = %s", st.session_state["conversation_uuid"])
        for key, value in selfassessment.items():
            print(f"Inserting {key}: {value}")
            sql = """
            INSERT INTO ratings (uuid, conversation_uuid, rating_type_id, rating, round)
            VALUES (UUID(), %s, %s, %s, %s);
            """
            result = query_db(sql, (st.session_state["conversation_uuid"], key, value, st.session_state["round"]))
            if result is None:
                print(f"Failed to insert {key}: {value}")  # Error logging
            else:
                print(f"Successfully inserted {key}: {value}, Rows affected: {result}")  # Success logging
        st.session_state['page'] = 'checkout'
        st.rerun()


    with st.sidebar:
        st.title("Your Submission")
        st.write("You're almost done! Please assess your story and submit your evaluation.")

def checkout():
    st.title("Thank you for your participation!")
    st.write("You may close this tab now.")
    st.balloons()

def main():
    st.session_state.setdefault('page', 'presenting_the_task')
    page = st.session_state['page']

    if page == 'presenting_the_task':
        presenting_the_task()
    elif page == 'legal_stuff':
        legal_stuff()
    elif page == 'homepage':
        homepage()
    elif page == 'experiment':
        experiment()
    elif page == 'finished_prompting':
        assess_your_story()
    elif page == 'checkout':
        checkout()


if __name__ == "__main__":
    main()
