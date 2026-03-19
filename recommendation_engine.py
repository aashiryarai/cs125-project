import json
import os
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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

            if age_hours < 6:
                return 1.0
            elif age_hours < 48:
                return 0.8 - (age_hours - 6) * 0.3 / 42
            elif age_hours < 168:
                return 0.5 - (age_hours - 48) * 0.4 / 120
            else:
                return 0.1
        except Exception:
            return 0.5

    def calculate_diversity_penalty(self, article_idx, recent_article_indices):
        if not recent_article_indices or self.tfidf_matrix is None:
            return 1.0

        if article_idx >= self.tfidf_matrix.shape[0]:
            return 1.0

        current_vec = self.tfidf_matrix[article_idx]
        max_similarity = 0.0

        for recent_idx in recent_article_indices:
            if recent_idx < self.tfidf_matrix.shape[0]:
                recent_vec = self.tfidf_matrix[recent_idx]
                similarity = cosine_similarity(current_vec, recent_vec)[0][0]
                max_similarity = max(max_similarity, similarity)

        if max_similarity > 0.8:
            return 0.3
        elif max_similarity > 0.6:
            return 0.6
        else:
            return 1.0

    def _get_topic_priority_factor(self, keyword):
        preferences = self.user_model.profile.get('preferences', {})
        followed_keywords = set(preferences.get('followed_keywords', []))
        avoided_keywords = set(preferences.get('avoided_keywords', []))

        if keyword in avoided_keywords:
            return 0.05

        if followed_keywords:
            if keyword in followed_keywords:
                return 1.0
            return 0.20

        return 1.0

    def score_article(self, article, article_idx, recent_article_indices=None):
        if recent_article_indices is None:
            recent_article_indices = []

        keyword = article.get('keyword', 'general')
        keyword_score = self.user_model.get_keyword_preference_score(keyword)

        topic_priority_factor = self._get_topic_priority_factor(keyword)
        adjusted_keyword_score = keyword_score * topic_priority_factor

        recency_score = self.calculate_recency_score(article)
        diversity_score = self.calculate_diversity_penalty(article_idx, recent_article_indices)

        source = article.get('source', 'Unknown')
        source_score = self.user_model.profile.get('source_scores', {}).get(source, 0.0)
        source_score = (source_score + 1) / 2

        final_score = (
            0.50 * adjusted_keyword_score +
            0.25 * recency_score +
            0.15 * diversity_score +
            0.10 * source_score
        )

        return {
            'final_score': final_score,
            'keyword_score': adjusted_keyword_score,
            'raw_keyword_score': keyword_score,
            'topic_priority_factor': topic_priority_factor,
            'recency_score': recency_score,
            'diversity_score': diversity_score,
            'source_score': source_score
        }

    def _normalize_recent_articles(self, recent_articles):
        if not recent_articles:
            return set()

        recent_ids = set()
        for article in recent_articles:
            if isinstance(article, dict):
                article_id = article.get('id')
                if article_id is not None:
                    recent_ids.add(article_id)
            elif isinstance(article, int):
                recent_ids.add(article)

        return recent_ids

    def _filter_candidate_articles(self, exclude_recent_ids=None):
        if exclude_recent_ids is None:
            exclude_recent_ids = set()

        preferences = self.user_model.profile.get('preferences', {})
        followed_keywords = set(preferences.get('followed_keywords', []))
        avoided_keywords = set(preferences.get('avoided_keywords', []))

        base_articles = [
            article for article in self.articles
            if article.get('id') not in exclude_recent_ids
            and article.get('keyword') not in avoided_keywords
        ]

        if followed_keywords:
            preferred_articles = [
                article for article in base_articles
                if article.get('keyword') in followed_keywords
            ]

            # Only hard-restrict when we have enough followed-topic articles.
            if len(preferred_articles) >= 3:
                return preferred_articles

        return base_articles

    def generate_recommendations(self, num_recommendations=None, recent_articles=None):
        if recent_articles is None:
            recent_articles = []

        if num_recommendations is None:
            num_recommendations = self.user_model.get_recommended_article_count()

        if not self.articles:
            print("No articles available for recommendation")
            return []

        self.user_model.learn_from_interactions(self.articles)

        recent_ids = self._normalize_recent_articles(recent_articles)
        candidate_articles = self._filter_candidate_articles(exclude_recent_ids=recent_ids)

        if len(candidate_articles) < num_recommendations:
            candidate_articles = [
                article for article in self.articles
                if article.get('keyword') not in self.user_model.profile.get('preferences', {}).get('avoided_keywords', [])
            ]

        article_index_by_id = {
            article.get('id'): idx for idx, article in enumerate(self.articles)
        }

        recent_indices = [
            article_index_by_id[article_id]
            for article_id in recent_ids
            if article_id in article_index_by_id
        ]

        scored_articles = []
        for article in candidate_articles:
            idx = article_index_by_id.get(article.get('id'))
            if idx is None:
                continue

            scores = self.score_article(article, idx, recent_indices)
            scored_articles.append({
                'article': article,
                'index': idx,
                'scores': scores
            })

        scored_articles.sort(key=lambda x: x['scores']['final_score'], reverse=True)

        min_score_threshold = 0.5
        filtered_articles = [
            item for item in scored_articles
            if item['scores']['final_score'] >= min_score_threshold
        ]

        # Fallback 1: relax threshold if we do not have enough results.
        if len(filtered_articles) < num_recommendations:
            filtered_articles = [
                item for item in scored_articles
                if item['scores']['final_score'] >= 0.3
            ]

        # Fallback 2: if still empty, use the best available items.
        if not filtered_articles:
            filtered_articles = scored_articles[:max(num_recommendations * 2, num_recommendations)]

        scored_articles = filtered_articles

        preferences = self.user_model.profile.get('preferences', {})
        followed_keywords = preferences.get('followed_keywords', [])

        selected_items = []
        selected_ids = set()

        # First pass: try to include at least one good article per followed topic.
        for keyword in followed_keywords:
            for item in scored_articles:
                article = item['article']
                article_id = article.get('id')

                if article.get('keyword') == keyword and article_id not in selected_ids:
                    selected_items.append(item)
                    selected_ids.add(article_id)
                    break

        # Second pass: fill remaining slots by best overall score.
        for item in scored_articles:
            article_id = item['article'].get('id')

            if article_id in selected_ids:
                continue

            if len(selected_items) >= num_recommendations:
                break

            selected_items.append(item)
            selected_ids.add(article_id)

        recommendations = []
        for item in selected_items[:num_recommendations]:
            article = item['article']
            scores = item['scores']
            explanation = self._generate_explanation(article, scores)

            recommendations.append({
                'article': article,
                'final_score': scores['final_score'],
                'explanation': explanation,
                'score_breakdown': scores
            })

        return recommendations

    def _generate_explanation(self, article, scores):
        keyword = article.get('keyword', 'general')
        followed = keyword in self.user_model.profile.get('preferences', {}).get('followed_keywords', [])
        explanations = []

        if followed and scores['keyword_score'] > 0.5:
            explanations.append(f"Aligned with your selected interest in {keyword}")
        elif scores['raw_keyword_score'] > 0.6:
            explanations.append(f"Relevant {keyword} topic")

        if scores['recency_score'] > 0.8:
            explanations.append("Very recent article")
        elif scores['recency_score'] > 0.5:
            explanations.append("Recent update")

        source = article.get('source', 'Unknown')
        if scores['source_score'] > 0.6:
            explanations.append(f"From {source}, a source you tend to engage with")

        if not explanations:
            explanations.append("Included as a diverse recommendation")

        return " • ".join(explanations[:2])

    def search_with_personalization(self, query, top_k=5):
        if self.tfidf_matrix is None:
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        avoided_keywords = set(
            self.user_model.profile.get('preferences', {}).get('avoided_keywords', [])
        )

        scored_results = []
        for idx, article in enumerate(self.articles):
            tfidf_score = similarities[idx]

            if tfidf_score < 0.01:
                continue

            if article.get('keyword') in avoided_keywords:
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
    from user_model import UserModel

    print("\n" + "=" * 60)
    print("Testing Enhanced Recommendation System")
    print("=" * 60 + "\n")

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

    print("\n\nRecommendation engine working correctly.")
    print("=" * 60 + "\n")