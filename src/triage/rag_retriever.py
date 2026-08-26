import os
from typing import Dict, List, Tuple
from src.data.loader import DataLoader

class KBRetriever:
    def __init__(self, loader: DataLoader = None):
        self.loader = loader or DataLoader()
        self.kb_docs = self.loader.get_knowledge_base_docs()
        self.filenames = list(self.kb_docs.keys())
        self.documents = list(self.kb_docs.values())
        self._init_vectorizer()

    def _init_vectorizer(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            self.vectorizer = TfidfVectorizer(stop_words='english')
            if self.documents:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
            else:
                self.tfidf_matrix = None
            self.cosine_similarity = cosine_similarity
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False

    def retrieve(self, query: str, top_k: int = 1) -> List[Tuple[str, float, str]]:
        """
        Retrieves top_k relevant KB articles for query.
        Returns list of (filename, similarity_score, document_content)
        """
        if not self.documents:
            return []

        if self.has_sklearn and self.tfidf_matrix is not None:
            query_vec = self.vectorizer.transform([query])
            scores = self.cosine_similarity(query_vec, self.tfidf_matrix)[0]
            indexed_scores = list(enumerate(scores))
            indexed_scores.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for idx, score in indexed_scores[:top_k]:
                fname = self.filenames[idx]
                content = self.documents[idx]
                results.append((fname, float(score), content))
            return results
        else:
            # Simple keyword matching fallback
            query_lower = query.lower()
            results = []
            for fname, content in self.kb_docs.items():
                match_count = sum(1 for word in query_lower.split() if word in content.lower())
                score = match_count / max(len(query_lower.split()), 1)
                results.append((fname, score, content))
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
