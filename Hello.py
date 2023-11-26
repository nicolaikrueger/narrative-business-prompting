import streamlit as st
from openai import OpenAI
client = OpenAI()
client = OpenAI(st.secrets["OPENAI_API_KEY"])

def homepage():
    st.title("Narrative Business Prompting")
    st.write("In this experiment, you will use a narrative Business Prompting Engine and experience its effects. This experiment will help develop and prove the use value of an assisted narrative business prompt engineering framework.")
    st.write(st.secrets.my_little_secret)
    if st.button("Begin experiment"):
        st.session_state['page'] = 'experiment'
        st.experimental_rerun()


def experiment():
    st.title("Narrative Business Prompting")

    # Set OpenAI API key from Streamlit secrets
    

    #if "openai_model" not in st.session_state:
    #    st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    #chat interface
    if prompt := st.chat_input("What do you want to learn?"):
        #st.session_state.messages.append({"role": "user", "content": prompt})
        #with st.chat_message("user"):
        #    st.markdown(prompt)

        #response = openai.ChatCompletion.create(
        #    model=st.session_state["openai_model"],
        #    messages=st.session_state.messages
        #)
        #full_response = response.choices[0].message["content"]

        #st.session_state.messages.append({"role": "assistant", "content": full_response})
        #with st.chat_message("assistant"):
        #    st.markdown(full_response)


        completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
            {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
        ]
        )

        #print(completion.choices[0].message)
        with st.chat_message("assistant"):
            st.markdown(completion.choices[0].message)

    #sidebar
    with st.sidebar:
        st.title("Instructions")
        st.write("Your text/instructions go here...")

        if st.button("Submit my solution"):
            # Check if there are any messages in the chat history
            if st.session_state.messages and len(st.session_state.messages) > 0:
                st.session_state['page'] = 'finished_prompting'
                st.experimental_rerun()
            else:
                st.error('Please prompt your story first...')


def assess_your_story():
    st.title("Please assess your story.")
    st.write('Read your story and evaluate in terms of a) creativity/ innovation (generic v. Unique) b) applicability (once/ very specific / Needs Work v. General/ directly deployable ) c) how likely will you use this')
    st.write('0 = very low rank; 5 = very high rank')

    selfassessment_creativity = st.slider('Creativity', 0, 5, 3)

    selfassessment_innovaiton = st.slider('Innovation', 0, 5, 3)

    selfassessment_applicability = st.slider('Applicability', 0, 5, 3)

    selfassessment_actualuse = st.slider('How likely will you use this', 0, 5, 3)

    if st.button("Submit and finish experiment"):
        st.session_state['page'] = 'checkout'
        st.experimental_rerun()


    with st.sidebar:
        st.title("Your Submission")
        st.write("Goes here")

def checkout():
    st.title("Thank you!")

    #ToDo remove restart button
    if st.button("Restart experiment"):
        st.session_state['page'] = 'Begin experiment'
        st.experimental_rerun()

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
