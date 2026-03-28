import streamlit as st
from modules import API_URL, generate_file_name, PPTX_TEMPLATE_FILES, LLM_MODEL_MAX_INPUT_LENGTH
import time
from io import BytesIO
import requests
    
def main():
    st.title("Create a slide deck with AI")
    st.info("This version is a deconstructed and simplified version of [Slide Deck AI](https://github.com/barun-saha/slide-deck-ai/tree/main).")
    ### template 
    with st.sidebar:
        # The PPT templates
        pptx_template = st.sidebar.radio(
            'Select a presentation template:',
           list(PPTX_TEMPLATE_FILES.keys()),
            captions=[PPTX_TEMPLATE_FILES[x]['caption'] for x in PPTX_TEMPLATE_FILES],
            horizontal=True
        )

        st.session_state.last_prompt_template_slides = pptx_template

    if "messages_slides" not in st.session_state:
        st.session_state.messages_slides = [{"role": "assistant", "content": "Hi, I'm the Slide Deck Chatbot! Type in a prompt to get started", "ok":True, "pptx_name": None}]
    if "slides_cache" not in st.session_state:
        st.session_state.slides_cache = {}
    if "chat_disabled_slides" not in st.session_state:
        st.session_state.chat_disabled_slides = False
    if "last_prompt_text_slides" not in st.session_state:
        st.session_state.last_prompt_text_slides = False
    if "last_prompt_template_slides" not in st.session_state:
        st.session_state.last_prompt_template_slides = False
    if "page_range_slider" not in st.session_state:
        st.session_state.page_range_slider = False

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
            if submitted:
                st.session_state.chat_input_edit = selected_question
    
    prompt = st.chat_input(placeholder="Write the topic or instructions here.",
        disabled=st.session_state.chat_disabled_slides,
        key='chat_input_slides',
        max_chars=LLM_MODEL_MAX_INPUT_LENGTH
        )

    for msg in st.session_state.messages_slides:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
                if not msg["ok"]:
                    with st.chat_message("assistant"):
                        st.error(msg["content"])
                else:
                    if msg["pptx_name"]:
                        pptx_name = msg["pptx_name"]
                        img_bytes = st.session_state.slides_cache.get(pptx_name)
                        if img_bytes:
                            with st.chat_message("assistant"):
                                st.write("WIP")
                        else:
                            st.error(f"Image with name: {pptx_name} not found in image cache")
                    if msg["content"]:
                        with st.chat_message("assistant"):
                            st.markdown(msg["content"])
        else:
            st.error("Message with invalid role") 

    if prompt:
        st.session_state.chat_disabled_slides = True
        st.session_state.last_prompt_text_slides = prompt
        # Add user message to session state
        st.session_state.messages_slides.append({
            "role": "user", 
            "content": f"Prompt: {prompt}"
        })
        st.rerun()
    
    if st.session_state.last_prompt_text_slides:
        
        with st.chat_message("assistant"):
            with st.spinner("Sending prompt and pptx template name to server..."):
                success = True
                prompt_response = "WIP"
                
                if success:
                    message = prompt_response
                    st.success(message)
                else:
                    error_msg = f"Failed to send prompt and pptx template name: {prompt_response}"
        
                    st.session_state.messages_slides.append({"role": "assistant", "content": error_msg, "ok": False})
                    st.session_state.chat_disabled_slides = False
                    st.session_state.last_prompt_text_slides = None
                    st.session_state.last_prompt_template_slides = None
                    st.rerun()
                    
            with st.spinner("Fetching powerpoint from server..."):
                success = True
                img_response = None
                if success: 
                    # Check if response is actually an image
                    content_type = img_response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        error_msg = f"Server returned non-image content: {content_type}"
                        if hasattr(img_response, 'text'):
                            error_msg += f" ,Response text: {img_response.text[:500]}"
                        st.session_state.messages_slides.append({"role": "assistant", "content": error_msg, "ok": False})
                        st.session_state.chat_disabled_slides = False
                        st.session_state.last_prompt_text_slides = None
                        st.session_state.last_prompt_template_slides = None
                        st.rerun()
                        
                    pptx_name = generate_file_name()
                    img_bytes = img_response.content
                    st.session_state.slides_cache[pptx_name] = img_bytes
                    st.session_state.messages_slides.append({"role": "assistant", "content": None, "ok": True, "pptx_name": pptx_name})
                    st.session_state.chat_disabled_slides = False
                    st.session_state.last_prompt_text_slides = None
                    st.session_state.last_prompt_template_slides = None
                    st.rerun()
                else:
                    error_msg = f"Failed to fetch edited image: {img_response}"
                    st.session_state.messages_slides.append({"role": "assistant", "content": error_msg, "ok": False})
                    st.session_state.chat_disabled_slides = False
                    st.session_state.last_prompt_text_slides = None
                    st.session_state.last_prompt_template_slides = None
                    st.rerun()

if __name__ == "__main__":
    main()
