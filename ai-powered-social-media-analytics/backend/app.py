"""
AI-Powered Social Media Analytics Platform - Flask Backend
Main application file with all REST API endpoints
"""

import os
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
from utils_mock import (
    register_user,
    login_user,
    connect_account,
    get_connected_accounts,
    get_posts,
    add_post,
    analyze_sentiment,
    get_ai_insights,
    get_analytics_summary,
    generate_recommendations,
    delete_account,
    update_post,
    get_trending_posts,
    get_user_stats,
    export_analytics,
    verify_token,
    analyze_hashtags,
    predict_engagement,
    get_audience_insights,
    get_competitor_analysis,
    get_content_calendar,
    detect_anomalies,
    forecast_growth
)
from dotenv import load_dotenv
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from faker import Faker
import random

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key_change_in_production')

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Faker for mock data generation
fake = Faker()


# ==================== Token Verification Decorator ====================

def token_required(f):
    """Decorator to verify JWT token and extract user_id"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'error': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Verify token
        user_id, error = verify_token(token)
        if error:
            return jsonify({'error': error}), 401
        
        # Store user_id in g object for use in route handler
        g.user_id = user_id
        return f(*args, **kwargs)
    
    return decorated

# ==================== Authentication Endpoints ====================

@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("50 per hour")
def register():
    """Register a new user"""
    try:
        data = request.json
        return register_user(data)
    except Exception as e:
        logger.error(f"Register error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("50 per hour")
def login():
    """Login user and return JWT token"""
    try:
        data = request.json
        return login_user(data)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== Social Account Endpoints ====================

@app.route('/api/accounts/connect', methods=['POST'])
@token_required
def connect_oauth():
    """Connect a social media account (OAuth mock or real)"""
    try:
        data = request.json
        data['user_id'] = g.user_id  # Add user_id from token
        return connect_account(data)
    except Exception as e:
        logger.error(f"Connect account error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/accounts', methods=['GET'])
@token_required
def get_accounts():
    """Get all connected accounts for a user"""
    try:
        return get_connected_accounts(g.user_id)
    except Exception as e:
        logger.error(f"Get accounts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@token_required
def delete_social_account(account_id):
    """Delete a connected social account"""
    try:
        return delete_account(g.user_id, account_id)
    except Exception as e:
        logger.error(f"Delete account error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== Posts & Analytics Endpoints ====================

@app.route('/api/posts', methods=['GET'])
@token_required
def fetch_posts():
    """Fetch posts for a user or account"""
    try:
        account_id = request.args.get('account_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        return get_posts(g.user_id, account_id, limit, offset)
    except Exception as e:
        logger.error(f"Get posts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/posts', methods=['POST'])
@token_required
def create_post():
    """Add a new post to analytics"""
    try:
        data = request.json
        data['user_id'] = g.user_id  # Add user_id from token
        return add_post(g.user_id, data)
    except Exception as e:
        logger.error(f"Add post error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@token_required
def edit_post(post_id):
    """Update a post"""
    try:
        data = request.json
        return update_post(g.user_id, post_id, data)
    except Exception as e:
        logger.error(f"Update post error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analyze', methods=['POST'])
@token_required
def analyze():
    """Analyze posts for sentiment, trends, AI score"""
    try:
        data = request.json
        data['user_id'] = g.user_id  # Add user_id from token
        return analyze_sentiment(data)
    except Exception as e:
        logger.error(f"Analyze error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/insights', methods=['GET'])
@token_required
def insights():
    """Get AI-generated insights and recommendations"""
    try:
        return get_ai_insights(g.user_id)
    except Exception as e:
        logger.error(f"Get insights error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/summary', methods=['GET'])
@token_required
def analytics_summary():
    """Get weekly/monthly analytics summary"""
    try:
        period = request.args.get('period', '7')
        return get_analytics_summary(g.user_id, period)
    except Exception as e:
        logger.error(f"Get analytics summary error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/recommendations', methods=['GET'])
@token_required
def recommendations():
    """Get AI recommendations for posting strategy"""
    try:
        return generate_recommendations(g.user_id)
    except Exception as e:
        logger.error(f"Get recommendations error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/posts/trending', methods=['GET'])
@token_required
def trending_posts():
    """Get trending posts for a user"""
    try:
        limit = int(request.args.get('limit', 10))
        return get_trending_posts(g.user_id, limit)
    except Exception as e:
        logger.error(f"Get trending posts error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/stats', methods=['GET'])
@token_required
def user_stats():
    """Get user statistics"""
    try:
        return get_user_stats(g.user_id)
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/export', methods=['GET'])
@token_required
def export_data():
    """Export user analytics data"""
    try:
        format_type = request.args.get('format', 'json')
        return export_analytics(g.user_id, format_type)
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== Advanced AI Analytics Endpoints ====================

@app.route('/api/analytics/hashtags', methods=['GET'])
@token_required
def hashtag_analysis():
    """Advanced hashtag analysis and performance metrics"""
    try:
        return analyze_hashtags(g.user_id)
    except Exception as e:
        logger.error(f"Hashtag analysis error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/predict-engagement', methods=['POST'])
@token_required
def predict_post_engagement():
    """Predict engagement for new content"""
    try:
        data = request.json
        return predict_engagement(data)
    except Exception as e:
        logger.error(f"Predict engagement error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/audience-insights', methods=['GET'])
@token_required
def audience_insights():
    """Get AI-powered audience demographics and behavior"""
    try:
        return get_audience_insights(g.user_id)
    except Exception as e:
        logger.error(f"Audience insights error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/competitor-analysis', methods=['GET'])
@token_required
def competitor_analysis():
    """Get competitor benchmarking and analysis"""
    try:
        industry = request.args.get('industry', 'technology')
        return get_competitor_analysis(g.user_id, industry)
    except Exception as e:
        logger.error(f"Competitor analysis error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/content-calendar', methods=['GET'])
@token_required
def content_calendar():
    """Get smart content calendar with optimization"""
    try:
        return get_content_calendar(g.user_id)
    except Exception as e:
        logger.error(f"Content calendar error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/anomalies', methods=['GET'])
@token_required
def anomaly_detection():
    """Detect anomalies in performance trends"""
    try:
        return detect_anomalies(g.user_id)
    except Exception as e:
        logger.error(f"Anomaly detection error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/analytics/forecast', methods=['GET'])
@token_required
def growth_forecast():
    """Get growth forecasting predictions"""
    try:
        months = int(request.args.get('months', 3))
        return forecast_growth(g.user_id, months)
    except Exception as e:
        logger.error(f"Growth forecast error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ==================== YouTube Data API Endpoint ====================

# Load YouTube API credentials
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

@app.route('/youtube/videos', methods=['GET'])
def get_youtube_videos():
    """Fetches advanced mock YouTube videos."""
    query = request.args.get('query', 'AI-powered analytics')
    mock_data = {
        "items": [
            {
                "id": {"videoId": fake.uuid4()},
                "snippet": {
                    "title": f"{query} - {fake.sentence(nb_words=6)}",
                    "description": fake.text(max_nb_chars=200),
                    "channelTitle": fake.company(),
                    "publishedAt": fake.iso8601(),
                    "viewCount": random.randint(1000, 1000000),
                    "likeCount": random.randint(100, 50000),
                    "commentCount": random.randint(10, 5000)
                }
            } for _ in range(10)
        ]
    }
    return jsonify(mock_data)

# ==================== Twitter Data API Endpoint ====================

# Load Twitter API credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")

# Generate Bearer Token
def get_twitter_bearer_token():
    """Generates a Bearer Token for Twitter API requests."""
    url = "https://api.twitter.com/oauth2/token"
    headers = {
        "Authorization": f"Basic {os.getenv('TWITTER_BASIC_AUTH')}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception("Failed to generate Bearer Token")

@app.route('/twitter/tweets', methods=['GET'])
def get_twitter_tweets():
    """Fetches advanced mock Twitter tweets."""
    query = request.args.get('query', 'AI-powered analytics')
    mock_data = {
        "data": [
            {
                "id": fake.uuid4(),
                "text": f"{query} - {fake.sentence(nb_words=12)}",
                "author": {
                    "name": fake.name(),
                    "username": fake.user_name(),
                    "followers_count": random.randint(100, 1000000),
                    "verified": random.choice([True, False])
                },
                "created_at": fake.iso8601(),
                "retweet_count": random.randint(10, 5000),
                "like_count": random.randint(100, 50000)
            } for _ in range(10)
        ]
    }
    return jsonify(mock_data)


# ==================== Health Check ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_ENV') == 'development', host='0.0.0.0', port=5000)
