"""
Mock database utilities for testing without MySQL
Stores data in memory with persistent file backup
"""

import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from flask import jsonify
import json
import csv
import io
from cachetools import TTLCache
from email_validator import validate_email, EmailNotValidError

# In-memory data storage
users_db = {}
accounts_db = {}
posts_db = {}
analytics_cache = TTLCache(maxsize=1000, ttl=1800)

# File-based persistence
DATA_FILE = 'mock_data.json'

JWT_SECRET = os.getenv('JWT_SECRET', 'dev_jwt_secret_change_in_production')

# Load persistent data
def load_data():
    global users_db, accounts_db, posts_db
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                users_db = data.get('users', {})
                accounts_db = data.get('accounts', {})
                posts_db = data.get('posts', {})
        except:
            pass

# Save persistent data
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({
            'users': users_db,
            'accounts': accounts_db,
            'posts': posts_db
        }, f, indent=2, default=str)

load_data()

# ==================== Validation Functions ====================

def validate_email_format(email):
    """Validate email format"""
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError:
        return None

def validate_username(username):
    """Validate username format"""
    if not username or len(username) < 3:
        return False
    if len(username) > 50:
        return False
    if not username.replace('_', '').replace('-', '').isalnum():
        return False
    return True

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit


# ==================== Authentication Functions ====================

def register_user(data):
    """Register a new user with validation and bcrypt hashing"""
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Validation
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    if not validate_username(username):
        return jsonify({'error': 'Invalid username. Must be 3-50 chars, alphanumeric.'}), 400

    valid_email = validate_email_format(email)
    if not valid_email:
        return jsonify({'error': 'Invalid email format'}), 400

    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    # Check for duplicates
    for user_id, user in users_db.items():
        if user['username'] == username:
            return jsonify({'error': 'Username already exists'}), 409
        if user['email'] == valid_email:
            return jsonify({'error': 'Email already exists'}), 409

    # Hash password with bcrypt
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        user_id = str(len(users_db) + 1)
        users_db[user_id] = {
            'id': int(user_id),
            'username': username,
            'email': valid_email,
            'password_hash': hashed.decode('utf-8'),
            'created_at': datetime.now().isoformat()
        }
        save_data()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': int(user_id)
        }), 201
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


def login_user(data):
    """Authenticate user and return JWT token"""
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        # Find user by email
        user = None
        for u in users_db.values():
            if u['email'] == email:
                user = u
                break

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Create JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'email': user['email'],
                'username': user['username'],
                'exp': datetime.utcnow() + timedelta(days=30)
            }, JWT_SECRET, algorithm='HS256')

            return jsonify({
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'created_at': user['created_at']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


def verify_token(token):
    """Verify JWT token and return (user_id, error)"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('user_id')
        if not user_id:
            return None, 'Invalid token: no user_id'
        return user_id, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'
    except Exception as e:
        return None, f'Token verification failed: {str(e)}'


# ==================== Social Account Functions ====================

def connect_account(data):
    """Connect a social media account"""
    user_id = data.get('user_id')
    platform = data.get('platform', '').lower()
    account_name = data.get('account_name', '').strip()

    if not (user_id and platform and account_name):
        return jsonify({'error': 'Missing required fields'}), 400

    if platform not in ['instagram', 'twitter', 'youtube', 'tiktok', 'linkedin']:
        return jsonify({'error': 'Unsupported platform'}), 400

    try:
        account_id = str(len(accounts_db) + 1)
        accounts_db[account_id] = {
            'id': int(account_id),
            'user_id': user_id,
            'platform': platform,
            'account_name': account_name,
            'access_token': f'mock_token_{account_id}',
            'connected_at': datetime.now().isoformat()
        }
        save_data()
        
        # Clear cache
        if f'accounts_{user_id}' in analytics_cache:
            del analytics_cache[f'accounts_{user_id}']
        
        return jsonify({
            'message': 'Account connected',
            'account': accounts_db[account_id]
        }), 201
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


def get_connected_accounts(user_id):
    """Get all connected accounts for a user"""
    try:
        cache_key = f'accounts_{user_id}'
        if cache_key in analytics_cache:
            return jsonify({
                'accounts': analytics_cache[cache_key],
                'timestamp': datetime.now().isoformat(),
                'from_cache': True
            }), 200

        accounts = [acc for acc in accounts_db.values() if acc['user_id'] == user_id]
        analytics_cache[cache_key] = accounts
        
        return jsonify({
            'accounts': accounts,
            'timestamp': datetime.now().isoformat(),
            'from_cache': False
        }), 200
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


def delete_account(user_id, account_id):
    """Delete a connected social account"""
    try:
        account_id_str = str(account_id)
        if account_id_str not in accounts_db:
            return jsonify({'error': 'Account not found'}), 404
        
        if accounts_db[account_id_str]['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        del accounts_db[account_id_str]
        save_data()
        
        # Clear cache
        if f'accounts_{user_id}' in analytics_cache:
            del analytics_cache[f'accounts_{user_id}']
        
        return jsonify({'message': 'Account deleted'}), 200
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


# ==================== Posts Functions ====================

def get_posts(user_id, account_id=None, limit=50, offset=0):
    """Get posts for a user"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        if account_id:
            posts = [p for p in posts if p['account_id'] == account_id]
        
        posts = sorted(posts, key=lambda x: x['post_date'], reverse=True)
        paginated = posts[offset:offset+limit]
        
        return jsonify({
            'posts': paginated,
            'total': len(posts),
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def add_post(user_id, data):
    """Add a new post"""
    try:
        account_id = data.get('account_id')
        content = data.get('content', '').strip()
        
        if not content or not account_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        post_id = str(len(posts_db) + 1)
        posts_db[post_id] = {
            'id': int(post_id),
            'user_id': user_id,
            'account_id': account_id,
            'content': content,
            'post_date': datetime.now().isoformat(),
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'impressions': 0,
            'sentiment': 'neutral',
            'ai_score': 0.5,
            'keywords': '',
            'created_at': datetime.now().isoformat()
        }
        save_data()
        
        return jsonify({
            'message': 'Post added',
            'post': posts_db[post_id]
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def update_post(user_id, post_id, data):
    """Update a post"""
    try:
        post_id_str = str(post_id)
        if post_id_str not in posts_db:
            return jsonify({'error': 'Post not found'}), 404
        
        if posts_db[post_id_str]['user_id'] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        post = posts_db[post_id_str]
        if 'content' in data:
            post['content'] = data['content']
        if 'likes' in data:
            post['likes'] = data['likes']
        if 'comments' in data:
            post['comments'] = data['comments']
        if 'shares' in data:
            post['shares'] = data['shares']
        
        save_data()
        return jsonify({'message': 'Post updated', 'post': post}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Analytics Functions ====================

def analyze_sentiment(data):
    """Mock sentiment analysis"""
    content = data.get('content', '').lower()
    
    positive_words = ['good', 'great', 'excellent', 'love', 'amazing', 'awesome', 'fantastic']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'horrible', 'poor', 'worst']
    
    pos_count = sum(1 for word in positive_words if word in content)
    neg_count = sum(1 for word in negative_words if word in content)
    
    if pos_count > neg_count:
        sentiment = 'positive'
        score = 0.7 + (pos_count * 0.1)
    elif neg_count > pos_count:
        sentiment = 'negative'
        score = 0.3 - (neg_count * 0.1)
    else:
        sentiment = 'neutral'
        score = 0.5
    
    return jsonify({
        'sentiment': sentiment,
        'score': min(1.0, max(0.0, score)),
        'confidence': 0.85
    }), 200


def get_ai_insights(user_id):
    """Get AI insights"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        
        return jsonify({
            'insights': [
                'Your engagement rate is above average',
                'Posts with emojis get 25% more likes',
                'Best posting time: 6-9 PM',
                'Instagram content performs best',
                'Video posts get 3x more engagement'
            ],
            'total_posts': len(posts),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_analytics_summary(user_id, period='7'):
    """Get analytics summary"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        total_likes = sum(p.get('likes', 0) for p in posts)
        total_comments = sum(p.get('comments', 0) for p in posts)
        total_shares = sum(p.get('shares', 0) for p in posts)
        
        return jsonify({
            'period': f'{period} days',
            'total_posts': len(posts),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'average_engagement': round((total_likes + total_comments + total_shares) / max(1, len(posts)), 2),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate_recommendations(user_id):
    """Generate recommendations"""
    return jsonify({
        'posting_times': [
            {'time': '7:00 AM', 'reason': 'Peak morning engagement'},
            {'time': '12:00 PM', 'reason': 'Lunch break scrolling'},
            {'time': '6:00 PM', 'reason': 'Evening commute'},
            {'time': '9:00 PM', 'reason': 'Night-time social media peak'}
        ],
        'engagement_tips': [
            'Use 3-5 relevant hashtags',
            'Include a call-to-action',
            'Post consistently 3-5 times per week',
            'Engage with follower comments within first hour',
            'Use video content (gets 3x more engagement)',
            'Share user-generated content',
            'Post when your audience is most active'
        ],
        'hashtag_strategy': {
            'trending': ['#socialmedia', '#digital', '#marketing'],
            'niche': ['#contentcreator', '#socialmediagrowth'],
            'brand': ['#yourbranding']
        },
        'timestamp': datetime.now().isoformat()
    }), 200


def get_trending_posts(user_id, limit=10):
    """Get trending posts"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        posts = sorted(posts, key=lambda x: x['likes'] + x['comments'] + x['shares'], reverse=True)
        return jsonify({
            'posts': posts[:limit],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_user_stats(user_id):
    """Get user statistics"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        accounts = [a for a in accounts_db.values() if a['user_id'] == user_id]
        
        total_likes = sum(p.get('likes', 0) for p in posts)
        total_comments = sum(p.get('comments', 0) for p in posts)
        total_shares = sum(p.get('shares', 0) for p in posts)
        
        return jsonify({
            'total_accounts': len(accounts),
            'total_posts': len(posts),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_engagement': total_likes + total_comments + total_shares,
            'average_post_engagement': round((total_likes + total_comments + total_shares) / max(1, len(posts)), 2),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def export_analytics(user_id, format_type='json'):
    """Export analytics data"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        
        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Content', 'Likes', 'Comments', 'Shares', 'Date'])
            for p in posts:
                writer.writerow([p['id'], p['content'][:50], p['likes'], p['comments'], p['shares'], p['post_date']])
            return output.getvalue(), 200
        else:
            return jsonify({
                'posts': posts,
                'exported_at': datetime.now().isoformat()
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Advanced AI Analytics Functions ====================

def analyze_hashtags(user_id):
    """Advanced hashtag analysis with performance metrics"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        hashtag_metrics = {}
        
        for post in posts:
            content = post.get('content', '').lower()
            words = content.split()
            hashtags = [w for w in words if w.startswith('#')]
            
            for tag in hashtags:
                if tag not in hashtag_metrics:
                    hashtag_metrics[tag] = {
                        'tag': tag,
                        'uses': 0,
                        'total_engagement': 0,
                        'avg_likes': 0,
                        'performance': 'neutral'
                    }
                hashtag_metrics[tag]['uses'] += 1
                engagement = post.get('likes', 0) + post.get('comments', 0) + post.get('shares', 0)
                hashtag_metrics[tag]['total_engagement'] += engagement
        
        # Calculate averages and performance rating
        for tag_data in hashtag_metrics.values():
            if tag_data['uses'] > 0:
                tag_data['avg_likes'] = round(tag_data['total_engagement'] / tag_data['uses'], 2)
                if tag_data['avg_likes'] > 100:
                    tag_data['performance'] = 'excellent'
                elif tag_data['avg_likes'] > 50:
                    tag_data['performance'] = 'good'
                elif tag_data['avg_likes'] > 20:
                    tag_data['performance'] = 'fair'
                else:
                    tag_data['performance'] = 'poor'
        
        top_hashtags = sorted(hashtag_metrics.values(), 
                            key=lambda x: x['total_engagement'], reverse=True)[:15]
        
        return jsonify({
            'top_hashtags': top_hashtags,
            'total_unique_hashtags': len(hashtag_metrics),
            'trending_this_month': top_hashtags[:5],
            'recommendations': [
                {'tag': '#ai', 'reason': 'Trending in tech'},
                {'tag': '#socialmedia', 'reason': 'High engagement'},
                {'tag': '#marketing', 'reason': 'Relevant to your niche'}
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def predict_engagement(data):
    """AI model to predict engagement for new content"""
    try:
        content = data.get('content', '').strip()
        platform = data.get('platform', 'instagram')
        
        # Simulated AI scoring based on content characteristics
        score = 0.5
        factors = []
        
        # Length scoring (optimal 100-150 chars)
        if 100 <= len(content) <= 150:
            score += 0.2
            factors.append({'factor': 'Content Length', 'impact': '+20%', 'tip': 'Perfect length for engagement'})
        
        # Emoji usage
        emoji_count = sum(1 for char in content if ord(char) > 0x1F300)
        if 1 <= emoji_count <= 3:
            score += 0.15
            factors.append({'factor': 'Emojis', 'impact': '+15%', 'tip': 'Great emoji usage'})
        
        # Question marks (encourages comments)
        if '?' in content:
            score += 0.1
            factors.append({'factor': 'Call-to-Action', 'impact': '+10%', 'tip': 'Questions boost engagement'})
        
        # Hashtags
        hashtag_count = len([w for w in content.split() if w.startswith('#')])
        if 3 <= hashtag_count <= 5:
            score += 0.15
            factors.append({'factor': 'Hashtags', 'impact': '+15%', 'tip': '3-5 hashtags optimal'})
        
        # Engagement multiplier by platform
        platform_multipliers = {'instagram': 1.2, 'tiktok': 1.3, 'twitter': 0.9, 'linkedin': 1.0, 'youtube': 1.4}
        platform_mult = platform_multipliers.get(platform, 1.0)
        predicted_engagement = round(min(0.95, max(0.1, score * platform_mult)) * 1000)
        
        return jsonify({
            'predicted_engagement': predicted_engagement,
            'confidence_score': round(min(1.0, score), 2),
            'engagement_rating': 'High' if score > 0.7 else 'Good' if score > 0.5 else 'Average',
            'factors': factors,
            'platform_boost': f'{(platform_mult - 1) * 100:.0f}%' if platform_mult > 1 else 'Standard',
            'ai_recommendation': 'Great content! This has high potential for engagement.' if score > 0.7 else 'Good, but consider adjustments for better performance.',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_audience_insights(user_id):
    """AI-powered audience demographics and behavior analysis"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        accounts = [a for a in accounts_db.values() if a['user_id'] == user_id]
        
        total_engagement = sum(p.get('likes', 0) + p.get('comments', 0) + p.get('shares', 0) for p in posts)
        
        return jsonify({
            'audience_size': 'Growing - Add more hashtags' if accounts else 'No data',
            'engagement_rate': round((total_engagement / max(1, len(posts))) * 100, 2) if posts else 0,
            'demographics': {
                'primary_age': '18-34',
                'gender_split': {'male': 45, 'female': 55},
                'top_locations': ['USA', 'India', 'UK', 'Canada', 'Australia'],
                'interests': ['Technology', 'Marketing', 'Business', 'Lifestyle']
            },
            'behavior_patterns': {
                'most_active_day': 'Saturday',
                'peak_engagement_time': '7:00 PM - 9:00 PM',
                'avg_session_duration': '8 minutes',
                'follower_growth_rate': '+15% this month'
            },
            'audience_sentiment': {
                'positive': 68,
                'neutral': 25,
                'negative': 7,
                'sentiment_trend': 'Improving'
            },
            'content_preferences': [
                'Educational content (42%)',
                'Inspirational posts (38%)',
                'Behind-the-scenes (35%)',
                'Tutorial videos (28%)'
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_competitor_analysis(user_id, industry='technology'):
    """AI-powered competitor benchmarking"""
    try:
        user_posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        user_engagement = sum(p.get('likes', 0) + p.get('comments', 0) + p.get('shares', 0) for p in user_posts) / max(1, len(user_posts))
        
        return jsonify({
            'industry': industry,
            'your_metrics': {
                'avg_engagement': round(user_engagement, 2),
                'content_frequency': f'{len(user_posts)} posts',
                'avg_post_length': round(sum(len(p.get('content', '')) for p in user_posts) / max(1, len(user_posts)), 0),
                'hashtag_strategy': 'Advanced'
            },
            'industry_benchmarks': {
                'avg_engagement': 150.50,
                'avg_post_frequency': 25,
                'avg_post_length': 120,
                'hashtag_avg': 4.2
            },
            'vs_competition': {
                'engagement_rank': 'Top 25%' if user_engagement > 100 else 'Top 50%',
                'posting_frequency': 'On par' if len(user_posts) >= 20 else 'Below average',
                'content_quality': 'Excellent' if user_engagement > 150 else 'Good',
                'hashtag_optimization': 'Well-optimized'
            },
            'growth_opportunities': [
                'Increase posting frequency to 5 posts/week',
                'Use trending hashtags in your niche',
                'Leverage video content (3x engagement)',
                'Cross-promote on multiple platforms',
                'Engage with audience comments within 1 hour'
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_content_calendar(user_id):
    """Smart content calendar with optimization suggestions"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        
        calendar = {
            'scheduled_posts': [
                {
                    'date': '2025-12-15',
                    'time': '7:00 PM',
                    'content_type': 'Tutorial',
                    'platform': 'Instagram',
                    'predicted_reach': 1250,
                    'status': 'Scheduled'
                },
                {
                    'date': '2025-12-16',
                    'time': '12:00 PM',
                    'content_type': 'Carousel',
                    'platform': 'LinkedIn',
                    'predicted_reach': 850,
                    'status': 'Scheduled'
                }
            ],
            'content_themes': [
                'Monday - Motivation Monday',
                'Wednesday - Tutorial Wednesday',
                'Friday - Feature Friday',
                'Sunday - Behind-the-scenes'
            ],
            'optimization_tips': [
                'Post Tue-Thu for max reach',
                'Use Stories on Instagram for 24h engagement',
                'Schedule bulk posts on weekends',
                'Space posts 24-48 hours apart'
            ],
            'next_recommended_posts': [
                {'type': 'Video Tutorial', 'topic': 'Social Media Growth', 'best_day': 'Wednesday'},
                {'type': 'Carousel', 'topic': 'Industry Tips', 'best_day': 'Tuesday'},
                {'type': 'Reel', 'topic': 'Behind-the-scenes', 'best_day': 'Friday'}
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(calendar), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def detect_anomalies(user_id):
    """Anomaly detection for performance trends"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        posts_sorted = sorted(posts, key=lambda x: x.get('post_date', ''))
        
        engagements = [p.get('likes', 0) + p.get('comments', 0) + p.get('shares', 0) for p in posts_sorted]
        avg_engagement = sum(engagements) / max(1, len(engagements))
        
        anomalies = []
        for i, engagement in enumerate(engagements):
            if engagement > avg_engagement * 2:
                anomalies.append({
                    'post_index': i,
                    'engagement': engagement,
                    'type': 'Spike - Viral content',
                    'reason': 'Exceptional performance',
                    'analysis': 'This post resonated with your audience'
                })
            elif engagement < avg_engagement * 0.3 and engagement > 0:
                anomalies.append({
                    'post_index': i,
                    'engagement': engagement,
                    'type': 'Dip - Below average',
                    'reason': 'Lower engagement than usual',
                    'analysis': 'Consider analyzing what made this post different'
                })
        
        return jsonify({
            'total_posts': len(posts),
            'average_engagement': round(avg_engagement, 2),
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies[:10],
            'trend': 'Upward' if engagements[-3:] and sum(engagements[-3:]) > avg_engagement * 3 else 'Stable',
            'insights': [
                f'Your best post got {max(engagements)} engagements',
                f'Consistency: Posts get {round(avg_engagement, 0)} engagements on average',
                'Performance is improving week-over-week'
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def forecast_growth(user_id, months=3):
    """Predictive analytics for growth forecasting"""
    try:
        posts = [p for p in posts_db.values() if p['user_id'] == user_id]
        accounts = [a for a in accounts_db.values() if a['user_id'] == user_id]
        
        current_followers = len(accounts) * 1000  # Mock: 1000 followers per account
        monthly_growth_rate = 0.15  # 15% monthly growth
        
        forecast = []
        for month in range(1, months + 1):
            projected_followers = int(current_followers * ((1 + monthly_growth_rate) ** month))
            forecast.append({
                'month': month,
                'projected_followers': projected_followers,
                'projected_engagement_rate': round(8.5 + (month * 0.5), 2),
                'projected_posts': len(posts) + (month * 4),
                'confidence': 'High' if month <= 2 else 'Medium'
            })
        
        return jsonify({
            'current_followers': current_followers,
            'forecast_period_months': months,
            'monthly_forecast': forecast,
            'growth_rate': f'{monthly_growth_rate * 100:.0f}%',
            'growth_drivers': [
                'Consistent posting schedule',
                'High-quality content',
                'Engagement with audience',
                'Strategic hashtag usage'
            ],
            'recommendations_for_growth': [
                'Collaborate with influencers in your niche',
                'Run contests and giveaways',
                'Create viral-worthy content',
                'Cross-promote on all platforms',
                'Engage authentically with followers'
            ],
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
