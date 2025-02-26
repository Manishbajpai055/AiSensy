from dotenv import load_dotenv
load_dotenv()
import asyncio
import streamlit as st
import os
from scraper import scrape  # Importing the scrape function
from openai import OpenAI
from htmlTemplates import css, bot_template, user_template

# Initialize OpenAI Client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# PINECONE_ENV = os.environ.get("PINECONE_ENV")


# # Get text embedding
# def get_embedding(text, model="text-embedding-3-small"):
#     text = text.replace("\n", " ")
#     response = client.embeddings.create(input=text, model=model)
#     return response.data[0].embedding

# Query Pinecone and OpenAI
# def query_pinecone_and_openai(question, index_name):
#     pinecone_client = st.session_state.pinecone_client
#     index = pinecone_client.Index(index_name)
#     query_embedding = get_embedding(question)
#     results = index.query(vector=query_embedding, top_k=4, include_metadata=True, namespace=index_name)
#     return results if results else None


system_prompt="""
You are an intelligent Q&A assistant that provides precise, context-aware answers based on extracted web content. Your goal is to respond accurately using only the given context while maintaining clarity and conciseness.

Response Guidelines:
	1.	Use Only the Provided Context
	•	Do not generate answers from external knowledge.
	•	If the context lacks sufficient information, respond with:
“The provided content does not contain enough information to answer this question.”
	2.	Be Concise & Relevant
	•	Provide direct and clear answers without unnecessary details.
	•	Summarize when needed but ensure completeness.
	3.	Preserve Source Integrity
	•	If multiple sources exist, specify which source the answer is based on (if applicable).
	•	Do not alter or misinterpret the extracted content.
	4.	Handle Unclear Queries Smartly
	•	If the question is ambiguous, ask for clarification instead of assuming.
	•	If multiple possible answers exist, list them briefly.
	5.	Maintain a Neutral & Informative Tone
	•	Avoid opinions, speculations, or external assumptions.
	•	Ensure responses are factual and unbiased based on the provided data.

"""


# Query OpenAI
def query_openai_api(context, question, assistant_placeholder,history):
    prompt = f"{question} Context: {context}"
    print("🚀 ~ context:", question)
    messages = [
            {"role":"system","content":system_prompt}
    ]
    messages.extend(history)
    # print("messages",messages)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[*messages,{"role":"system","content":prompt}],
        temperature=0.6,
        # top_p=0.5,
        stream=True,
        stream_options={"include_usage": True}
    )
    
    assistant_message =""
    for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    assistant_message += delta.content
                    # Update the placeholder with the new content
                    assistant_placeholder.markdown(
                        bot_template.replace("{{MSG}}", assistant_message),
                        unsafe_allow_html=True
                    )
            if chunk.usage is not None:
                print("\n🔹 Usage Details:")
                print(f"Prompt Tokens: {chunk.usage.prompt_tokens}")
                print(f"Completion Tokens: {chunk.usage.completion_tokens}")
                print(f"Total Tokens: {chunk.usage.total_tokens}")
    print(assistant_message)
    return assistant_message

def main():
    st.set_page_config(page_title="Web Content Q&A", page_icon="📚")
    # st.subheader("💬 Ask a Question")
    
    if "scraped_data" not in st.session_state:
        st.session_state.scraped_data = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Centered URL input before scraping
    if not st.session_state.scraped_data:
        st.markdown("<h1 style='text-align: center;'>Web Content Q&A Tool</h1>", unsafe_allow_html=True)
        urls = st.text_area("Enter one or more URLs (separated by commas)", key="url_input")
        
        if st.button("Chat with Websites", key="scrape_button"):
            with st.spinner("Extracting content..."):
                url_list = [url.strip() for url in urls.split(",") if url.strip()]
                st.session_state.scraped_data = asyncio.run(scrape(url_list))
                st.session_state.chat_history = []  # Reset history for new content
                st.success("Content processed and stored!")
            st.rerun()

    else:
        # New Chat Button
        
        if st.button("🆕 New Chat"):
            st.session_state.scraped_data = None
            st.session_state.chat_history = []
            st.rerun()
        
        for i, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.write(
                    user_template.replace("{{MSG}}", message["content"]),
                    unsafe_allow_html=True,
                )   
            else:
                st.write(
                    bot_template.replace("{{MSG}}", message["content"]),
                    unsafe_allow_html=True,
                )
        assistant_placeholder = st.empty()
        # Chat UI (Always at the Bottom)
        
        question = st.chat_input("Type your question here...", key="question_input")
        if question:
            if st.session_state.scraped_data:
                last_five_history = st.session_state.chat_history[-5:]  # Pass last 5 messages
                answer = query_openai_api(st.session_state.scraped_data, question, assistant_placeholder, last_five_history)
                st.session_state.chat_history.append({"role": "user", "content": question})
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                # Refresh to display the latest message
                st.rerun()
                question = ""
            else:
                st.warning("⚠️ Please scrape content first before asking a question.")



if __name__ == "__main__":
    main()
