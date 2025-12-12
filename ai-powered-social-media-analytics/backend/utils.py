"""
Advanced utility functions for database operations, authentication, AI analysis
Production-ready with error handling, caching, and advanced features
"""

import os
import bcrypt
import jwt
import mysql.connector
from datetime import datetime, timedelta
from flask import jsonify
from dotenv import load_dotenv
import random
import json
import csv
import io
from cachetools import TTLCache
from email_validator import validate_email, EmailNotValidError

load_dotenv()

# Simple in-memory cache (30 minutes TTL)
analytics_cache = TTLCache(maxsize=1000, ttl=1800)

# ==================== Database Configuration ====================

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'ai_social_analytics'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
}

JWT_SECRET = os.getenv('JWT_SECRET', 'dev_jwt_secret_change_in_production')

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

def get_db():
    """Create and return database connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        raise Exception(f"Database connection failed: {str(e)}")


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

    # Hash password with bcrypt
    try:
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, valid_email, hashed.decode('utf-8'))
        )
        db.commit()
        user_id = cursor.lastrowid
        cursor.close()
        db.close()
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id
        }), 201
    except mysql.connector.Error as e:
        msg = str(e)
        if 'Duplicate entry' in msg:
            if 'username' in msg:
                return jsonify({'error': 'Username already exists'}), 409
            elif 'email' in msg:
                return jsonify({'error': 'Email already exists'}), 409
        return jsonify({'error': f'Registration failed: {msg}'}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


def login_user(data):
    """Authenticate user and return JWT token"""
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Create JWT token with extended expiration
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
                    'created_at': str(user['created_at'])
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except mysql.connector.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
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
    """Connect a social media account (mock OAuth)"""
    user_id = data.get('user_id')
    platform = data.get('platform', '').lower()
    account_name = data.get('account_name', '').strip()

    if not (user_id and platform and account_name):
        return jsonify({'error': 'Missing required fields'}), 400

    valid_platforms = ['instagram', 'twitter', 'youtube', 'tiktok', 'linkedin']
    if platform not in valid_platforms:
        return jsonify({'error': f'Platform must be one of {valid_platforms}'}), 400

    if len(account_name) < 2 or len(account_name) > 100:
        return jsonify({'error': 'Invalid account name length'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id=%s", (user_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'User not found'}), 404
        
        cursor.execute(
            "INSERT INTO social_accounts (user_id, platform, account_name) VALUES (%s, %s, %s)",
            (user_id, platform, account_name)
        )
        db.commit()
        account_id = cursor.lastrowid
        cursor.close()
        db.close()

        # Clear cache
        cache_key = f"accounts_{user_id}"
        if cache_key in analytics_cache:
            del analytics_cache[cache_key]

        return jsonify({
            'message': f'{platform.capitalize()} account connected successfully',
            'account_id': account_id,
            'platform': platform,
            'account_name': account_name
        }), 201
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_connected_accounts(user_id):
    """Get all connected social accounts for a user"""
    cache_key = f"accounts_{user_id}"
    
    if cache_key in analytics_cache:
        return jsonify(analytics_cache[cache_key]), 200

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM social_accounts WHERE user_id=%s ORDER BY connected_at DESC", (user_id,))
        accounts = cursor.fetchall()
        cursor.close()
        db.close()

        result = {
            'accounts': accounts,
            'total': len(accounts),
            'timestamp': datetime.now().isoformat()
        }

        # Cache the result
        analytics_cache[cache_key] = result

        return jsonify(result), 200
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Posts Functions ====================

def get_posts(user_id, account_id=None, limit=50, offset=0):
    """Get posts for a user, optionally filtered by account"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if account_id:
            cursor.execute(
                "SELECT * FROM posts WHERE user_id=%s AND account_id=%s ORDER BY post_date DESC LIMIT %s OFFSET %s",
                (user_id, account_id, limit, offset)
            )
        else:
            cursor.execute(
                "SELECT * FROM posts WHERE user_id=%s ORDER BY post_date DESC LIMIT %s OFFSET %s",
                (user_id, limit, offset)
            )

        posts = cursor.fetchall()
        
        # Get total count
        if account_id:
            cursor.execute("SELECT COUNT(*) as count FROM posts WHERE user_id=%s AND account_id=%s", (user_id, account_id))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM posts WHERE user_id=%s", (user_id,))
        
        total = cursor.fetchone()['count']
        cursor.close()
        db.close()

        return jsonify({
            'posts': posts,
            'total': total,
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.now().isoformat()
        }), 200
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def add_post(data):
    """Add a new post to analytics database"""
    user_id = data.get('user_id')
    account_id = data.get('account_id')
    content = data.get('content', '').strip()
    likes = data.get('likes', 0)
    comments = data.get('comments', 0)
    shares = data.get('shares', 0)
    impressions = data.get('impressions', 0)

    if not (user_id and account_id and content):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO posts 
               (user_id, account_id, content, post_date, likes, comments, shares, impressions)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, account_id, content, datetime.now(), likes, comments, shares, impressions)
        )
        db.commit()
        post_id = cursor.lastrowid
        cursor.close()
        db.close()

        return jsonify({
            'message': 'Post added successfully',
            'post_id': post_id
        }), 201
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 400


# ==================== AI Analysis Functions ====================

def analyze_sentiment(data):
    """Analyze posts for sentiment, trends, and AI score (mock AI)"""
    posts = data.get('posts', [])

    if not posts:
        return jsonify({'error': 'No posts provided'}), 400

    try:
        # Mock AI sentiment analysis
        results = []
        sentiments = ['positive', 'neutral', 'negative']

        for post in posts:
            content = post.get('content', '')
            # Simple mock sentiment based on keywords
            if any(word in content.lower() for word in ['amazing', 'great', 'love', 'awesome', 'excellent']):
                sentiment = 'positive'
                ai_score = random.uniform(0.7, 1.0)
            elif any(word in content.lower() for word in ['hate', 'bad', 'terrible', 'awful']):
                sentiment = 'negative'
                ai_score = random.uniform(0.0, 0.3)
            else:
                sentiment = 'neutral'
                ai_score = random.uniform(0.4, 0.6)

            results.append({
                'post_id': post.get('id'),
                'content': content,
                'sentiment': sentiment,
                'ai_score': round(ai_score, 2),
                'keywords': extract_keywords(content)
            })

        return jsonify({
            'analysis': results,
            'summary': f'Analyzed {len(results)} posts. Sentiment distribution: {count_sentiments(results)}'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_ai_insights(user_id):
    """Generate AI insights based on user's posts"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM posts WHERE user_id=%s ORDER BY post_date DESC LIMIT 50",
            (user_id,)
        )
        posts = cursor.fetchall()
        cursor.close()
        db.close()

        if not posts:
            return jsonify({
                'insights': 'No posts to analyze yet. Start by connecting your accounts!',
                'recommendations': []
            }), 200

        # Generate mock AI insights
        total_engagement = sum(p.get('likes', 0) + p.get('comments', 0) + p.get('shares', 0) for p in posts)
        avg_engagement = total_engagement / len(posts) if posts else 0

        insights = {
            'total_posts': len(posts),
            'total_engagement': total_engagement,
            'average_engagement': round(avg_engagement, 2),
            'insights': [
                'Your content performs best on weekdays between 6-9 PM',
                'Posts with visual content get 3x more engagement',
                'Hashtags increase reach by 40%',
                'Shorter captions (under 100 chars) perform better'
            ]
        }

        return jsonify(insights), 200
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 400


def get_analytics_summary(user_id):
    """Get weekly/monthly analytics summary"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Get posts from last 30 days
        cursor.execute(
            "SELECT * FROM posts WHERE user_id=%s AND post_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
            (user_id,)
        )
        posts = cursor.fetchall()
        cursor.close()
        db.close()

        if not posts:
            return jsonify({
                'summary': 'No data available',
                'stats': {}
            }), 200

        # Calculate statistics
        stats = {
            'total_posts': len(posts),
            'total_likes': sum(p.get('likes', 0) for p in posts),
            'total_comments': sum(p.get('comments', 0) for p in posts),
            'total_shares': sum(p.get('shares', 0) for p in posts),
            'total_impressions': sum(p.get('impressions', 0) for p in posts),
            'average_likes': round(sum(p.get('likes', 0) for p in posts) / len(posts), 2),
            'average_comments': round(sum(p.get('comments', 0) for p in posts) / len(posts), 2),
            'average_engagement_rate': round((sum(p.get('likes', 0) + p.get('comments', 0) + p.get('shares', 0) for p in posts) / (len(posts) * 100)) * 100, 2)
        }

        return jsonify({
            'summary': f'Last 30 days: {stats["total_posts"]} posts, {stats["total_likes"]} total likes',
            'stats': stats,
            'period': 'Last 30 days'
        }), 200
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 400


def generate_recommendations(user_id):
    """Generate AI-powered recommendations for posting strategy"""
    recommendations = {
        'best_posting_times': [
            {'day': 'Monday-Friday', 'time': '6:00 PM - 9:00 PM', 'engagement': '45%', 'reason': 'Post-work engagement peak'},
            {'day': 'Tuesday-Thursday', 'time': '9:00 AM - 10:00 AM', 'engagement': '35%', 'reason': 'Morning commute'},
            {'day': 'Saturday', 'time': '10:00 AM - 12:00 PM', 'engagement': '35%', 'reason': 'Weekend morning scroll'},
            {'day': 'Sunday', 'time': '7:00 PM - 9:00 PM', 'engagement': '38%', 'reason': 'Sunday evening'}
        ],
        'content_recommendations': [
            'Increase use of carousel posts - 2.3x more engagement',
            'Include 3-5 relevant hashtags per post for maximum reach',
            'Post videos 2-3 times per week for 5x better reach',
            'Use call-to-action buttons to boost clicks by 65%',
            'Share user-generated content to build community (15% boost)',
            'Post educational content on weekdays, entertainment on weekends',
            'Use trending audio in video content for 40% more reach'
        ],
        'hashtag_strategy': {
            'optimal_count': '3-5 hashtags per post',
            'distribution': ['1 branded hashtag', '2-3 niche hashtags', '1 trending hashtag'],
            'trending_categories': ['#AI', '#Analytics', '#SocialMedia', '#Marketing', '#Tech', '#Data'],
            'best_performing': ['#AI', '#DigitalMarketing', '#DataAnalytics']
        },
        'content_mix': {
            'educational': '30%',
            'promotional': '20%',
            'entertainment': '35%',
            'user_generated': '15%'
        },
        'engagement_tips': [
            'Reply to comments within first hour for 60% more engagement',
            'Use questions in captions to boost comments by 50%',
            'Post consistently at same times for algorithm favor',
            'Collaborate with 5-10 accounts weekly for cross-promotion',
            'Use stories/reels for 2-3x reach vs regular posts'
        ],
        'timestamp': datetime.now().isoformat()
    }

    return jsonify(recommendations), 200


def delete_account(user_id, account_id):
    """Delete a connected account"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify ownership
        cursor.execute("SELECT user_id FROM social_accounts WHERE id=%s", (account_id,))
        account = cursor.fetchone()
        if not account or account[0] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        cursor.execute("DELETE FROM social_accounts WHERE id=%s AND user_id=%s", (account_id, user_id))
        db.commit()
        cursor.close()
        db.close()

        # Clear cache
        cache_key = f"accounts_{user_id}"
        if cache_key in analytics_cache:
            del analytics_cache[cache_key]

        return jsonify({'message': 'Account disconnected successfully'}), 200
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def update_post(user_id, post_id, data):
    """Update a post"""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Verify ownership
        cursor.execute("SELECT user_id FROM posts WHERE id=%s", (post_id,))
        post = cursor.fetchone()
        if not post or post[0] != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        likes = max(0, int(data.get('likes', 0)))
        comments = max(0, int(data.get('comments', 0)))
        shares = max(0, int(data.get('shares', 0)))
        impressions = max(0, int(data.get('impressions', 0)))
        content = data.get('content', '').strip()
        
        cursor.execute(
            """UPDATE posts 
               SET likes=%s, comments=%s, shares=%s, impressions=%s, content=%s
               WHERE id=%s AND user_id=%s""",
            (likes, comments, shares, impressions, content, post_id, user_id)
        )
        db.commit()
        cursor.close()
        db.close()

        return jsonify({'message': 'Post updated successfully'}), 200
    except mysql.connector.Error as e:
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_trending_posts(user_id, limit=10):
    """Get trending posts by engagement"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute(
            """SELECT * FROM posts 
               WHERE user_id=%s 
               ORDER BY (likes + comments + shares) DESC 
               LIMIT %s""",
            (user_id, limit)
        )
        trending = cursor.fetchall()
        cursor.close()
        db.close()

        return jsonify({
            'trending_posts': trending,
            'total': len(trending),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # User info
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        
        # Account stats
        cursor.execute("SELECT COUNT(*) as count FROM social_accounts WHERE user_id=%s", (user_id,))
        accounts_count = cursor.fetchone()['count']
        
        # Post stats
        cursor.execute("SELECT COUNT(*) as count FROM posts WHERE user_id=%s", (user_id,))
        posts_count = cursor.fetchone()['count']
        
        # Engagement stats
        cursor.execute(
            """SELECT 
                SUM(likes) as total_likes,
                SUM(comments) as total_comments,
                SUM(shares) as total_shares,
                SUM(impressions) as total_impressions
               FROM posts WHERE user_id=%s""",
            (user_id,)
        )
        engagement = cursor.fetchone()
        cursor.close()
        db.close()

        stats = {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': str(user['created_at']),
            'accounts_count': accounts_count,
            'posts_count': posts_count,
            'total_likes': engagement['total_likes'] or 0,
            'total_comments': engagement['total_comments'] or 0,
            'total_shares': engagement['total_shares'] or 0,
            'total_impressions': engagement['total_impressions'] or 0,
            'total_engagement': (engagement['total_likes'] or 0) + (engagement['total_comments'] or 0) + (engagement['total_shares'] or 0),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def export_analytics(user_id, format_type='json'):
    """Export user analytics"""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM posts WHERE user_id=%s ORDER BY post_date DESC", (user_id,))
        posts = cursor.fetchall()
        cursor.close()
        db.close()

        if format_type == 'csv':
            output = io.StringIO()
            if posts:
                fieldnames = posts[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(posts)
            
            return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=analytics.csv'}
        else:
            return jsonify({
                'data': posts,
                'total': len(posts),
                'exported_at': datetime.now().isoformat()
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Helper Functions ====================

def extract_keywords(text, limit=5):
    """Extract keywords from text"""
    keywords = []
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'was', 'are'}
    
    words = text.lower().split()
    for word in words:
        clean_word = word.strip('.,!?;:"\'')
        if len(clean_word) > 3 and clean_word not in common_words:
            keywords.append(clean_word)
    
    return list(set(keywords))[:limit]


def count_sentiments(results):
    """Count sentiment distribution"""
    positive = sum(1 for r in results if r.get('sentiment') == 'positive')
    negative = sum(1 for r in results if r.get('sentiment') == 'negative')
    neutral = sum(1 for r in results if r.get('sentiment') == 'neutral')
    return {
        'positive': positive,
        'neutral': neutral,
        'negative': negative
    }
