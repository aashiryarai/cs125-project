#combine index with personalization
import json
import os
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class PersonalizedNewsRecommender:
    def __init__(self, user_model, articles_path='articles.json'):
        self.user_model = user_model
        self.articles = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.load_articles(articles_path)
        self.build_tfidf_index()
    
    def load_articles(self, filepath):
        if not os.path.exists(filepath):
            print(f"No articles found at {filepath}")
            return []
        with open(filepath, 'r') as f:
            self.articles = json.load(f)
        print(f"Loaded {len(self.articles)} articles")
        return self.articles
    
    def build_tfidf_index(self):
        if not self.articles:
            return
        # combine title and description for better matching
        texts = [
            f"{article.get('title', '')} {article.get('description', '')}"
            for article in self.articles
        ]
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        print(f"Built TF-IDF index with {self.tfidf_matrix.shape[1]} features")
    
    def calculate_recency_score(self, article):
        try:
            published = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
            now = datetime.now(published.tzinfo)
            age_hours = (now - published).total_seconds() / 3600
            # full score for <6h, half score at 48h, minimal at 7 days
            if age_hours < 6:
                return 1.0
            elif age_hours < 48:
                return 0.8 - (age_hours - 6) * 0.3 / 42  # Linear decay to 0.5
            elif age_hours < 168:  # 7 days
                return 0.5 - (age_hours - 48) * 0.4 / 120  # Linear decay to 0.1
            else:
                return 0.1
        except:
            return 0.5  #default
    
    def calculate_diversity_penalty(self, article_idx, recent_article_indices):
        if not recent_article_indices or self.tfidf_matrix is None:
            return 1.0
        if article_idx >= self.tfidf_matrix.shape[0]:
            return 1.0
        #similarity to recent articles
        current_vec = self.tfidf_matrix[article_idx]
        max_similarity = 0.0
        for recent_idx in recent_article_indices:
            if recent_idx < self.tfidf_matrix.shape[0]:
                recent_vec = self.tfidf_matrix[recent_idx]
                similarity = cosine_similarity(current_vec, recent_vec)[0][0]
                max_similarity = max(max_similarity, similarity)
        # convert similarity to penalty
        if max_similarity > 0.8:
            return 0.3  #penalty for very similar content
        elif max_similarity > 0.6:
            return 0.6
        else:
            return 1.0
    
    def score_article(self, article, article_idx, recent_article_indices=None):
        if recent_article_indices is None:
            recent_article_indices = []
        # 1. keyword preference (0-1)
        keyword = article.get('keyword', 'general')
        keyword_score = self.user_model.get_keyword_preference_score(keyword)
        # 2. recency score (0-1)
        recency_score = self.calculate_recency_score(article)
        # 3. diversity penalty (0-1)
        diversity_score = self.calculate_diversity_penalty(article_idx, recent_article_indices)
        # 4. source score (if available)
        source = article.get('source', 'Unknown')
        source_score = self.user_model.profile['source_scores'].get(source, 0.0)
        source_score = (source_score + 1) / 2  # Convert from [-1,1] to [0,1]
        # weighted combination
        final_score = (
            0.35 * keyword_score +      # user interests most important
            0.30 * recency_score +       
            0.20 * diversity_score +    
            0.15 * source_score         
        )
        return {
            'final_score': final_score,
            'keyword_score': keyword_score,
            'recency_score': recency_score,
            'diversity_score': diversity_score,
            'source_score': source_score
        }
    
    def generate_recommendations(self, num_recommendations=None, recent_articles=None):
        if recent_articles is None:
            recent_articles = []
        if num_recommendations is None:
            num_recommendations = self.user_model.get_recommended_article_count()
        if not self.articles:
            print("No articles available for recommendation")
            return []
        # learn from past interactions
        self.user_model.learn_from_interactions(self.articles)
        # get indices of recent articles
        recent_indices = []
        if recent_articles:
            recent_ids = {a['id'] for a in recent_articles}
            recent_indices = [i for i, article in enumerate(self.articles) 
                            if article['id'] in recent_ids]
        # score all articles
        scored_articles = []
        for idx, article in enumerate(self.articles):
            scores = self.score_article(article, idx, recent_indices)
            scored_articles.append({
                'article': article,
                'index': idx,
                'scores': scores
            })
        # sort by final score
        scored_articles.sort(key=lambda x: x['scores']['final_score'], reverse=True)
        # get top recommendations
        recommendations = []
        for item in scored_articles[:num_recommendations]:
            article = item['article']
            scores = item['scores']
            # generate explanation
            explanation = self._generate_explanation(article, scores)
            recommendations.append({
                'article': article,
                'final_score': scores['final_score'],
                'explanation': explanation,
                'score_breakdown': scores
            })
        return recommendations
    
    def _generate_explanation(self, article, scores):
        #human-readable
        keyword = article.get('keyword', 'general')
        followed = keyword in self.user_model.profile['preferences']['followed_keywords']
        explanations = []
        # keyword match
        if followed and scores['keyword_score'] > 0.7:
            explanations.append(f"Matches your interest in {keyword}")
        elif scores['keyword_score'] > 0.6:
            explanations.append(f"Trending {keyword} topic")
        # recency
        if scores['recency_score'] > 0.8:
            explanations.append("Breaking news")
        elif scores['recency_score'] > 0.5:
            explanations.append("Recent update")
        # source
        source = article.get('source', 'Unknown')
        if scores['source_score'] > 0.6:
            explanations.append(f"From {source} (you engage with this source)")
        if not explanations:
            explanations.append("Diverse perspective")
        return " • ".join(explanations[:2])  # max 2
    
    def search_with_personalization(self, query, top_k=5):
        if self.tfidf_matrix is None:
            return []
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        scored_results = []
        for idx, article in enumerate(self.articles):
            tfidf_score = similarities[idx]
            # only relevant articles
            if tfidf_score < 0.01:
                continue
            scores = self.score_article(article, idx)
            combined_score = 0.7 * tfidf_score + 0.3 * scores['final_score']
            scored_results.append({
                'article': article,
                'tfidf_score': tfidf_score,
                'personalization_score': scores['final_score'],
                'combined_score': combined_score,
                'explanation': self._generate_explanation(article, scores)
            })
        scored_results.sort(key=lambda x: x['combined_score'], reverse=True)
        return scored_results[:top_k]

if __name__ == "__main__":
    # test
    from user_model import UserModel
    print("\n" + "="*60)
    print("Testing Enhanced Recommendation System")
    print("="*60 + "\n")
    user = UserModel('test_user')
    user.update_preferences(
        followed_keywords=['technology', 'science'],
        avoided_keywords=['sports'],
        session_length='medium'
    )
    recommender = PersonalizedNewsRecommender(user)
    print("\n1. Testing Personalized Feed:")
    print("-" * 60)
    recommendations = recommender.generate_recommendations(num_recommendations=5)
    for i, rec in enumerate(recommendations, 1):
        article = rec['article']
        print(f"\n{i}. {article['title'][:70]}...")
        print(f"   Source: {article['source']} | Keyword: {article['keyword']}")
        print(f"   Why: {rec['explanation']}")
        print(f"   Score: {rec['final_score']:.3f}")
    print("\n\n2. Testing Search with Personalization:")
    print("-" * 60)
    search_results = recommender.search_with_personalization("artificial intelligence", top_k=5)
    for i, result in enumerate(search_results, 1):
        article = result['article']
        print(f"\n{i}. {article['title'][:70]}...")
        print(f"   TF-IDF: {result['tfidf_score']:.3f} | Personal: {result['personalization_score']:.3f}")
        print(f"   Combined: {result['combined_score']:.3f}")
        print(f"   Why: {result['explanation']}")
    print("\n\n✓ Recommendation engine working correctly!")
    print("="*60 + "\n")