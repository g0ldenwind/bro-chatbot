import streamlit as st
import warnings
import sys
from PIL import Image
import io

# Suppress FutureWarning (google.generativeai deprecation warnings)
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai

# Page configuration
st.set_page_config(
    page_title="Bro Chatbot",
    page_icon="😎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for cyan input border
st.markdown("""
<style>
    .stChatInput > div {
        border-color: cyan !important;
    }
    .stChatInput > div:focus-within {
        border-color: cyan !important;
        box-shadow: 0 0 0 1px cyan !important;
    }
    .stChatInput textarea:focus {
        border-color: cyan !important;
    }
</style>
""", unsafe_allow_html=True)

# System instruction (persona configuration)
SYSTEM_INSTRUCTION = """You are a chill but real Bro.
You call the user "bro", "dude", or "man" and always speak in a casual, friendly tone.
You keep it real and give honest advice, but always have your bro's back.
You're supportive, laid-back, and hype them up when needed.
Be cool, genuine, and act like a best friend who's always down to help."""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = None
if "model_name" not in st.session_state:
    st.session_state.model_name = ""
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "image_analysis" not in st.session_state:
    st.session_state.image_analysis = None
if "bro_icon" not in st.session_state:
    st.session_state.bro_icon = "😎"

# Bro icon options
BRO_ICONS = {
    "😎 Cool Bro": "😎",
    "🤙 Chill Bro": "🤙",
    "💪 Gym Bro": "💪",
    "🎮 Gamer Bro": "🎮",
    "🧢 Cap Bro": "🧢",
    "🤘 Rock Bro": "🤘",
}

def initialize_gemini_model(api_key):
    """Initialize Gemini API model"""
    try:
        genai.configure(api_key=api_key)

        # List available models
        try:
            available_models = genai.list_models()
            model_names_list = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]

            # Extract model IDs
            usable_models = []
            for m in model_names_list:
                if 'gemini' in m.lower() and 'flash' in m.lower():
                    model_id = m.replace('models/', '')
                    usable_models.append(model_id)

            if not usable_models:
                # If no flash models, look for any gemini models
                for m in model_names_list:
                    if 'gemini' in m.lower():
                        model_id = m.replace('models/', '')
                        usable_models.append(model_id)

            if not usable_models:
                # If still none found, use the first available model
                usable_models = [model_names_list[0].replace('models/', '')] if model_names_list else []

        except Exception as e:
            st.error(f"Failed to retrieve model list: {e}")
            # Fallback: try commonly used model names
            usable_models = ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-pro']

        # Try available models
        model = None
        model_name = None
        for model_name_candidate in usable_models:
            try:
                model = genai.GenerativeModel(
                    model_name_candidate,
                    system_instruction=SYSTEM_INSTRUCTION
                )
                # Connection test
                test_response = model.generate_content("Hello")
                model_name = model_name_candidate
                break
            except Exception as e:
                if model_name_candidate == usable_models[-1]:
                    # If all attempts failed
                    raise Exception(f"All model attempts failed. Last error: {str(e)}")
                continue

        if model is None:
            raise Exception("No available models found.")
        
        return model, model_name
        
    except Exception as e:
        raise Exception(f"Failed to configure API key: {str(e)}")

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")

    # Bro icon selector
    st.markdown("### 🎭 Choose Your Bro")
    selected_icon = st.selectbox(
        "Select Bro Icon",
        options=list(BRO_ICONS.keys()),
        index=list(BRO_ICONS.values()).index(st.session_state.bro_icon) if st.session_state.bro_icon in BRO_ICONS.values() else 0,
        label_visibility="collapsed"
    )
    st.session_state.bro_icon = BRO_ICONS[selected_icon]
    st.markdown(f"Current Bro: {st.session_state.bro_icon}")

    st.markdown("---")

    # API key input
    api_key_input = st.text_input(
        "Google Gemini API Key",
        type="password",
        value=st.session_state.api_key,
        help="Enter your API key from Google AI Studio"
    )

    if st.button("🔑 Set API Key", use_container_width=True):
        if api_key_input:
            with st.spinner("Verifying API key..."):
                try:
                    model, model_name = initialize_gemini_model(api_key_input)
                    st.session_state.api_key = api_key_input
                    st.session_state.model = model
                    st.session_state.model_name = model_name
                    st.session_state.api_configured = True
                    st.success(f"✓ Model '{model_name}' configured successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.info("Please verify your API key is correct.")
        else:
            st.warning("Please enter an API key.")

    # Display when API key is configured
    if st.session_state.api_configured:
        st.markdown("---")
        st.success("✓ API key is configured")
        if st.session_state.model_name:
            st.info(f"Using model: {st.session_state.model_name}")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.uploaded_image = None
            st.session_state.image_analysis = None
            st.rerun()

        st.markdown("---")
        st.markdown("### 🖼️ Image Upload")
        uploaded_file = st.file_uploader(
            "Upload an image for Bro to check out",
            type=["png", "jpg", "jpeg", "gif", "webp"],
            help="Upload an image and Bro will tell you what he sees!"
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)

            if st.button("🔍 Ask Bro to Check It", use_container_width=True):
                with st.spinner("Bro is checking it out..."):
                    try:
                        # Use gemini-1.5-flash for image analysis
                        vision_model = genai.GenerativeModel('gemini-1.5-flash')

                        # Convert image for API
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format=image.format or 'PNG')
                        img_byte_arr.seek(0)

                        # Create prompt with Mom persona
                        prompt = f"""You are a chill but real Bro. Check out this image and describe what you see
                        in the way a best friend would. Comment on it like a bro would - maybe hype them up,
                        give honest feedback, or share your thoughts. Be cool, casual, and supportive."""

                        response = vision_model.generate_content([prompt, image])

                        if response.text:
                            st.session_state.image_analysis = response.text
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"🖼️ *Bro checked out your image:*\n\n{response.text}"
                            })
                            st.success("Bro checked out the image!")
                            st.rerun()
                        else:
                            st.error("Couldn't check this image out, bro.")
                    except Exception as e:
                        st.error(f"Error analyzing image: {str(e)}")

    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Enter your API key in the sidebar
    2. Click "Set API Key" button
    3. Start chatting with Bro!
    4. Upload an image for Bro to check out
    5. Type "exit" to end the conversation
    """)

# Main Area
st.title("💬 Bro Chatbot")
st.markdown("Chat with your chill Bro!")

# If API key is not configured
if not st.session_state.api_configured:
    st.info("👈 Please set your API key in the sidebar.")
    st.markdown("""
    ### How to Get an API Key
    1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. Generate an API key
    3. Enter it in the sidebar
    """)
else:
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar=st.session_state.bro_icon):
                st.markdown(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Type your message..."):
        # Exit condition
        if prompt.lower() == 'exit':
            exit_msg = "Later, bro! Hit me up anytime, I got you!"
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": exit_msg})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant", avatar=st.session_state.bro_icon):
                st.markdown(exit_msg)
        else:
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get response from Gemini
            with st.chat_message("assistant", avatar=st.session_state.bro_icon):
                with st.spinner("Bro is thinking..."):
                    try:
                        response = st.session_state.model.generate_content(prompt)
                        if response.text:
                            st.markdown(response.text)
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                        else:
                            error_msg = "My bad bro, couldn't come up with a response..."
                            st.markdown(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    except Exception as e:
                        error_msg = f"Yo, something went wrong: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
