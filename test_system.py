"""
Test Script
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from user_model import UserModel
from recommendation_engine import PersonalizedNewsRecommender
import json
def print_header(text):
    print("\n" + "="*70)
    print(text)
    print("="*70 + "\n")

def test_user_model():
    """User Model"""
    print_header("User Model Test")
    # Create user
    user = UserModel('demo_user')
    print("Created user profile")
    # Set preferences
    user.update_preferences(
        followed_keywords=['technology', 'science'],
        avoided_keywords=['sports'],
        session_length='medium'
    )
    print("Set user preferences:")
    print(f"  - Followed: {user.profile['preferences']['followed_keywords']}")
    print(f"  - Avoided: {user.profile['preferences']['avoided_keywords']}")
    print(f"  - Session: {user.profile['preferences']['preferred_session_length']}")
    # Simulate interactions
    print("\nSimulating user interactions:")
    user.record_interaction(1, 'click')
    user.record_interaction(1, 'complete', reading_time=120)
    print("  - Clicked article 1, read for 120 seconds")
    user.record_interaction(5, 'save')
    print("  - Saved article 5")
    user.record_interaction(10, 'skip')
    print("  - Skipped article 10")
    # Get stats
    stats = user.get_interaction_stats()
    print("\nInteraction statistics:")
    print(f"  - Total: {stats['total_interactions']}")
    print(f"  - Clicks: {stats['clicks']}")
    print(f"  - Saves: {stats['saves']}")
    print(f"  - Skips: {stats['skips']}")
    print(f"  - Completion rate: {stats['completion_rate']:.1%}")
    return user

def test_recommendation_engine(user):
    """Recommendation Engine"""
    print_header("Recommendation Engine Test")
    # Create recommender
    recommender = PersonalizedNewsRecommender(user)
    print("Loaded articles and built TF-IDF index")
    # Generate recommendations
    print("\nGenerating personalized recommendations...")
    recommendations = recommender.generate_recommendations(num_recommendations=5)
    print("\nYOUR PERSONALIZED NEWS FEED:\n")
    for i, rec in enumerate(recommendations, 1):
        article = rec['article']
        scores = rec['score_breakdown']
        print(f"{i}. {article['title'][:65]}...")
        print(f"Source: {article['source']}")
        print(f"Keyword: {article['keyword']}")
        print(f"Why: {rec['explanation']}")
        print(f"Score: {rec['final_score']:.3f}")
        print(f"      (Keyword: {scores['keyword_score']:.2f}, "
              f"Recency: {scores['recency_score']:.2f}, "
              f"Diversity: {scores['diversity_score']:.2f}, "
              f"Source: {scores['source_score']:.2f})")
        print()
    return recommender

def test_personalized_search(recommender):
    """Test search with personalization"""
    print_header("Search with Personalization Test")
    query = "artificial intelligence"
    print(f"Searching for: '{query}'\n")
    results = recommender.search_with_personalization(query, top_k=5)
    print("SEARCH RESULTS (ranked by relevance + personalization):\n")
    for i, result in enumerate(results, 1):
        article = result['article']
        print(f"{i}. {article['title'][:65]}...")
        print(f"Source: {article['source']} | Keyword: {article['keyword']}")
        print(f"TF-IDF: {result['tfidf_score']:.3f} | "
              f"Personal: {result['personalization_score']:.3f} | "
              f"Combined: {result['combined_score']:.3f}")
        print(f"{result['explanation']}")
        print()

def test_learning():
    """Test learning from interactions"""
    print_header("Learning from Interaction Test")
    # Create new user
    user = UserModel('learning_test_user')
    user.update_preferences(
        followed_keywords=['technology'],
        session_length='medium'
    )
    # Load articles for interaction
    recommender = PersonalizedNewsRecommender(user)
    print("Initial keyword preference scores:")
    for keyword in ['technology', 'science', 'business', 'sports', 'health']:
        score = user.get_keyword_preference_score(keyword)
        print(f"  {keyword}: {score:.2f}")
    # Simulate interactions with science articles
    print("\nSimulating heavy engagement with 'science' articles...")
    for article in recommender.articles[:20]:
        if article.get('keyword') == 'science':
            user.record_interaction(article['id'], 'click')
            user.record_interaction(article['id'], 'save')
    # Simulate skipping sports
    print("Simulating skipping 'sports' articles...")
    for article in recommender.articles[:20]:
        if article.get('keyword') == 'sports':
            user.record_interaction(article['id'], 'skip')
    # Learn from interactions
    user.learn_from_interactions(recommender.articles)
    print("\nAfter learning, keyword preference scores:")
    for keyword in ['technology', 'science', 'business', 'sports', 'health']:
        score = user.get_keyword_preference_score(keyword)
        change = ""
        if keyword == 'science':
            change = " (increased!)"
        elif keyword == 'sports':
            change = " (decreased!)"
        print(f"  {keyword}: {score:.2f}{change}")

def test_different_scenarios():
    """Test different user scenarios"""
    print_header("Different User Scenarios Test")
    # Scenario 1: Tech enthusiast
    print("Scenario 1: Technology Enthusiast")
    print("-" * 50)
    user1 = UserModel('tech_enthusiast')
    user1.update_preferences(
        followed_keywords=['technology'],
        avoided_keywords=['sports', 'entertainment'],
        session_length='long'
    )
    recommender1 = PersonalizedNewsRecommender(user1)
    recs1 = recommender1.generate_recommendations(num_recommendations=3)
    print(f"Should get {user1.get_recommended_article_count()} articles (long session)")
    print("Top 3 recommendations:")
    for i, rec in enumerate(recs1[:3], 1):
        print(f"{i}. {rec['article']['title'][:60]}...")
        print(f"   Keyword: {rec['article']['keyword']} | Score: {rec['final_score']:.3f}")
    # Scenario 2: Balanced reader
    print("\n\nScenario 2: Balanced News Consumer")
    print("-" * 50)
    user2 = UserModel('balanced_reader')
    user2.update_preferences(
        followed_keywords=['technology', 'science', 'business', 'health'],
        avoided_keywords=[],
        session_length='short'
    )
    recommender2 = PersonalizedNewsRecommender(user2)
    recs2 = recommender2.generate_recommendations(num_recommendations=3)
    print(f"Should get {user2.get_recommended_article_count()} articles (short session)")
    print("Top 3 recommendations:")
    for i, rec in enumerate(recs2, 1):
        print(f"{i}. {rec['article']['title'][:60]}...")
        print(f"   Keyword: {rec['article']['keyword']} | Score: {rec['final_score']:.3f}")

def main():
    try:
        # Test 1: User Model
        user = test_user_model()
        # Test 2: Recommendation Engine
        recommender = test_recommendation_engine(user)
        # Test 3: Personalized Search
        test_personalized_search(recommender)
        # Test 4: Learning
        test_learning()
        # Test 5: Different Scenarios
        test_different_scenarios()
        print_header("ALL TESTS PASSED!")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)