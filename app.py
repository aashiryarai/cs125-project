"""
Flask web app for the Personal News Feed - CS125 Final Demo
"""
from flask import Flask, render_template, request, jsonify
from user_model import UserModel
from recommendation_engine import PersonalizedNewsRecommender

app = Flask(__name__)

# Default user for the demo
USER_ID = 'demo_user'
user = UserModel(USER_ID)
recommender = PersonalizedNewsRecommender(user, 'articles.json')


@app.route('/')
def index():
    """Main feed page with personalized recommendations"""
    try:
        recommendations = recommender.generate_recommendations()
        user_prefs = user.profile['preferences']
        
        return render_template('index.html',
                             recommendations=recommendations,
                             user_prefs=user_prefs)
    except Exception as e:
        return f"Error loading feed: {str(e)}<br><a href='/'>Retry</a>", 500


@app.route('/preferences')
def preferences_page():
    """Preferences configuration page"""
    try:
        user_prefs = user.profile['preferences']
        return render_template('preferences.html',
                             user_prefs=user_prefs)
    except Exception as e:
        return f"Error loading preferences: {str(e)}<br><a href='/'>Back to Feed</a>", 500


@app.route('/search')
def search_page():
    """Search results page"""
    try:
        query = request.args.get('q', '').strip()
        results = []
        
        if query:
            results = recommender.search_with_personalization(query, top_k=10)
        
        return render_template('search.html',
                             query=query,
                             results=results)
    except Exception as e:
        return f"Search error: {str(e)}<br><a href='/'>Back to Feed</a>", 500


@app.route('/api/recommendations')
def get_recommendations():
    """API endpoint for recommendations"""
    try:
        count = request.args.get('count', 10, type=int)
        recs = recommender.generate_recommendations(num_recommendations=min(count, 20))
        return jsonify([{
            'article': r['article'],
            'explanation': r['explanation'],
            'score': r['final_score']
        } for r in recs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preferences', methods=['GET', 'POST'])
def api_preferences():
    """API endpoint for preferences"""
    global user, recommender
    
    if request.method == 'GET':
        return jsonify(user.profile['preferences'])
    
    try:
        data = request.get_json() or {}
        user.update_preferences(
            followed_keywords=data.get('followed_keywords'),
            avoided_keywords=data.get('avoided_keywords'),
            session_length=data.get('session_length')
        )
        # Rebuild recommender with new preferences
        recommender = PersonalizedNewsRecommender(user, 'data/articles.json')
        return jsonify({'success': True, 'preferences': user.profile['preferences']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interact', methods=['POST'])
def record_interaction():
    """Record user interaction (click, save, skip)"""
    try:
        data = request.get_json() or {}
        article_id = data.get('article_id')
        action = data.get('action', 'click')
        reading_time = data.get('reading_time')
        
        if article_id is not None and action:
            user.record_interaction(article_id, action, reading_time=reading_time)
            return jsonify({'success': True})
        
        return jsonify({'error': 'article_id and action required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 CS125 PERSONAL NEWS FEED - FINAL DEMO")
    print("="*70)
    print("\n📊 System Status:")
    print(f"   Articles loaded: {len(recommender.articles)}")
    print(f"   User: {user.user_id}")
    print(f"   Preferences: {user.profile['preferences']['followed_keywords']}")
    print("\n🌐 Server starting at: http://localhost:5000")
    print("⚠️  Press CTRL+C to stop\n")
    print("="*70 + "\n")
    
    app.run(debug=True, port=5001, host='127.0.0.1')