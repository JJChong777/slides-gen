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
    if "last_prompt_pdf_slides" not in st.session_state:
        st.session_state.last_prompt_pdf_slides = None

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
                st.session_state.chat_input_slides = selected_question
                # st.session_state.chat_disabled_slides = True
                # st.session_state.messages_slides.append({
                #     "role": "user", 
                #     "content": f"Prompt: {selected_question}"
                # })
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
                    pptx_cache_name = msg["pptx_cache_name"]
                    pptx_bytes = st.session_state.slides_cache.get(pptx_cache_name)
                    if pptx_bytes:
                        with st.chat_message("assistant"):
                            if msg["content"]:
                                st.markdown(msg["content"])
                            st.download_button(
                                label="⬇️ Download Presentation (.pptx)",
                                data=pptx_bytes,
                                file_name=f"{pptx_name}.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                key=f"dl_{pptx_cache_name}" # Unique key for each button
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
        max_chars=LLM_MODEL_MAX_INPUT_LENGTH,
        accept_file = True,
        file_type=["pdf"],
        max_upload_size=25
    )

    if prompt and prompt.text:
        st.session_state.chat_disabled_slides = True
        st.session_state.last_prompt_text_slides = prompt.text
        if prompt["files"]:
            st.session_state.last_prompt_pdf_slides = prompt["files"][0]
        st.session_state.messages_slides.append({
            "role": "user", 
            "content": f"Prompt: {prompt.text}, PDF: {prompt['files'][0].name if prompt['files'] else 'None'}"
        })
        st.rerun()
    
    # Handle the API Call
    if st.session_state.last_prompt_text_slides:
        prompt_text = st.session_state.last_prompt_text_slides
        
        with st.chat_message("assistant"):
            with st.spinner("Generating your slide deck with Vertex AI... This may take 15-30 seconds."):
                try:
                    # 1. Call the new /build_full endpoint (fixed underscore)
                    url = f"{API_URL_SLIDE}/build_full"
                    
                    # 2. Separate text data from file data
                    data_payload = {"prompt": prompt_text}
                    files_payload = None
                    
                    if st.session_state.last_prompt_pdf_slides:
                        pdf_file = st.session_state.last_prompt_pdf_slides
                        # The key "pdf_file" matches the multer upload.single("pdf_file") in Node
                        files_payload = {
                            "pdf_file": (pdf_file.name, pdf_file.getvalue(), 'application/pdf')
                        }
                    
                    # 3. Use data= and files= (NEVER json= when uploading files)
                    response = requests.post(url, data=data_payload, files=files_payload, timeout=120)
                    
                    if response.status_code == 200:
                        # 4. Get the raw bytes of the .pptx file
                        pptx_bytes = response.content
                        pptx_cache_name = generate_file_name()
                        
                        # (Optional) Try to get the real filename from the headers, fallback to cache name
                        content_disp = response.headers.get("Content-Disposition", "")
                        if "filename=" in content_disp:
                            # Extracts the filename from 'attachment; filename="title.pptx"'
                            pptx_name = content_disp.split('filename="')[1].strip('"')
                        else:
                            pptx_name = f"{pptx_cache_name}.pptx"

                        # 5. Store in cache so the download button survives reruns
                        st.session_state.slides_cache[pptx_cache_name] = pptx_bytes
                        
                        # 6. Save success to chat history
                        st.session_state.messages_slides.append({
                            "role": "assistant", 
                            "content": "Done! Here is your generated slide deck:", 
                            "ok": True, 
                            "pptx_cache_name": pptx_cache_name,
                            "pptx_name": pptx_name
                        })
                    else:
                        error_msg = f"Server Error {response.status_code}: {response.text}"
                        st.session_state.messages_slides.append({"role": "assistant", "content": error_msg, "ok": False})
                except Exception as e:
                    error_msg = f"Request failed: {str(e)}"
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