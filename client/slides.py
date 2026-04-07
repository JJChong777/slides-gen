import streamlit as st
from modules import API_URL_SLIDE, generate_file_name, PPTX_TEMPLATE_FILES, LLM_MODEL_MAX_INPUT_LENGTH
import time
from io import BytesIO
import requests
    
def main():
    st.title("Create a slide deck with AI")

 # Initialize session state
    if "messages_slides" not in st.session_state:
        st.session_state.messages_slides = [{"role": "assistant", "content": "Hi, I'm the Slide Deck Chatbot! Type in a prompt to get started", "ok": True, "pptx_name": None}]
    if "slides_cache" not in st.session_state:
        st.session_state.slides_cache = {}
    if "chat_disabled_slides" not in st.session_state:
        st.session_state.chat_disabled_slides = False
    if "last_prompt_text_slides" not in st.session_state:
        st.session_state.last_prompt_text_slides = None

    suggested_questions = [
        "Introduction to Machine Learning",
        "Sun Tzu Art of War",
        "Anti Air Missile Systems Explained"
    ]

    with st.chat_message("assistant"):
        st.markdown("Try asking:")
        with st.form("suggested_question_form"):
            selected_question = st.selectbox(
                "What suggested topic would you like to choose for slides?",
                suggested_questions,
                index=None,
                placeholder="Select suggested question...",
            )
            submitted = st.form_submit_button('Submit Question')
            if submitted and selected_question:
                # Set the prompt text state directly when a suggestion is clicked
                st.session_state.last_prompt_text_slides = selected_question
                st.session_state.chat_disabled_slides = True
                st.session_state.messages_slides.append({
                    "role": "user", 
                    "content": f"Prompt: {selected_question}"
                })
                st.rerun()
    
    # Render chat history
    for msg in st.session_state.messages_slides:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            if not msg["ok"]:
                with st.chat_message("assistant"):
                    st.error(msg["content"])
            else:
                # If there's a pptx file associated with this message, render the download button
                if msg.get("pptx_name"):
                    pptx_name = msg["pptx_name"]
                    pptx_bytes = st.session_state.slides_cache.get(pptx_name)
                    if pptx_bytes:
                        with st.chat_message("assistant"):
                            if msg["content"]:
                                st.markdown(msg["content"])
                            st.download_button(
                                label="⬇️ Download Presentation (.pptx)",
                                data=pptx_bytes,
                                file_name=f"{pptx_name}.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                key=f"dl_{pptx_name}" # Unique key for each button
                            )
                    else:
                        with st.chat_message("assistant"):
                            st.error(f"Presentation data lost for: {pptx_name}")
                elif msg.get("content"):
                    with st.chat_message("assistant"):
                        st.markdown(msg["content"])

    # Chat Input
    prompt = st.chat_input(placeholder="Write the topic or instructions here.",
        disabled=st.session_state.chat_disabled_slides,
        key='chat_input_slides',
        max_chars=LLM_MODEL_MAX_INPUT_LENGTH
    )

    if prompt:
        st.session_state.chat_disabled_slides = True
        st.session_state.last_prompt_text_slides = prompt
        st.session_state.messages_slides.append({
            "role": "user", 
            "content": f"Prompt: {prompt}"
        })
        st.rerun()
    
    # Handle the API Call
    if st.session_state.last_prompt_text_slides:
        prompt_text = st.session_state.last_prompt_text_slides
        
        with st.chat_message("assistant"):
            with st.spinner("Generating your slide deck with Vertex AI... This may take 15-30 seconds."):
                try:
                    # 1. Call the new /build-full endpoint
                    url = f"{API_URL_SLIDE}/build-full"
                    payload = {"prompt": prompt_text}
                    
                    # We add a 120 second timeout because Vertex AI can take a while to generate
                    response = requests.post(url, json=payload, timeout=120)
                    
                    if response.status_code == 200:
                        # 2. Get the raw bytes of the .pptx file
                        pptx_bytes = response.content
                        pptx_name = generate_file_name()
                        
                        # 3. Store in cache so the download button survives reruns
                        st.session_state.slides_cache[pptx_name] = pptx_bytes
                        
                        # 4. Save success to chat history
                        st.session_state.messages_slides.append({
                            "role": "assistant", 
                            "content": "Done! Here is your generated slide deck:", 
                            "ok": True, 
                            "pptx_name": pptx_name
                        })
                    else:
                        error_msg = f"Server Error {response.status_code}: {response.text}"
                        st.session_state.messages_slides.append({"role": "assistant", "content": error_msg, "ok": False})
                        
                except requests.exceptions.RequestException as e:
                    error_msg = f"Failed to connect to the server. Is server_build running? Error: {str(e)}"
                    st.session_state.messages_slides.append({"role": "assistant", "content": error_msg, "ok": False})

                # 5. Cleanup state and unlock chat
                st.session_state.chat_disabled_slides = False
                st.session_state.last_prompt_text_slides = None
                st.rerun()

if __name__ == "__main__":
    main()