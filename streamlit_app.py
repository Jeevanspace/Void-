    unsafe_allow_html=True,
)
st.write("")

with st.expander("📂 UPLOAD FILES / VISION", expanded=False):
    uploaded_file = st.file_uploader(
        "Upload an image or PDF",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        help="For PDFs, VOID extracts selectable text. Scanned PDFs may require OCR.",
        key="void_upload",
    )
    speak_responses = st.checkbox("Speak assistant responses", value=True)

# Render saved conversation.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("image_url"):
            st.image(message["image_url"], caption="Generated image")
        if message.get("content"):
            st.markdown(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format="audio/mp3")


# =============================================================================
# 7. INPUT AND PROCESSING
# =============================================================================
left, right = st.columns([1, 6], vertical_alignment="bottom")

with left:
    audio_data = mic_recorder(
        start_prompt="🎤 Speak",
        stop_prompt="🛑 Stop",
        just_once=True,
        use_container_width=True,
        key="void_mic",
    )

with right:
    text_input = st.chat_input("Command Void...")

final_input = text_input.strip() if text_input else None

# Process each unique recording once. Text input takes precedence if both exist.
if not final_input and audio_data and audio_data.get("bytes"):
    audio_hash = hashlib.sha256(audio_data["bytes"]).hexdigest()
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        final_input = audio_to_text(audio_data["bytes"])
        if final_input:
            st.info(f"Voice recognized: {final_input}")

# Only act after the user has supplied a message.
if final_input:
    st.session_state.messages.append({"role": "user", "content": final_input})

    file_context = None
    image_to_analyze = None

    if uploaded_file is not None:
        mime_type = uploaded_file.type or ""

        if mime_type.startswith("image/"):
            try:
                image_to_analyze = Image.open(uploaded_file).convert("RGB")
            except Exception as exc:
                st.error(f"Could not open this image: {exc}")

        elif mime_type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
            file_context = extract_pdf_text(uploaded_file)
            if file_context.startswith("PDF extraction failed:"):
                st.error(file_context)
                file_context = None

    with st.spinner("VOID is processing your command..."):
        if image_to_analyze is not None:
            answer = analyze_image(final_input, image_to_analyze)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
            if speak_responses:
                # Generate audio once, store bytes, then render it below.
                try:
                    tts_buffer = io.BytesIO()
                    gTTS(text=answer[:4500], lang="en", slow=False).write_to_fp(tts_buffer)
                    st.session_state.messages[-1]["audio_bytes"] = tts_buffer.getvalue()
                except Exception:
                    pass

        else:
            response_type, content = brain_engine(final_input, file_context)

            if response_type == "IMG":
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": "Image request created. If the image service is available, it will appear below.",
                        "image_url": content,
                    }
                )
            else:
                st.session_state.messages.append(
                    {"role": "assistant", "content": content}
                )
                if speak_responses and not content.startswith("Groq API error:"):
                    try:
                        tts_buffer = io.BytesIO()
                        gTTS(text=content[:4500], lang="en", slow=False).write_to_fp(tts_buffer)
                        st.session_state.messages[-1]["audio_bytes"] = tts_buffer.getvalue()
                    except Exception:
                        pass

    st.rerun()
