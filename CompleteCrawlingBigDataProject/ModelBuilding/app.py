import torch
from flask import Flask, request, jsonify, render_template
from Get_data import get_data_from_es
from Model import create_tfidf_model, create_bert_model, search_combined
app = Flask(__name__)

device = 'cuda' if torch.cuda.is_available() else 'cpu'

documents = get_data_from_es()
tfidf_matrix_title, tfidf_matrix_content, vectorizer_title, vectorizer_content = create_tfidf_model(documents)
embedding, model = create_bert_model(documents, device=device)
@app.route("/")
def home():
    return render_template("Ou_tool.html")

@app.route('/search', methods=['GET'])
def search_api():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No query provided"}), 400

    combined_results = search_combined(
        query,
        vectorizer_title, vectorizer_content, tfidf_matrix_title, tfidf_matrix_content,
        model, embedding, documents,
        device=device
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template("search_results.html", results=combined_results)

    return render_template("Ou_tool.html", results=combined_results)

if __name__ == '__main__':
    app.run(debug=True)