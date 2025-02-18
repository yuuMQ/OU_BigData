from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from unidecode import unidecode
from sentence_transformers import SentenceTransformer
import torch
def create_tfidf_model(documents):
    documents_normalized = [
        {"url": doc["url"],
         "title": unidecode(doc["title"]),
         "content": unidecode(doc["content"])}
        for doc in documents
    ]

    vectorizer_title = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    vectorizer_content = TfidfVectorizer(max_features=500, ngram_range=(1, 2))

    tfidf_matrix_title = vectorizer_title.fit_transform([doc["title"] for doc in documents_normalized])
    tfidf_matrix_content = vectorizer_content.fit_transform([doc["content"] for doc in documents_normalized])

    return tfidf_matrix_title, tfidf_matrix_content, vectorizer_title, vectorizer_content

# Tim kiem
def search_tfidf(query, vectorizer_title, vectorizer_content, tfidf_matrix_title, tfidf_matrix_content, documents):
    if not query.strip():
        return []

    query_normalized = unidecode(query)

    # Chuyen doi query thanh vector TF-IDF cho title va content
    query_vec_title = vectorizer_title.transform([query_normalized])
    query_vec_content = vectorizer_content.transform([query_normalized])

    # Cosine
    similarity_title = cosine_similarity(query_vec_title, tfidf_matrix_title)
    similarity_content = cosine_similarity(query_vec_content, tfidf_matrix_content)

    # Do tuong quan trung binh
    similarity = (similarity_title + similarity_content) / 2
    results = []
    for idx, score in enumerate(similarity[0]):
        if score > 0:
            url = documents[idx]["url"]
            results.append({
                "url": documents[idx]["url"],
                "title": documents[idx]["title"],
                "content": documents[idx]["content"],
                "score": score,
            })

    results = sorted(results, key=lambda d: d["score"], reverse=True)
    return results


def create_bert_model(documents, device='cpu'):
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2', device=device)
    documents_text = [doc["title"] + " " + doc["content"] for doc in documents]
    embeddings = model.encode(documents_text, convert_to_tensor=True, show_progress_bar=True, device=device)
    return embeddings, model

def search_bert(query, model, embeddings, documents, device='cpu'):
    query_vec = model.encode([query], convert_to_tensor=True, device=device)
    similarities = cosine_similarity(query_vec.cpu().numpy(), embeddings.cpu().numpy())
    results = []
    for idx, score in enumerate(similarities[0]):
        if score > 0:
            results.append({
                "url": documents[idx]["url"],
                "title": documents[idx]["title"],
                "content": documents[idx]["content"],
                "score": score,
            })
    results = sorted(results, key=lambda d: d["score"], reverse=True)
    return results

def search_combined(query,
                    vectorizer_title, vectorizer_content, tfidf_matrix_title, tfidf_matrix_content,
                    model, embeddings, documents,
                    tfidf_weight=0.6, bert_weight=0.4,
                    device='cpu'
                    ):
    results_tfidf = search_tfidf(query, vectorizer_title, vectorizer_content,
                                 tfidf_matrix_title, tfidf_matrix_content, documents)
    results_bert = search_bert(query, model, embeddings, documents, device=device)

    combined_results = {}
    # Thêm kết quả tfidf
    for result in results_tfidf:
        result["score"] *= tfidf_weight
        if result["url"] not in combined_results:
            combined_results[result["url"]] = result
        else:
            combined_results[result["url"]]["score"] = max(combined_results[result["url"]]["score"], result["score"])

    # Thêm kết quả BERT vào
    for result in results_bert:
        result["score"] *= bert_weight
        if result["url"] not in combined_results:
            combined_results[result["url"]] = result
        else:
            combined_results[result["url"]]["score"] = max(combined_results[result["url"]]["score"], result["score"])

    unique_results = sorted(combined_results.values(), key=lambda d: d["score"], reverse=True)

    if device == 'cuda':
        torch.cuda.empty_cache()

    return unique_results
