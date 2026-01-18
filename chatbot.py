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

# Bro icon options
BRO_ICONS = {
    "😎 Cool Bro": "😎",
    "🤙 Chill Bro": "🤙",
    "💪 Gym Bro": "💪",
    "🎮 Gamer Bro": "🎮",
    "🧢 Cap Bro": "🧢",
    "🤘 Rock Bro": "🤘",
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model" not in st.session_state:
    st.session_state.model = None
if "bro_icon" not in st.session_state:
    st.session_state.bro_icon = "😎"
if "api_configured" not in st.session_state:
    st.session_state.api_configured = False

def initialize_gemini_model():
    """Initialize Gemini API model using secrets"""
    try:
        # Get API key from Streamlit secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)

        # Use gemini-1.5-flash directly
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )
        return model

    except KeyError:
        st.error("API key not found! Please configure GEMINI_API_KEY in secrets.")
        return None
    except Exception as e:
        st.error(f"Failed to initialize: {str(e)}")
        return None

# Auto-initialize model on startup
if not st.session_state.api_configured:
    model = initialize_gemini_model()
    if model:
        st.session_state.model = model
        st.session_state.api_configured = True

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

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 🖼️ Image Upload")
    uploaded_file = st.file_uploader(
        "Upload an image for Bro to check out",
        type=["png", "jpg", "jpeg", "gif", "webp"],
        help="Upload an image and Bro will tell you what he sees!"
    )

    if uploaded_file is not None and st.session_state.api_configured:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

        if st.button("🔍 Ask Bro to Check It", use_container_width=True):
            with st.spinner("Bro is checking it out..."):
                try:
                    # Use gemini-1.5-flash for image analysis
                    api_key = st.secrets["GEMINI_API_KEY"]
                    genai.configure(api_key=api_key)
                    vision_model = genai.GenerativeModel('gemini-1.5-flash')

                    # Create prompt with Bro persona
                    prompt = """You are a chill but real Bro. Check out this image and describe what you see
                    in the way a best friend would. Comment on it like a bro would - maybe hype them up,
                    give honest feedback, or share your thoughts. Be cool, casual, and supportive."""

                    response = vision_model.generate_content([prompt, image])

                    if response.text:
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
    1. Choose your Bro icon above
    2. Start chatting with Bro!
    3. Upload an image for Bro to check out
    4. Type "exit" to end the conversation
    """)

# Main Area
st.title("💬 Bro Chatbot")
st.markdown("Chat with your chill Bro!")

# If API is not configured
if not st.session_state.api_configured:
    st.error("Bro is not available right now. Please try again later.")
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
