import streamlit as st
from dotenv import load_dotenv
import chat_session
import time
import re
import helper
import chat_session
from together import Together
import os


def stream_data(response):
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.1)


def handle_userinput(user_input):
    for message in st.session_state.chat_session.history:
        with st.chat_message((message["role"])):
            st.markdown(message['content'])

def main():
    load_dotenv()
    st.set_page_config(
        page_title="Echo.me",
        page_icon='echoMe.png',
        layout="wide"
    )

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = chat_session.chat_session()
    
    
    st.header("Alter Ego")
    
    with open("Profile.md", "r", encoding="utf-8") as file:
        markdown_content = file.read()

    # Regular expression patterns to match headings and sections
    heading_pattern = re.compile(r"(##\s+\*\*(.*?)\*\*)")
    content_pattern = re.compile(r"(?:@[\w]+|\- [\w\s]+|[a-zA-Z,.\s]+)")

    # Parse the markdown into sections
    sections = []
    for match in heading_pattern.finditer(markdown_content):
        heading = match.group(2)
        start = match.end()
        
        # Find the end of the section or next heading
        next_match = heading_pattern.search(markdown_content, start)
        end = next_match.start() if next_match else len(markdown_content)
        
        # Extract content in this section
        content = markdown_content[start:end].strip()
        sections.append({"heading": heading, "content": content})

    # Create chunks
    chunks = []
    for section in sections:
        heading = section['heading']
        content = section['content']
        chunk_text = f"{heading}: {content}"
        chunks.append(chunk_text)
        
    #embade and vectorize
    vector_db = helper.load_vector_db(chunks)

    llm = Together(api_key=os.environ.get('TOGETHER_API_KEY'))
    
    st.session_state.llm = llm
    
    st.session_state.vdb = vector_db

    if("vdb" in st.session_state):
        user_query = st.chat_input("Ask Your Question")        
        if user_query:
            st.session_state.chat_session.history.append({'role': 'user', 'content': user_query})
            handle_userinput(user_query)
            response = helper.generate_response(st.session_state.vdb, user_query, st.session_state.llm)
            st.session_state.chat_session.history.append({'role': 'assistant', 'content': response})
            with st.chat_message("assistant"):
                st.write_stream(stream_data(response))

if __name__ == "__main__":
    main()