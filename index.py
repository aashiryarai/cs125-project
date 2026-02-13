import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class NewsIndexer:
    def __init__(self, json_path="articles.json"):
        self.articles = self.load_articles(json_path)
        
        # initializing td idf vectorizer
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = None
        
        self.build_index()

    # loads article data into memroy
    def load_articles(self, path):
        with open(path, "r") as f:
            return json.load(f)

    def build_index(self):
        texts = [
            article["title"] + " " + article["description"]
            for article in self.articles
        ]
        # converting text documents into tf idf vectors
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        print("tf idf index built successfully")

    # used cosine similarity
    def search(self, query, top_k=5):
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        ranked_indices = similarities.argsort()[::-1][:top_k]

        results = []

        # retrieving top ranked articles
        for index in ranked_indices:
            article = self.articles[index]
            
            results.append({
                "title": article["title"],
                "description": article["description"],
                "score": float(similarities[index])
            })

        return results
    
if __name__ == "__main__":
    indexer = NewsIndexer()
    results = indexer.search("AI technology", top_k=5)

    for r in results:
        print(r["title"], "| Score:", r["score"])