from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import uuid
import os
import io
import openai
import pdfplumber
import docx
import faiss
import numpy as np

app = Flask(__name__)
CORS(app)

CHAPTER_DIR = os.path.join(os.path.dirname(__file__), 'chapters')
EMBED_INDEX_PATH = os.path.join(os.path.dirname(__file__), 'embeddings.index')
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')

os.makedirs(CHAPTER_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

# simple faiss index - in memory for POC
if os.path.exists(EMBED_INDEX_PATH):
    index = faiss.read_index(EMBED_INDEX_PATH)
    ids = []
    with open(EMBED_INDEX_PATH + '.ids', 'r') as f:
        ids = [line.strip() for line in f]
else:
    index = faiss.IndexFlatL2(1536)
    ids = []


def embed_text(text: str):
    response = openai.Embedding.create(input=[text], model="text-embedding-ada-002")
    return np.array(response['data'][0]['embedding'], dtype='float32')


def save_index():
    faiss.write_index(index, EMBED_INDEX_PATH)
    with open(EMBED_INDEX_PATH + '.ids', 'w') as f:
        for i in ids:
            f.write(i + '\n')


def extract_text(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        text = ''
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + '\n'
        return text
    else:
        doc = docx.Document(file_path)
        return '\n'.join([p.text for p in doc.paragraphs])


@app.route('/api/chapters', methods=['POST'])
def upload_chapter():
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({'error': 'no file'}), 400

    chapter_id = str(uuid.uuid4())
    save_path = os.path.join(CHAPTER_DIR, chapter_id + '_' + uploaded.filename)
    uploaded.save(save_path)

    text = extract_text(save_path)

    chunk_size = 800
    tokens = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    for t in tokens:
        vec = embed_text(t)
        index.add(np.array([vec]))
        ids.append(chapter_id)

    save_index()
    text_path = save_path + '.txt'
    with open(text_path, 'w') as f:
        f.write(text)

    return jsonify({'chapter_id': chapter_id})


@app.route('/api/lesson', methods=['POST'])
def start_lesson():
    data = request.get_json()
    chapter_id = data.get('chapter_id')
    prompt = data.get('optional_prompt', '')
    if not chapter_id:
        return jsonify({'error': 'missing chapter_id'}), 400

    # gather text for chapter
    chapter_files = [f for f in os.listdir(CHAPTER_DIR) if f.startswith(chapter_id) and f.endswith('.txt')]
    if not chapter_files:
        return jsonify({'error': 'chapter not found'}), 404
    with open(os.path.join(CHAPTER_DIR, chapter_files[0]), 'r') as f:
        text = f.read()

    system_msg = "You are a helpful tutor. Narrate the following lesson:"
    user_msg = prompt + '\n' + text
    chat = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=[{'role':'system','content':system_msg}, {'role':'user','content':user_msg}])
    narration = chat['choices'][0]['message']['content']

    speech = openai.Audio.speech.create(model='tts-1', voice='alloy', input=narration)
    audio_content = speech.content
    audio_path = os.path.join(STORAGE_DIR, chapter_id + '.wav')
    with open(audio_path, 'wb') as f:
        f.write(audio_content)

    return send_file(audio_path, mimetype='audio/wav')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error': 'no messages'}), 400

    def generate():
        response = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages, stream=True)
        for chunk in response:
            if 'choices' in chunk and chunk['choices'][0].get('delta', {}).get('content'):
                yield f"data: {chunk['choices'][0]['delta']['content']}\n\n"
        yield "data: [DONE]\n\n"

    return app.response_class(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
