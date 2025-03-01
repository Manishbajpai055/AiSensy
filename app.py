from dotenv import load_dotenv
load_dotenv()
import asyncio
import streamlit as st
import os
from scraper import scrape  # Importing the scrape function
from openai import OpenAI
from htmlTemplates import css, bot_template, user_template
import json
from parsePrompt import parse_prompt

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
You are an intelligent Q&A assistant that provides precise, context-aware answers based only on the provided content. Your goal is to ensure accuracy while understanding different phrasings of a question.

Response Guidelines:
	1.	Use Only Provided Context – Answer strictly based on the given content. If insufficient, respond: “The provided content does not contain enough information to answer this question.”
	2.	Understand Variations – Recognize different wordings, synonyms, and structures. Prioritize meaning over exact keyword matches.
	3.	Be Clear & Concise – Provide direct, relevant answers while ensuring completeness. Summarize when necessary.
	4.	Preserve Accuracy – Do not alter or misinterpret the content. If multiple sources exist, specify the source.
	5.	Handle Ambiguity Smartly – Ask for clarification if needed. If multiple answers exist, list them briefly.
	6.	Maintain Neutrality – Avoid opinions, speculations, or external knowledge. Ensure responses remain factual and unbiased.

"""

def get_suggested_prompts(context):
    prompt = f"Provide exactly 2 relevant questions in JSON array format, structured as follows: [{{\"question\": \"Your question here\"}}]. Do not include any other text. Use the given context: {context}"
    response =  client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    
    return response.choices[0].message.content


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


def setState(state,value):
    st.session_state[state] = value
    print(f"Button clicked: {value}")
    st.session_state.show_suggestions = False


def main():
    st.set_page_config(page_title="Web Content Q&A", page_icon="📚")
    # st.subheader("💬 Ask a Question")
    
    if "scraped_data" not in st.session_state:
        st.session_state.scraped_data = None
    if "question" not in st.session_state:
        st.session_state.question = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    # Get suggested prompts only once  
    if "show_suggestions" not in st.session_state:
        st.session_state.show_suggestions = True

    # Centered URL input before scraping
    # if not st.session_state.scraped_data:
    #     st.markdown("<h1 style='text-align: center;'>Web Content Q&A Tool</h1>", unsafe_allow_html=True)
    #     urls = st.text_area("Enter one or more URLs (separated by commas)", key="url_input")
        
    #     if st.button("Chat with Websites", key="scrape_button"):
    #         with st.spinner("Extracting content..."):
    #             url_list = [url.strip() for url in urls.split(",") if url.strip()]
    #             st.session_state.scraped_data = asyncio.run(scrape(url_list))
    #             st.session_state.chat_history = []  # Reset history for new content
    #             st.success("Content processed and stored!")
    #         st.rerun()

        
    if st.button("🆕 New Chat"):
        st.session_state.scraped_data = None
        st.session_state.chat_history = []
        st.rerun()
    
    if not st.session_state.scraped_data:
        st.markdown(
        """
        <div style="text-align: center;">
            <h3>🔹 How to Use the Tool 🔹</h3>
            <p><b>Enter URLs:</b> Provide one or more URLs separated by spaces or commas.</p>
            <p><b>Example:</b> <br> <code>https://www.example.com, https://www.another-site.com</code></p>
            <p><b>Ask Your Question:</b> Type your query after the URLs.</p>
            <p><b>Example:</b> <br> <code>https://www.example.com Summarize this page.</code></p>
            <p><b>Get Answers:</b> The tool extracts and summarizes content from the given URLs.</p>
        </div>
        """,
        unsafe_allow_html=True
        )


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
    question = st.chat_input("Enter Urls and Type your question here...", key="question_input")
    # Chat UI (Always at the Bottom)
    if st.session_state.show_suggestions and st.session_state.scraped_data:
        suggestion = get_suggested_prompts(st.session_state.scraped_data)
        suggestion = json.loads(suggestion)
        print("🚀 ~ suggestion:", suggestion)

        st.markdown("##### Suggestions:")
        cols = st.columns(len(suggestion))
        
        for i, item in enumerate(suggestion):
            print("🚀🚀🚀🚀🚀🚀 ~ item:", i, item)
            eachquestion = item["question"]
            if cols[i].button(eachquestion,on_click=setState,args=["question",eachquestion]):
                print("button")

    
    if question:
        parsed_data = parse_prompt(question)
        url, prompt = parsed_data["url"], parsed_data["prompt"]
        print("🚀 ~ url, prompt:", url, prompt)
        if not st.session_state.scraped_data and url:
            with st.spinner("Extracting content..."):
                st.session_state.scraped_data = asyncio.run(scrape(url))
                st.session_state.chat_history = []  # Reset history for new content
                st.success("Content processed and stored!")
                st.session_state.question = prompt
                # st.session_state.question = True
                # st.rerun()
        if st.session_state.scraped_data:
            last_five_history = st.session_state.chat_history[-5:]  # Pass last 5 messages
            answer = query_openai_api(st.session_state.scraped_data, prompt, assistant_placeholder, last_five_history)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            # Refresh to display the latest message
            # prompt = ""
            st.rerun()
        else:
            st.warning("⚠️ Please scrape content first before asking a question.")
    if st.session_state.question:
        last_five_history = st.session_state.chat_history[-5:]  # Pass last 5 messages
        answer = query_openai_api(st.session_state.scraped_data, st.session_state.question, assistant_placeholder, last_five_history)
        st.session_state.chat_history.append({"role": "user", "content": st.session_state.question})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.session_state.question = None
        # Refresh to display the latest message
        st.rerun()



if __name__ == "__main__":
    main()
