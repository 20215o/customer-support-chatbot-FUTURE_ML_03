# 🤖 AI Customer Support Chatbot

A comprehensive customer support chatbot with multiple AI backends, Telegram integration, and smart fallback systems.

## ✨ Features

### 🧠 **Multi-AI Architecture**
- **Dialogflow ES**: Primary intent detection and structured responses
- **OpenAI ChatGPT**: Advanced conversational AI for complex queries
- **Smart Response System**: Rule-based fallback for common queries
- **Smart Fallback**: Automatically switches to Dialogflow when OpenAI quota is exceeded

### 📱 **Telegram Integration**
- Standalone Telegram bot (`telegram_bot.py`)
- Integrated Telegram status monitoring in Streamlit app
- Real-time message processing
- Markdown support for rich formatting

### 🎯 **Smart Response Logic**
1. **Dialogflow First**: Always tries Dialogflow for intent detection
2. **Generic Response Detection**: Identifies and rejects unhelpful Dialogflow responses
3. **ChatGPT Fallback**: Uses OpenAI for complex or unique queries
4. **Smart Responses**: Rule-based system for common customer service queries
5. **Quota Management**: Automatically switches to Dialogflow when OpenAI quota is exceeded

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure API Keys**
Edit `config.py` with your API keys:
```python
OPENAI_API_KEY = "your-openai-key"
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
DIALOGFLOW_PROJECT_ID = "your-dialogflow-project-id"
GOOGLE_APPLICATION_CREDENTIALS_PATH = "path/to/dialogflow_key.json"
```

### 3. **Run the Streamlit App**
```bash
streamlit run app.py
```

### 4. **Run Telegram Bot (Optional)**
```bash
python telegram_bot.py
```

## 📊 Response Types

### **Dialogflow Responses** 🎯
- Specific customer service queries
- Intent-based responses
- Structured information

### **ChatGPT Responses** 🧠
- Complex or unique questions
- Creative responses
- When Dialogflow gives generic responses

### **Smart Responses** ⚡
- Common customer service queries
- Rule-based responses
- Fast and reliable

### **Fallback Responses** 🛟
- When all AI services are unavailable
- Contact information and support options

## 🔧 Smart Fallback System

### **When OpenAI Quota is Exceeded:**
1. ✅ **Dialogflow continues working**
2. ✅ **Smart responses remain available**
3. ✅ **Seamless user experience**
4. ✅ **No service interruption**

### **Response Priority:**
1. **Dialogflow** (if meaningful response)
2. **Smart Responses** (rule-based)
3. **ChatGPT** (if quota available)
4. **Fallback** (contact information)

## 📱 Telegram Bot Features

### **Standalone Operation**
- Runs independently of Streamlit app
- Continuous message monitoring
- Automatic response generation

### **Message Processing**
- Dialogflow intent detection
- Smart response system
- Fallback to contact information

### **Bot Commands**
- `/start` - Welcome message
- `/help` - Available services
- `/contact` - Support information

## 🎛️ Streamlit Dashboard

### **Main Features**
- Real-time chat interface
- Response source tracking
- Statistics dashboard
- Quick action buttons

### **Sidebar Controls**
- Chat history management
- Export functionality
- System status monitoring
- Telegram bot status
- Quota management

### **Quick Actions**
- Contact Support
- Order Status
- Returns & Refunds
- Business Hours
- Test ChatGPT responses

## 🔍 Testing Different Response Types

### **Dialogflow Responses:**
- "Hello"
- "Where is my order?"
- "What are your business hours?"

### **ChatGPT Responses:**
- "Tell me a joke"
- "What's the weather like?"
- "How do I make pizza?"
- "What's the meaning of life?"

### **Smart Responses:**
- "I need help"
- "Contact support"
- "Return policy"

## 📈 Statistics Tracking

The app tracks:
- **Total Messages**: All user interactions
- **Dialogflow Responses**: Intent-based responses
- **ChatGPT Responses**: AI-generated responses
- **Fallback Responses**: Contact information

## 🛠️ Configuration

### **Environment Variables**
All configuration is in `config.py`:
- OpenAI API Key
- Telegram Bot Token
- Dialogflow Project ID
- Google Credentials Path

### **Dialogflow Setup**
1. Create Dialogflow project
2. Set up intents and responses
3. Download service account key
4. Update `config.py` with project ID

### **Telegram Bot Setup**
1. Create bot with @BotFather
2. Get bot token
3. Update `config.py`
4. Start conversation with bot

## 🔄 Quota Management

### **Automatic Detection**
- Monitors OpenAI API responses
- Detects quota exceeded errors
- Switches to Dialogflow automatically

### **Manual Reset**
- Use "Reset OpenAI Quota Flag" button
- Restores ChatGPT functionality
- Useful for testing

## 📞 Support Features

### **Contact Information**
- Phone: 1-800-SUPPORT (24/7)
- Email: support@company.com
- Live Chat: Available on website
- Business Hours: Mon-Fri 8AM-8PM EST

### **Quick Actions**
- One-click contact support
- Order status checking
- Returns and refunds
- Business hours lookup

## 🎨 UI/UX Features

### **Professional Design**
- Gradient backgrounds
- Glass-morphism effects
- Smooth animations
- Responsive layout

### **User Experience**
- Typing indicators
- Message source badges
- Statistics dashboard
- Export functionality

## 🔒 Security

### **API Key Management**
- Keys stored in `config.py`
- Environment variable support
- Secure credential handling

### **Error Handling**
- Graceful API failures
- User-friendly error messages
- Fallback responses

## 🚀 Deployment

### **Local Development**
```bash
streamlit run app.py
```

### **Production Deployment**
- Deploy to Streamlit Cloud
- Set up Telegram webhook
- Configure environment variables
- Monitor API quotas

## 📝 License

This project is for educational and demonstration purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Built with ❤️ using Streamlit, OpenAI, Dialogflow, and Telegram Bot API** 