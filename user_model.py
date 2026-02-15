#user model for personalization
import json
import os
from datetime import datetime
from collections import defaultdict

class UserModel:
    def __init__(self, user_id='default_user'):
        self.user_id = user_id
        self.profile_path = f'data/users/{user_id}.json'
        self.profile = self._load_or_create_profile()
    
    def _load_or_create_profile(self):
        """Load existing profile or create new one"""
        if os.path.exists(self.profile_path):
            with open(self.profile_path, 'r') as f:
                profile = json.load(f)
                if 'topic_scores' not in profile or not isinstance(profile.get('topic_scores'), dict):
                    profile['topic_scores'] = {}
                if 'source_scores' not in profile or not isinstance(profile.get('source_scores'), dict):
                    profile['source_scores'] = {}
                return profile
        else:
            #default profile structure
            return {
                'user_id': self.user_id,
                'preferences': {
                    'followed_keywords': ['technology', 'science'],  # Match your keywords
                    'avoided_keywords': [],
                    'preferred_session_length': 'medium',  # short, medium, long
                    'preferred_article_depth': 'mixed'
                },
                'interaction_history': [],
                'topic_scores': {},  # Learned keyword preferences
                'source_scores': {},  # Source credibility
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
    
    def save_profile(self):
        #save user profile
        os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
        self.profile['last_updated'] = datetime.now().isoformat()
        with open(self.profile_path, 'w') as f:
            json.dump(self.profile, f, indent=2)
    
    def update_preferences(self, followed_keywords=None, avoided_keywords=None, 
                          session_length=None, article_depth=None):
       #update user preferences
        if followed_keywords is not None:
            self.profile['preferences']['followed_keywords'] = followed_keywords
        if avoided_keywords is not None:
            self.profile['preferences']['avoided_keywords'] = avoided_keywords
        if session_length is not None:
            self.profile['preferences']['preferred_session_length'] = session_length
        if article_depth is not None:
            self.profile['preferences']['preferred_article_depth'] = article_depth
        self.save_profile()
    
    def record_interaction(self, article_id, interaction_type, reading_time=None):
        #interaction types: click, save, skip, complete
        #record user interaction
        interaction = {
            'article_id': article_id,
            'type': interaction_type,
            'timestamp': datetime.now().isoformat(),
            'reading_time': reading_time
        }
        self.profile['interaction_history'].append(interaction)
        #keep last 100 interactions
        if len(self.profile['interaction_history']) > 100:
            self.profile['interaction_history'] = self.profile['interaction_history'][-100:]
        self.save_profile()
    
    def get_interaction_stats(self):
        #stats about user interactions
        interactions = self.profile['interaction_history']
        stats = {
            'total_interactions': len(interactions),
            'clicks': sum(1 for i in interactions if i['type'] == 'click'),
            'saves': sum(1 for i in interactions if i['type'] == 'save'),
            'skips': sum(1 for i in interactions if i['type'] == 'skip'),
            'completes': sum(1 for i in interactions if i['type'] == 'complete')
        }
        if stats['clicks'] > 0:
            stats['completion_rate'] = stats['completes'] / stats['clicks']
        else:
            stats['completion_rate'] = 0.0
        return stats
    
    def learn_from_interactions(self, articles):
        #update topic scores
        keyword_engagement = defaultdict(lambda: {'positive': 0, 'negative': 0})
        source_engagement = defaultdict(lambda: {'positive': 0, 'negative': 0})
        # create article lookup by ID
        article_lookup = {a['id']: a for a in articles}
        for interaction in self.profile['interaction_history'][-50:]:  # Recent 50
            article_id = interaction['article_id']
            interaction_type = interaction['type']
            if article_id not in article_lookup:
                continue
            article = article_lookup[article_id]
            keyword = article.get('keyword', 'general')
            source = article.get('source', 'Unknown')
            # positive signal
            if interaction_type in ['click', 'save', 'complete']:
                weight = 2.0 if interaction_type == 'save' else 1.0
                keyword_engagement[keyword]['positive'] += weight
                source_engagement[source]['positive'] += weight
            # negative signal
            elif interaction_type == 'skip':
                keyword_engagement[keyword]['negative'] += 1.0
                source_engagement[source]['negative'] += 0.5
        # calculate score
        for keyword, counts in keyword_engagement.items():
            total = counts['positive'] + counts['negative']
            if total > 0:
                score = (counts['positive'] - counts['negative']) / total
                self.profile['topic_scores'][keyword] = score
        for source, counts in source_engagement.items():
            total = counts['positive'] + counts['negative']
            if total > 0:
                score = (counts['positive'] - counts['negative']) / total
                self.profile['source_scores'][source] = score
        self.save_profile()
    
    def get_keyword_preference_score(self, keyword):
        # combine explicit and learned preferences
        if keyword in self.profile['preferences']['avoided_keywords']:
            return 0.0
        base_score = 0.5
        if keyword in self.profile['preferences']['followed_keywords']:
            base_score = 0.8
        #learned score
        learned_score = self.profile['topic_scores'].get(keyword, 0.0)
        # weighted combination
        final_score = 0.6 * base_score + 0.4 * (0.5 + learned_score / 2)
        return max(0.0, min(1.0, final_score))
    
    def get_recommended_article_count(self):
        #get recommeded number of articles
        length_map = {
            'short': 3,
            'medium': 5,
            'long': 8
        }
        return length_map.get(self.profile['preferences']['preferred_session_length'], 5)

if __name__ == "__main__":
    #test user model
    user = UserModel('test_user')
    print("User profile created:")
    print(json.dumps(user.profile, indent=2))
    # simulate some interactions
    user.record_interaction(1, 'click')
    user.record_interaction(1, 'complete', reading_time=120)
    user.record_interaction(2, 'skip')
    print("\n Interaction stats:")
    print(json.dumps(user.get_interaction_stats(), indent=2))
    
    print("\n User model working correctly!")
