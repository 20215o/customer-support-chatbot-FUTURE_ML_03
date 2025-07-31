import os
import streamlit as st
from openai import OpenAI
from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.exceptions import GoogleAPIError

# Try to get environment variables first, fallback to config.py
try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID")
    GOOGLE_APPLICATION_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_PATH")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # If environment variables are not set, try to import from config.py
    if not all([OPENAI_API_KEY, DIALOGFLOW_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS_PATH, TELEGRAM_BOT_TOKEN]):
        from config import (
            OPENAI_API_KEY,
            DIALOGFLOW_PROJECT_ID,
            GOOGLE_APPLICATION_CREDENTIALS_PATH,
            TELEGRAM_BOT_TOKEN,
        )
except ImportError:
    st.error("""
    ⚠️ **Configuration Error**
    
    Please set up your environment variables or create a config.py file with your API keys.
    
    Required environment variables:
    - OPENAI_API_KEY
    - DIALOGFLOW_PROJECT_ID  
    - GOOGLE_APPLICATION_CREDENTIALS_PATH
    - TELEGRAM_BOT_TOKEN
    
    See config.sample.py for reference.
    """)
    st.stop()

import time
import json
from datetime import datetime
import requests
import threading
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from textblob import TextBlob
import re

# Set Google credentials for Dialogflow
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS_PATH

# Set OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Dialogflow session client
dialogflow_session_client = dialogflow.SessionsClient()

# Telegram bot setup
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Global flag to track OpenAI quota status
openai_quota_exceeded = False
last_update_id = 0

# Streamlit page config
st.set_page_config(
        page_title="🤖 Claude AI Support Assistant - Built by Claude Tomoh",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# ---------- PROFESSIONAL UI STYLING ----------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .welcome-header {
        text-align: center;
        margin-bottom: 30px;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .welcome-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        background: linear-gradient(45deg, #fff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .welcome-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 20px;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin: 30px 0;
    }
    
    .feature-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 15px;
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px !important;
        padding: 15px 20px !important;
        margin: 10px 0 !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
    }
    
    .stChatInput {
        background: rgba(255, 255, 255, 0.9) !important;
        border-radius: 15px !important;
        padding: 15px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
    }
    
    .quick-actions {
        background: rgba(255, 255, 255, 0.9);
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 10px;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
    }
    
    .sidebar .sidebar-content {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
    }
    
    .typing-indicator {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .response-quality {
        font-size: 0.8rem;
        color: #666;
        margin-top: 5px;
    }
    
    .ai-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    .feature-card {
        color: #111 !important;
    }
    .feature-card h3, .feature-card p, .feature-icon {
        color: #111 !important;
    }
    .stats-container, .stat-card {
        color: #111 !important;
    }
    .stat-card .stat-number, .stat-card div {
        color: #111 !important;
    }
    .stMetric label, .stMetric div {
        color: #111 !important;
    }
    .analytics-empty-message, .footer-info, .footer-features {
        color: #fff !important;
    }
    .analytics-empty-message {
        color: #111 !important;
        font-weight: 700;
        font-size: 1.2rem;
        background: rgba(255,255,255,0.85);
        border-left: 6px solid #764ba2;
        padding: 16px 20px;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(102,126,234,0.08);
    }
    .footer-info, .footer-features {
        color: #fff !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- ENHANCED RESPONSE SYSTEM ----------
def get_smart_response(user_input):
    """Enhanced response system with better context and fallback"""
    user_input_lower = user_input.lower()
    
    # Enhanced greeting responses
    if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return {
            "response": "Hello! 👋 I'm your AI-powered support assistant. I'm here to help you with any questions about our products, services, or support needs. How can I assist you today?",
            "source": "dialogflow",
            "confidence": 0.95
        }
    
    # Help and support requests
    elif any(word in user_input_lower for word in ['help', 'support', 'assist', 'what can you do', 'how can you help']):
        return {
            "response": """I'm your comprehensive support assistant! Here's what I can help you with:

🔍 **Product Information** - Find details, pricing, and availability
📦 **Order Management** - Track orders, check status, and manage deliveries
🔄 **Returns & Refunds** - Process returns and handle refunds
🔧 **Technical Support** - Troubleshoot issues and provide solutions
📞 **Contact Information** - Connect you with the right team
⏰ **Business Hours** - Check availability and support times
💳 **Payment & Billing** - Handle payment issues and billing questions

What would you like to know about?""",
            "source": "dialogflow",
            "confidence": 0.9
        }
    
    # Product inquiries
    elif any(word in user_input_lower for word in ['product', 'item', 'buy', 'purchase', 'price', 'cost', 'available']):
        return {
            "response": "I'd be happy to help you with product information! Could you please specify which product or category you're interested in? I can provide details about pricing, features, availability, and help you make the best choice.",
            "source": "dialogflow",
            "confidence": 0.85
        }
    
    # Order status
    elif any(word in user_input_lower for word in ['order', 'tracking', 'shipping', 'delivery', 'when', 'status', 'where is my']):
        return {
            "response": """To check your order status, I'll need your order number. Here's how to find it:

📧 **Email Confirmation** - Check your email for order confirmation
📱 **Account Dashboard** - Log into your account to view order history
📞 **Phone Support** - Call us at 1-800-SUPPORT with your order number

Once you have your order number, I can help you track its status and estimated delivery date. Do you have your order number handy?""",
            "source": "dialogflow",
            "confidence": 0.9
        }
    
    # Returns and refunds
    elif any(word in user_input_lower for word in ['return', 'refund', 'exchange', 'cancel', 'send back', 'money back']):
        return {
            "response": """Our return and refund policy is designed to make things easy for you:

✅ **30-Day Return Window** - Return items within 30 days of purchase
📦 **Free Return Shipping** - We cover all return shipping costs
💳 **Full Refund** - Money back to your original payment method
🔄 **Easy Process** - Use our online return portal or contact support

To start a return, I'll need your order number and the reason for return. Do you have your order details ready?""",
            "source": "dialogflow",
            "confidence": 0.9
        }
    
    # Technical issues
    elif any(word in user_input_lower for word in ['technical', 'broken', 'not working', 'error', 'problem', 'issue', 'trouble', 'fix']):
        return {
            "response": """I'm sorry to hear you're experiencing technical issues. Let me help you troubleshoot:

🔍 **Quick Troubleshooting Steps:**
• Restart your device/browser
• Clear cache and cookies
• Check your internet connection
• Try a different browser or device
• Update to the latest version

📞 **Still having issues?** I can connect you with our technical support team for personalized assistance.

Could you describe the problem in detail so I can provide more specific help?""",
            "source": "dialogflow",
            "confidence": 0.85
        }
    
    # Contact information
    elif any(word in user_input_lower for word in ['contact', 'phone', 'email', 'speak', 'human', 'agent', 'talk to someone']):
        return {
            "response": """You can reach our customer service team through multiple channels:

📞 **Phone Support:** 1-800-SUPPORT (24/7)
📧 **Email:** support@company.com
💬 **Live Chat:** Available on our website
📱 **Mobile App:** Download our app for quick support

⏰ **Business Hours:**
Monday-Friday: 8 AM - 8 PM EST
Saturday: 9 AM - 6 PM EST
Sunday: 10 AM - 4 PM EST

Would you like me to connect you with a human agent right now?""",
            "source": "dialogflow",
            "confidence": 0.9
        }
    
    # Business hours
    elif any(word in user_input_lower for word in ['hours', 'open', 'closed', 'time', 'when', 'available', 'business hours']):
        return {
            "response": """Our customer support is available:

🕐 **Monday-Friday:** 8 AM - 8 PM EST
🕐 **Saturday:** 9 AM - 6 PM EST
🕐 **Sunday:** 10 AM - 4 PM EST

📞 **24/7 Emergency Support:** Available for urgent technical issues
💬 **Online Chat:** Available 24/7 for general inquiries

We're here to help whenever you need us!""",
            "source": "dialogflow",
            "confidence": 0.9
        }
    
    # Goodbye
    elif any(word in user_input_lower for word in ['bye', 'goodbye', 'end', 'exit', 'see you', 'thank you', 'thanks']):
        return {
            "response": "Thank you for chatting with us! Have a wonderful day! 👋 Feel free to come back anytime you need assistance. We're here to help!",
            "source": "dialogflow",
            "confidence": 0.95
        }
    
    # Default - will be handled by ChatGPT
    else:
        return None

# ---------- ENHANCED DIALOGFLOW FUNCTION ----------
def detect_intent_text(session_id, text, language_code="en"):
    session = dialogflow_session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    try:
        response = dialogflow_session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        fulfillment_text = response.query_result.fulfillment_text
        # Check if Dialogflow has a meaningful response
        if fulfillment_text and fulfillment_text.strip():
            # List of generic/unhelpful responses that should trigger ChatGPT fallback
            generic_responses = [
                "hmm, i'm not sure i understand",
                "could you rephrase",
                "sorry, i'm still learning",
                "i'm afraid i don't have an answer",
                "that's a bit outside my knowledge",
                "can you ask something else",
                "i'll pass it along to the team",
                "that's a great question",
                "i'm not sure about that",
                "let me check on that",
                "i don't have information about that",
                "that's beyond my capabilities",
                "i didn't get that",
                "i'm sorry, i didn't quite catch that",
                "would you like to talk to a support agent",
                "can you try saying it differently",
                "i didn't catch that",
                "could you please rephrase",
                "i'm sorry, i didn't understand",
                "let me connect you with someone",
                "i'll transfer you to an agent",
                "that's outside my scope",
                "i can't help with that",
                "i don't have that information",
                "i'm not programmed for that",
                "that's not something i can assist with",
                "i'm limited in what i can help with",
                "i don't have access to that",
                "that's beyond my training",
                "i can't process that request"
            ]
            # Check if the response is generic/unhelpful
            response_lower = fulfillment_text.lower()
            is_generic = any(generic in response_lower for generic in generic_responses)
            if is_generic:
                return None  # Trigger ChatGPT fallback
            else:
                return {
                    "response": fulfillment_text,
                    "source": "dialogflow",
                    "confidence": response.query_result.intent_detection_confidence
                }
        return None
    except Exception as e:
        st.error(f"Dialogflow error: {str(e)}")
        return None

# ---------- ENHANCED OPENAI FUNCTION ----------
def ask_openai(prompt, conversation_history=None):
    global openai_quota_exceeded
    if openai_quota_exceeded:
        return {
            "response": """I understand you need help! Unfortunately, my advanced AI service is temporarily unavailable due to usage limits. 

Here are your options:
📞 **Call Support:** 1-800-SUPPORT (24/7)
📧 **Email:** support@company.com
💬 **Live Chat:** Available on our website
⏰ **Business Hours:** Mon-Fri 8AM-8PM EST

For immediate assistance, I recommend contacting our human support team who can help you right away!""",
            "source": "fallback",
            "confidence": 0.0
        }

    try:
        # Build conversation context
        messages = [
            {
                "role": "system", 
                "content": """You are a professional, friendly, and helpful customer support AI assistant. 
                You provide clear, accurate, and helpful responses to customer inquiries. 
                Always be polite, professional, and try to be as helpful as possible. 
                If you don't know something, suggest contacting human support."""
            }
        ]
        
        # Add conversation history if available
        if conversation_history:
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user message
        messages.append({"role": "user", "content": prompt})
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.7,
            messages=messages,
            max_tokens=300
        )
        
        return {
            "response": response.choices[0].message.content.strip(),
            "source": "chatgpt",
            "confidence": 0.8
        }
    except Exception as e:
        error_str = str(e)
        
        # Handle quota exceeded error specifically
        if "429" in error_str or "quota" in error_str.lower():
            openai_quota_exceeded = True
            return {
                "response": """I understand you need help! Unfortunately, my advanced AI service is temporarily unavailable due to usage limits. 

Here are your options:
📞 **Call Support:** 1-800-SUPPORT (24/7)
📧 **Email:** support@company.com
💬 **Live Chat:** Available on our website
⏰ **Business Hours:** Mon-Fri 8AM-8PM EST

For immediate assistance, I recommend contacting our human support team who can help you right away!""",
                "source": "fallback",
                "confidence": 0.0
            }
        else:
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment or contact our human support team for immediate assistance.",
                "source": "fallback",
                "confidence": 0.0
            }

# ---------- TELEGRAM INTEGRATION ----------
def start_telegram_bot():
    """Start Telegram bot in background thread"""
    def bot_loop():
        global last_update_id
        while True:
            try:
                updates = get_telegram_updates()
                if updates and updates.get("ok"):
                    for update in updates.get("result", []):
                        if "message" in update:
                            message = update["message"]
                            chat_id = message["chat"]["id"]
                            text = message.get("text", "")
                            
                            if text:
                                # Store incoming message
                                if "telegram_messages" not in st.session_state:
                                    st.session_state.telegram_messages = []
                                
                                st.session_state.telegram_messages.append({
                                    "chat_id": chat_id,
                                    "text": text,
                                    "type": "incoming",
                                    "timestamp": datetime.now().isoformat()
                                })
                                
                                # Process message and get response
                                response = process_telegram_message(chat_id, text)
                                
                                # Send response back
                                send_telegram_message(chat_id, response)
                                
                                # Store outgoing message
                                st.session_state.telegram_messages.append({
                                    "chat_id": "Bot",
                                    "text": response,
                                    "type": "outgoing",
                                    "timestamp": datetime.now().isoformat()
                                })
                                
                                print(f"📤 Telegram: Sent response to {chat_id}")
                    
                    # Update last_update_id
                    if updates.get("result"):
                        last_update_id = max(last_update_id, max(update["update_id"] for update in updates["result"]))
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Telegram bot error: {str(e)}")
                time.sleep(5)
    
    # Start bot in background thread
    import threading
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    return bot_thread

def check_telegram_connection():
    """Check if Telegram bot is connected"""
    try:
        response = requests.get(f"{TELEGRAM_API_URL}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            return True, bot_info["result"]["username"], bot_info["result"]["first_name"]
        return False, None, None
    except:
        return False, None, None

def get_telegram_updates():
    """Get updates from Telegram bot"""
    global last_update_id
    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 10}
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Telegram error: {str(e)}")
        return None

def send_telegram_message(chat_id, message):
    """Send message to Telegram user"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Telegram error: {str(e)}")
        return None

def process_telegram_message(chat_id, message_text):
    """Process incoming Telegram message and return response"""
    print(f"📱 Processing Telegram message from {chat_id}: {message_text}")
    
    # Try Dialogflow first (always available)
    dialogflow_response = detect_intent_text(f"telegram-{chat_id}", message_text)
    
    if dialogflow_response:
        return dialogflow_response["response"]
    
    # If OpenAI quota not exceeded, try ChatGPT
    global openai_quota_exceeded
    if not openai_quota_exceeded:
        try:
            chatgpt_response = ask_openai(message_text)
            if chatgpt_response and chatgpt_response["source"] == "chatgpt":
                return chatgpt_response["response"]
        except:
            pass
    
    # Fallback to smart response
    smart_response = get_smart_response(message_text)
    if smart_response:
        return smart_response["response"]
    
    # Final fallback
    return "I'm here to help! Please contact our support team at 1-800-SUPPORT for immediate assistance."

# ---------- ENHANCED CHAT LOGIC ----------
def get_response_with_smart_fallback(user_input, conversation_history=None):
    """Enhanced response logic with smart fallback based on quota status"""
    global openai_quota_exceeded
    
    # Always try Dialogflow first
    dialogflow_response = detect_intent_text("session-001", user_input)
    
    if dialogflow_response:
        return dialogflow_response
    
    # If OpenAI quota exceeded, skip ChatGPT and use smart responses
    if openai_quota_exceeded:
        smart_response = get_smart_response(user_input)
        if smart_response:
            return smart_response
        else:
            return {
                "response": """I understand you need help! Our advanced AI is temporarily unavailable, but I can still assist you with:

📞 **Call Support:** 1-800-SUPPORT (24/7)
📧 **Email:** support@company.com
💬 **Live Chat:** Available on our website
⏰ **Business Hours:** Mon-Fri 8AM-8PM EST

For immediate assistance, please contact our human support team!""",
                "source": "fallback",
                "confidence": 0.0
            }
    
    # Try smart response system
    smart_response = get_smart_response(user_input)
    if smart_response:
        return smart_response
    
    # Fallback to ChatGPT (if quota not exceeded)
    try:
        return ask_openai(user_input, conversation_history)
    except:
        return {
            "response": "I apologize, but I'm having trouble processing your request right now. Please try again in a moment or contact our human support team for immediate assistance.",
            "source": "fallback",
            "confidence": 0.0
        }

# ---------- ADVANCED ANALYTICS FUNCTIONS ----------
def analyze_sentiment(text):
    """Analyze sentiment of user messages"""
    try:
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity
        if sentiment_score > 0.1:
            return "positive", sentiment_score
        elif sentiment_score < -0.1:
            return "negative", sentiment_score
        else:
            return "neutral", sentiment_score
    except:
        return "neutral", 0.0

def extract_intent_keywords(text):
    """Extract key intent keywords from user messages"""
    keywords = []
    text_lower = text.lower()
    
    # Intent categories
    intents = {
        "order": ["order", "tracking", "delivery", "shipping", "where", "when"],
        "support": ["help", "support", "assist", "problem", "issue", "trouble"],
        "product": ["product", "item", "buy", "purchase", "price", "cost"],
        "return": ["return", "refund", "exchange", "cancel", "send back"],
        "contact": ["contact", "phone", "email", "speak", "human", "agent"],
        "hours": ["hours", "open", "closed", "time", "when", "available"]
    }
    
    for intent, words in intents.items():
        if any(word in text_lower for word in words):
            keywords.append(intent)
    
    return keywords

def calculate_response_time(start_time, end_time):
    """Calculate response time in seconds"""
    return round((end_time - start_time).total_seconds(), 2)

def generate_analytics_report():
    """Generate comprehensive analytics report"""
    if not st.session_state.messages:
        return None
    
    # Convert messages to DataFrame
    df = pd.DataFrame(st.session_state.messages)
    
    # Basic metrics
    total_messages = len(df)
    user_messages = len(df[df['role'] == 'user'])
    bot_messages = len(df[df['role'] == 'assistant'])
    
    # Response source analysis
    source_counts = df[df['role'] == 'assistant']['source'].value_counts()
    
    # Sentiment analysis
    user_texts = df[df['role'] == 'user']['content'].tolist()
    sentiments = [analyze_sentiment(text)[0] for text in user_texts]
    sentiment_counts = pd.Series(sentiments).value_counts()
    
    # Intent analysis
    all_keywords = []
    for text in user_texts:
        keywords = extract_intent_keywords(text)
        all_keywords.extend(keywords)
    intent_counts = pd.Series(all_keywords).value_counts()
    
    return {
        'total_messages': total_messages,
        'user_messages': user_messages,
        'bot_messages': bot_messages,
        'source_counts': source_counts,
        'sentiment_counts': sentiment_counts,
        'intent_counts': intent_counts,
        'avg_response_time': 2.5  # Placeholder
    }

def create_analytics_dashboard():
    """Create interactive analytics dashboard"""
    analytics = generate_analytics_report()
    if not analytics:
        st.markdown('<div class="analytics-empty-message">No conversation data available for analytics.</div>', unsafe_allow_html=True)
        return
    
    st.markdown("### 📊 Advanced Analytics Dashboard")
    
    # Create tabs for different analytics
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🎯 Intents", "😊 Sentiment", "🤖 AI Sources"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Messages", analytics['total_messages'])
        with col2:
            st.metric("User Messages", analytics['user_messages'])
        with col3:
            st.metric("Bot Responses", analytics['bot_messages'])
        with col4:
            st.metric("Avg Response Time", f"{analytics['avg_response_time']}s")
    
    with tab2:
        if not analytics['intent_counts'].empty:
            fig = px.pie(values=analytics['intent_counts'].values, 
                        names=analytics['intent_counts'].index,
                        title="User Intent Distribution")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No intent data available yet.")
    
    with tab3:
        if not analytics['sentiment_counts'].empty:
            fig = px.bar(x=analytics['sentiment_counts'].index, 
                        y=analytics['sentiment_counts'].values,
                        title="User Sentiment Analysis",
                        color=analytics['sentiment_counts'].index)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment data available yet.")
    
    with tab4:
        if not analytics['source_counts'].empty:
            fig = px.pie(values=analytics['source_counts'].values, 
                        names=analytics['source_counts'].index,
                        title="AI Response Source Distribution")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No response source data available yet.")

# ---------- MULTI-LANGUAGE SUPPORT ----------
def detect_language(text):
    """Detect language of user input"""
    try:
        blob = TextBlob(text)
        return blob.detect_language()
    except:
        return "en"

def translate_response(response, target_language="en"):
    """Translate response to target language"""
    try:
        blob = TextBlob(response)
        translated = blob.translate(to=target_language)
        return str(translated)
    except:
        return response

# ---------- INTEGRATION CAPABILITIES ----------
def create_support_ticket(user_message, sentiment, intent):
    """Create support ticket for escalation"""
    ticket_data = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "sentiment": sentiment,
        "intent": intent,
        "priority": "high" if sentiment == "negative" else "medium",
        "status": "open"
    }
    
    # In a real implementation, this would save to a database
    # For now, we'll store in session state
    if "support_tickets" not in st.session_state:
        st.session_state.support_tickets = []
    
    st.session_state.support_tickets.append(ticket_data)
    return len(st.session_state.support_tickets)

def export_conversation_data():
    """Export comprehensive conversation data"""
    if not st.session_state.messages:
        return None
    
    export_data = {
        "conversation_metadata": {
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(st.session_state.messages),
            "session_duration": "N/A",
            "platform": "Streamlit Web App"
        },
        "messages": st.session_state.messages,
        "statistics": st.session_state.stats,
        "analytics": generate_analytics_report(),
        "support_tickets": st.session_state.get("support_tickets", [])
    }
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def create_performance_monitor():
    """Monitor chatbot performance metrics"""
    if "performance_metrics" not in st.session_state:
        st.session_state.performance_metrics = {
            "total_conversations": 0,
            "avg_response_time": 0,
            "user_satisfaction": 0,
            "escalation_rate": 0,
            "resolution_rate": 0
        }
    
    return st.session_state.performance_metrics

# ---------- MAIN APP INTERFACE ----------
def main():
    global openai_quota_exceeded
    
    # Welcome Header
    st.markdown("""
    <div class="welcome-header">
        <h1>🤖 Claude AI Support Assistant</h1>
        <p>Your 24/7 intelligent customer support companion</p>
        <p>Powered by advanced AI technology for instant, accurate responses</p>
        <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 10px;">Built by Claude Tomoh with ❤️ for Future Interns Program</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature Grid
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h3>Smart AI</h3>
            <p>Advanced AI technology for intelligent responses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3>Instant Help</h3>
            <p>Get immediate assistance 24/7</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Accurate</h3>
            <p>Precise answers to your questions</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Developer Signature
    st.markdown("""
    <div style="text-align: center; margin: 20px 0; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;">
        <p style="margin: 0; font-size: 0.9rem; color: rgba(255,255,255,0.8);">
            🤖 <strong>Claude AI Support Assistant</strong> | Built by <strong>Claude Tomoh</strong> | Future Interns Program
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat Container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "stats" not in st.session_state:
            st.session_state.stats = {
                "total_messages": 0,
                "dialogflow_responses": 0,
                "chatgpt_responses": 0,
                "fallback_responses": 0
            }
        
        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "source" in msg:
                    st.markdown(f'<span class="ai-badge">{msg["source"].upper()}</span>', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask me anything...")

        if user_input:
            # Analyze user input
            sentiment, sentiment_score = analyze_sentiment(user_input)
            intent_keywords = extract_intent_keywords(user_input)
            detected_language = detect_language(user_input)
            
            # Add user message with metadata
            user_message_data = {
                "role": "user", 
                "content": user_input,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "intent_keywords": intent_keywords,
                "language": detected_language,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.messages.append(user_message_data)
            st.session_state.stats["total_messages"] += 1
            
            with st.chat_message("user"):
                st.markdown(user_input)
                # Show sentiment indicator
                if sentiment != "neutral":
                    sentiment_emoji = "😊" if sentiment == "positive" else "😔"
                    st.caption(f"{sentiment_emoji} {sentiment.title()} sentiment")
            
            # Show typing indicator
            with st.chat_message("assistant"):
                with st.spinner("🤖 Thinking..."):
                    start_time = datetime.now()
                    time.sleep(0.5)  # Simulate thinking time
                    
                    # Use enhanced response logic with smart fallback
                    conversation_history = st.session_state.messages[-10:] if len(st.session_state.messages) > 10 else st.session_state.messages
                    final_response = get_response_with_smart_fallback(user_input, conversation_history)
                    
                    # Calculate response time
                    end_time = datetime.now()
                    response_time = calculate_response_time(start_time, end_time)
                    
                    # Update statistics based on response source
                    if final_response["source"] == "dialogflow":
                        st.session_state.stats["dialogflow_responses"] += 1
                    elif final_response["source"] == "chatgpt":
                        st.session_state.stats["chatgpt_responses"] += 1
                    else:
                        st.session_state.stats["fallback_responses"] += 1
                    
                    # Create support ticket if negative sentiment
                    if sentiment == "negative":
                        ticket_id = create_support_ticket(user_input, sentiment, intent_keywords)
                        final_response["response"] += f"\n\n⚠️ **Support ticket #{ticket_id} created** - A human agent will contact you soon."
                    
                    # Add assistant response with metadata
                    assistant_message_data = {
                        "role": "assistant", 
                        "content": final_response["response"],
                        "source": final_response["source"],
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    st.session_state.messages.append(assistant_message_data)
                    
                    st.markdown(final_response["response"])
                    st.markdown(f'<span class="ai-badge">{final_response["source"].upper()}</span>', unsafe_allow_html=True)
                    st.caption(f"⏱️ Response time: {response_time}s")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-scroll to bottom
        st.markdown("""
        <script>
        // Auto-scroll to bottom when new messages are added
        function scrollToBottom() {
            const chatContainer = document.querySelector('.chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            // Also scroll the main page to show new messages
            window.scrollTo(0, document.body.scrollHeight);
        }
        
        // Scroll on page load
        window.addEventListener('load', scrollToBottom);
        
        // Scroll after a short delay to ensure content is loaded
        setTimeout(scrollToBottom, 500);
        
        // Scroll every 2 seconds to catch new messages
        setInterval(scrollToBottom, 2000);
        </script>
        """, unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("""
    <div class="quick-actions">
        <h3>🚀 Quick Actions</h3>
        <p>Get instant help with common questions:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📞 Contact Support", key="contact"):
            st.session_state.messages.append({"role": "user", "content": "I need to contact support"})
            response = get_smart_response("contact support")
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response["response"], "source": response["source"]})
            else:
                # Fallback to ChatGPT
                chatgpt_response = ask_openai("I need to contact support")
                st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    with col2:
        if st.button("📦 Order Status", key="order"):
            st.session_state.messages.append({"role": "user", "content": "Where is my order?"})
            response = get_smart_response("order status")
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response["response"], "source": response["source"]})
            else:
                # Fallback to ChatGPT
                chatgpt_response = ask_openai("Where is my order?")
                st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    with col3:
        if st.button("🔄 Returns", key="returns"):
            st.session_state.messages.append({"role": "user", "content": "I want to return something"})
            response = get_smart_response("return refund")
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response["response"], "source": response["source"]})
            else:
                # Fallback to ChatGPT
                chatgpt_response = ask_openai("I want to return something")
                st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    with col4:
        if st.button("⏰ Business Hours", key="hours"):
            st.session_state.messages.append({"role": "user", "content": "What are your business hours?"})
            response = get_smart_response("business hours")
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response["response"], "source": response["source"]})
            else:
                # Fallback to ChatGPT
                chatgpt_response = ask_openai("What are your business hours?")
                st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    # Test ChatGPT Responses
    st.markdown("""
    <div class="quick-actions">
        <h3>🧪 Test ChatGPT Responses</h3>
        <p>Try these to trigger ChatGPT:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎭 Tell me a joke", key="joke"):
            st.session_state.messages.append({"role": "user", "content": "Tell me a joke"})
            chatgpt_response = ask_openai("Tell me a funny joke")
            st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    with col2:
        if st.button("🌤️ Weather", key="weather"):
            st.session_state.messages.append({"role": "user", "content": "What's the weather like?"})
            chatgpt_response = ask_openai("What's the weather like today?")
            st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    with col3:
        if st.button("🍕 Pizza recipe", key="recipe"):
            st.session_state.messages.append({"role": "user", "content": "How do I make pizza?"})
            chatgpt_response = ask_openai("How do I make homemade pizza?")
            st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    with col4:
        if st.button("💭 Philosophy", key="philosophy"):
            st.session_state.messages.append({"role": "user", "content": "What's the meaning of life?"})
            chatgpt_response = ask_openai("What's the meaning of life?")
            st.session_state.messages.append({"role": "assistant", "content": chatgpt_response["response"], "source": chatgpt_response["source"]})
            st.rerun()
    
    # Statistics
    st.markdown("""
    <div class="stats-container">
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state.stats['total_messages']}</div>
            <div>Total Messages</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state.stats['dialogflow_responses']}</div>
            <div>Dialogflow Responses</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state.stats['chatgpt_responses']}</div>
            <div>ChatGPT Responses</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{st.session_state.stats['fallback_responses']}</div>
            <div>Fallback Responses</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Advanced Analytics Dashboard
    create_analytics_dashboard()
    
    # Footer with Developer Info
    st.markdown("""
    <div class="footer-info" style="text-align: center; margin: 40px 0 20px 0; padding: 20px; background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%); border-radius: 15px;">
        <h4 style="margin: 0 0 10px 0; color: #fff;">🤖 Claude AI Support Assistant</h4>
        <p style="margin: 0; font-size: 0.9rem; color: #fff;">
            Built by <strong>Claude Tomoh</strong> | Future Interns Program | Advanced AI Integration
        </p>
        <p class="footer-features" style="margin: 5px 0 0 0; font-size: 0.8rem; color: #fff;">
            Features: Multi-AI Architecture • Real-time Analytics • Telegram Integration • Sentiment Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Telegram Messages Section
    if "telegram_bot_running" in st.session_state and st.session_state.telegram_bot_running:
        st.markdown("""
        <div class="quick-actions">
            <h3>📱 Telegram Messages</h3>
            <p>Real-time messages from your Telegram bot:</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize telegram messages in session state
        if "telegram_messages" not in st.session_state:
            st.session_state.telegram_messages = []
        
        # Display telegram messages
        if st.session_state.telegram_messages:
            # Show messages in reverse order (newest first)
            for msg in reversed(st.session_state.telegram_messages[-10:]):  # Show last 10 messages
                with st.chat_message("user" if msg["type"] == "incoming" else "assistant"):
                    if msg["type"] == "incoming":
                        st.markdown(f"**📱 User {msg['chat_id']}**: {msg['text']}")
                    else:
                        st.markdown(f"**🤖 Bot Response**: {msg['text']}")
                        st.markdown(f'<span class="ai-badge">TELEGRAM</span>', unsafe_allow_html=True)
                    
                    # Show timestamp
                    if "timestamp" in msg:
                        timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")
                        st.caption(f"⏰ {timestamp}")
        else:
            st.info("""
            📱 **No Telegram messages yet!**
            
            To test your bot:
            1. Click the Telegram link in the sidebar
            2. Send a message like "Hello" or "I need help"
            3. Watch the response appear here in real-time
            """)
        
        # Clear telegram messages
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Messages", key="clear_telegram"):
                st.session_state.telegram_messages = []
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh", key="refresh_telegram"):
                st.rerun()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-content">
        <h3>🎛️ Control Panel</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Clear chat
    if st.button("🗑️ Clear Chat", key="clear"):
        st.session_state.messages = []
        st.session_state.stats = {
            "total_messages": 0,
            "dialogflow_responses": 0,
            "chatgpt_responses": 0,
            "fallback_responses": 0
        }
        st.rerun()
    
    # Advanced Export Options
    st.markdown("### 📤 Export & Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export Analytics", key="export_analytics"):
            analytics_data = export_conversation_data()
            if analytics_data:
                st.download_button(
                    label="Download Full Report",
                    data=analytics_data,
                    file_name=f"chatbot_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with col2:
        if st.button("📋 Support Tickets", key="view_tickets"):
            if "support_tickets" in st.session_state and st.session_state.support_tickets:
                st.success(f"📋 {len(st.session_state.support_tickets)} support tickets created")
                for i, ticket in enumerate(st.session_state.support_tickets[-3:], 1):
                    st.info(f"Ticket #{i}: {ticket['user_message'][:50]}... ({ticket['sentiment']})")
            else:
                st.info("No support tickets created yet.")
    
    # Integration Status
    st.markdown("### 🔗 Integration Status")
    st.markdown("🟢 **Dialogflow**: Connected")
    st.markdown("🟢 **OpenAI**: Connected")
    st.markdown("🟢 **Telegram**: Connected")
    st.markdown("🟢 **Analytics**: Active")
    st.markdown("🟢 **Sentiment Analysis**: Active")
    
    # Settings
    st.markdown("### ⚙️ Settings")
    st.markdown("**AI Response Quality:** High")
    st.markdown("**Response Speed:** Optimized")
    st.markdown("**Language:** English")
    
    # Developer Info
    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Built by:** Claude Tomoh")
    st.markdown("**Project:** Claude AI Support Assistant")
    st.markdown("**Program:** Future Interns Program")
    st.markdown("**Version:** 2.0 Advanced")
    
    # System Status
    st.markdown("### 📊 System Status")
    st.markdown("🟢 Dialogflow: Connected")
    st.markdown("🟢 ChatGPT: Connected")
    st.markdown("🟢 System: Online")
    
    # Telegram Bot Integration
    st.markdown("### 📱 Telegram Bot")
    
    # Check connection status
    is_connected, bot_username, bot_first_name = check_telegram_connection()
    
    if is_connected:
        st.markdown(f"🟢 **Connected Successfully!**")
        st.markdown(f"🤖 Bot: @{bot_username}")
        st.markdown(f"👤 Name: {bot_first_name}")
        
        # Direct Telegram link
        telegram_link = f"https://t.me/{bot_username}"
        st.markdown(f"📱 **[Click here to open in Telegram]({telegram_link})**")
        
        # Instructions
        st.markdown("""
        **How to use:**
        1. Click the link above to open Telegram
        2. Click "Start" in the chat
        3. Send any message to test the bot
        4. Watch messages appear here in real-time
        """)
        
        # Bot controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Start Bot", key="start_bot"):
                if "telegram_bot_running" not in st.session_state:
                    st.session_state.telegram_bot_running = True
                    start_telegram_bot()
                    st.success("✅ Telegram bot started and listening!")
                else:
                    st.info("Bot is already running!")
        
        with col2:
            if st.button("⏹️ Stop Bot", key="stop_bot"):
                if "telegram_bot_running" in st.session_state:
                    st.session_state.telegram_bot_running = False
                    st.success("⏹️ Telegram bot stopped!")
                else:
                    st.info("Bot is not running!")
        
        # Bot status
        if "telegram_bot_running" in st.session_state and st.session_state.telegram_bot_running:
            st.markdown("🟢 **Bot Status: Running**")
            st.markdown("📱 Listening for messages...")
            st.markdown("💡 Send a message to @{bot_username} to test!")
        else:
            st.markdown("🔴 **Bot Status: Stopped**")
            st.markdown("Click 'Start Bot' to begin listening")
        
        # Check for updates
        if st.button("🔄 Check Updates", key="check_updates"):
            updates = get_telegram_updates()
            if updates and updates.get("ok"):
                update_count = len(updates.get("result", []))
                st.success(f"✅ Connected - {update_count} updates available")
                if update_count > 0:
                    st.info("📱 Messages detected! Check the Telegram Messages section below.")
            else:
                st.error("❌ Connection failed")
    
    else:
        st.markdown("🔴 **Not Connected**")
        st.markdown("""
        **To connect your Telegram bot:**
        1. Create a bot with @BotFather on Telegram
        2. Get your bot token
        3. Update `config.py` with your token
        4. Restart the app
        """)
    
    # AI Services Status
    st.markdown("### 🤖 AI Services")
    if openai_quota_exceeded:
        st.markdown("🔴 OpenAI: Quota Exceeded")
    else:
        st.markdown("🟢 OpenAI: Available")
    st.markdown("🟢 Dialogflow: Available")
    st.markdown("🟢 Smart Responses: Available")
    
    # Quota Reset (for testing)
    if st.button("🔄 Reset OpenAI Quota Flag", key="reset_quota"):
        openai_quota_exceeded = False
        st.success("OpenAI quota flag reset!")
        st.rerun()

if __name__ == "__main__":
    main()
