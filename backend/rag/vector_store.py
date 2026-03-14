from typing import List, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embeddings(text_chunks: List[str]) -> np.ndarray:
    """
    Create local embeddings using SentenceTransformers.
    """
    embeddings = embedding_model.encode(text_chunks)
    return np.array(embeddings, dtype="float32")


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.
    """
    return embedding_model.encode([query])[0].tolist()


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    """
    Build an in-memory FAISS index from embeddings.
    """
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index


class VectorStore:
    """
    Simple wrapper around FAISS index and original text chunks.
    """

    def __init__(self, chunks: List[str]):
        self.chunks = chunks
        self.embeddings = create_embeddings(chunks)
        self.index = build_faiss_index(self.embeddings)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        query = np.array([query_embedding], dtype="float32")
        distances, indices = self.index.search(query, top_k)
        results: List[Tuple[str, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.chunks[idx], float(dist)))
        return results
