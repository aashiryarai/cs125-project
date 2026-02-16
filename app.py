"""
Flask web app for the Personal News Feed
"""
from flask import Flask, render_template, request, jsonify
from user_model import UserModel
from recommendation_engine import PersonalizedNewsRecommender

app = Flask(__name__)

# Default user for the demo
USER_ID = 'web_user'
user = UserModel(USER_ID)
recommender = PersonalizedNewsRecommender(user)


@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')


@app.route('/api/recommendations')
def get_recommendations():
    """Get personalized news recommendations"""
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


@app.route('/api/search')
def search():
    """Search articles with personalization"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    try:
        results = recommender.search_with_personalization(query, top_k=15)
        return jsonify([{
            'article': r['article'],
            'explanation': r['explanation'],
            'tfidf_score': r['tfidf_score'],
            'combined_score': r['combined_score']
        } for r in results])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preferences', methods=['GET', 'POST'])
def preferences():
    """Get or update user preferences"""
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
        recommender = PersonalizedNewsRecommender(user)
        return jsonify({'success': True, 'preferences': user.profile['preferences']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interaction', methods=['POST'])
def record_interaction():
    """Record user interaction (click, save, skip, complete)"""
    try:
        data = request.get_json() or {}
        article_id = data.get('article_id', type=int)
        action = data.get('action', 'click')
        reading_time = data.get('reading_time')
        if article_id and action:
            user.record_interaction(article_id, action, reading_time=reading_time)
            return jsonify({'success': True})
        return jsonify({'error': 'article_id and action required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
