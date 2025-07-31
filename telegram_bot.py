#!/usr/bin/env python3
"""
Telegram Bot for Customer Support
This script runs independently and handles Telegram messages
"""

import os
import time
import requests
import json
from datetime import datetime
from config import (
    OPENAI_API_KEY,
    DIALOGFLOW_PROJECT_ID,
    GOOGLE_APPLICATION_CREDENTIALS_PATH,
    TELEGRAM_BOT_TOKEN,
)

# Set Google credentials for Dialogflow
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS_PATH

# Telegram bot setup
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Global variables
openai_quota_exceeded = False
last_update_id = 0

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

def get_telegram_updates():
    """Get updates from Telegram bot"""
    global last_update_id
    try:
        url = f"{TELEGRAM_API_URL}/getUpdates"
        params = {"offset": last_update_id + 1, "timeout": 30}
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print(f"Telegram error: {str(e)}")
        return None

def detect_intent_text(session_id, text, language_code="en"):
    """Dialogflow intent detection"""
    try:
        from google.cloud import dialogflow_v2 as dialogflow
        dialogflow_session_client = dialogflow.SessionsClient()
        
        session = dialogflow_session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.QueryInput(text=text_input)

        response = dialogflow_session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        fulfillment_text = response.query_result.fulfillment_text
        
        if fulfillment_text and fulfillment_text.strip():
            # Check for generic responses
            generic_responses = [
                "i didn't get that", "i'm sorry, i didn't quite catch that",
                "would you like to talk to a support agent", "can you try saying it differently",
                "i didn't catch that", "could you please rephrase"
            ]
            
            response_lower = fulfillment_text.lower()
            is_generic = any(generic in response_lower for generic in generic_responses)
            
            if not is_generic:
                return fulfillment_text
        return None
    except Exception as e:
        print(f"Dialogflow error: {str(e)}")
        return None

def get_smart_response(user_input):
    """Smart response system"""
    user_input_lower = user_input.lower()
    
    # Greeting responses
    if any(word in user_input_lower for word in ['hello', 'hi', 'hey']):
        return "Hello! 👋 I'm your AI support assistant. How can I help you today?"
    
    # Help requests
    elif any(word in user_input_lower for word in ['help', 'support', 'assist']):
        return """I'm here to help! Here's what I can assist with:

🔍 Product Information
📦 Order Management  
🔄 Returns & Refunds
🔧 Technical Support
📞 Contact Information
⏰ Business Hours

What would you like to know about?"""
    
    # Contact requests
    elif any(word in user_input_lower for word in ['contact', 'phone', 'speak', 'human']):
        return """You can reach our customer service team:

📞 Phone: 1-800-SUPPORT (24/7)
📧 Email: support@company.com
💬 Live Chat: Available on our website

⏰ Business Hours: Mon-Fri 8AM-8PM EST"""
    
    # Business hours
    elif any(word in user_input_lower for word in ['hours', 'open', 'time']):
        return """Our customer support hours:

🕐 Monday-Friday: 8 AM - 8 PM EST
🕐 Saturday: 9 AM - 6 PM EST  
🕐 Sunday: 10 AM - 4 PM EST

📞 24/7 Emergency Support available for urgent issues"""
    
    return None

def process_telegram_message(chat_id, message_text):
    """Process incoming Telegram message and return response"""
    print(f"Processing message from {chat_id}: {message_text}")
    
    # Try Dialogflow first
    dialogflow_response = detect_intent_text(f"telegram-{chat_id}", message_text)
    if dialogflow_response:
        return dialogflow_response
    
    # Try smart response system
    smart_response = get_smart_response(message_text)
    if smart_response:
        return smart_response
    
    # Final fallback
    return "I'm here to help! Please contact our support team at 1-800-SUPPORT for immediate assistance."

def main():
    """Main bot loop"""
    global last_update_id
    
    print("🤖 Starting Telegram Customer Support Bot...")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    # Test bot connection
    test_response = requests.get(f"{TELEGRAM_API_URL}/getMe")
    if test_response.status_code == 200:
        bot_info = test_response.json()
        print(f"✅ Bot connected: @{bot_info['result']['username']}")
    else:
        print("❌ Bot connection failed!")
        return
    
    print("🔄 Starting message loop...")
    
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
                            # Process message and get response
                            response = process_telegram_message(chat_id, text)
                            
                            # Send response back
                            send_telegram_message(chat_id, response)
                            print(f"📤 Sent response to {chat_id}")
                    
                    # Update last_update_id
                    last_update_id = max(last_update_id, update["update_id"])
            
            time.sleep(1)  # Wait before next check
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {str(e)}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main() 