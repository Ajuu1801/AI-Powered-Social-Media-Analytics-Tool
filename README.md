# AI-Powered Social Media Analytics Tool

An advanced AI‑driven platform that analyzes content from **YouTube, Twitter, Instagram, LinkedIn, Reddit**, and more — providing insights using NLP, sentiment analysis, keyword extraction, trend detection, and AI summaries.

## 🚀 Features
- Multi‑platform social media data analytics  
- AI‑powered sentiment & emotion detection  
- Trend & keyword extraction  
- Content performance scoring  
- Dark modern UI (React)  
- Backend with FastAPI/Flask  
- Supports multiple API keys  
- Export reports (PDF/CSV)  
- Fully modular & scalable design  

## 📂 Project Structure
```
/backend
    ├── app.py / main.py
    ├── services/
    ├── utils/
    ├── requirements.txt
    └── .env (create this)

/frontend
    ├── src/
    ├── components/
    ├── pages/
    └── package.json
```

## 🔐 Environment Variables (`.env`)
Create a `.env` file in **backend** and add:

```
YOUTUBE_API_KEY=your_youtube_api_key
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_SECRET=your_reddit_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
LINKEDIN_ACCESS_TOKEN=your_linkedin_token

OPENAI_API_KEY=your_openai_api_key
```

## ▶️ Running the Project

### Backend
```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```
cd frontend
npm install
npm start
```

## 📊 Output
- AI‑generated insights  
- Sentiment graphs  
- Engagement analysis  
- Summary reports  

## 🤝 Contributing
Pull requests are welcome! For major changes, open an issue first.

## 📜 License
MIT License.

