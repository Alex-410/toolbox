from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework import status
import os
import json
import re
import requests
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

RAG_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rag_data')
os.makedirs(RAG_DATA_DIR, exist_ok=True)

FAISS_INDEX_FILE = os.path.join(RAG_DATA_DIR, 'faiss_index')
DOCS_FILE = os.path.join(RAG_DATA_DIR, 'documents.json')
CHAT_HISTORY_FILE = os.path.join(RAG_DATA_DIR, 'chat_history.json')

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'qwen3-embedding:0.6b')
RERANK_MODEL = os.getenv('RERANK_MODEL', 'qwen3-reranker:0.6b')
LLM_API_KEY = os.getenv('LLM_API_KEY', '')
LLM_MODEL = os.getenv('LLM_MODEL', 'deepseek-chat')
LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com')

faiss_index = None
documents = []


def get_embeddings(texts):
    url = f'{OLLAMA_BASE_URL}/api/embed'
    vectors = []
    for text in texts:
        try:
            resp = requests.post(url, json={'model': EMBEDDING_MODEL, 'input': text}, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if 'embedding' in result:
                vectors.append(result['embedding'])
            elif 'embeddings' in result:
                vectors.append(result['embeddings'][0])
            else:
                raise Exception(f'Ollama响应缺少embedding字段: {result}')
        except requests.exceptions.RequestException as e:
            raise Exception(f'连接Ollama失败: {str(e)}')
        except (KeyError, ValueError, IndexError) as e:
            raise Exception(f'Ollama响应格式错误: {str(e)}')
    return vectors


def rerank(query, documents_list, top_k=3):
    if not RERANK_MODEL:
        return documents_list[:top_k]
    
    url = f'{OLLAMA_BASE_URL}/api/rerank'
    try:
        resp = requests.post(url, json={
            'model': RERANK_MODEL,
            'query': query,
            'documents': documents_list,
            'top_n': top_k
        }, timeout=60)
        result = resp.json()
        return [documents_list[i] for i in result.get('results', [])]
    except Exception:
        return documents_list[:top_k]


def chunk_text(text, strategy='fixed', chunk_size=500, overlap=50):
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    
    if strategy == 'fixed':
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            if overlap <= 0:
                start = end
            else:
                start = start + chunk_size - overlap
            if start >= len(text):
                break
            if start <= 0 and overlap > 0:
                break
        return chunks
    
    elif strategy == 'recursive':
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ''
        
        for para in paragraphs:
            if not para.strip():
                continue
                
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk += ('\n\n' if current_chunk else '') + para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                if len(para) > chunk_size:
                    sub_chunks = []
                    for i in range(0, len(para), chunk_size - overlap):
                        sub_chunk = para[i:i + chunk_size]
                        sub_chunks.append(sub_chunk)
                    if sub_chunks:
                        current_chunk = sub_chunks[-1]
                        chunks.extend(sub_chunks[:-1])
                else:
                    current_chunk = para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    return [text]


def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ''
    
    if ext in ['.txt', '.md']:
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if not text:
            return '', '无法解码文件，请确保文件是UTF-8编码'
    
    elif ext == '.pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + '\n'
        except Exception as e:
            return '', str(e)
    
    return text, None


@csrf_exempt
@api_view(['POST'])
def upload_document(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': '请上传文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    ext = os.path.splitext(file.name)[1].lower()
    
    if ext not in ['.txt', '.md', '.pdf']:
        return JsonResponse({'error': '不支持的文件类型，仅支持 TXT/MD/PDF'}, status=status.HTTP_400_BAD_REQUEST)
    
    strategy = request.data.get('strategy', 'fixed')
    chunk_size = int(request.data.get('chunk_size', 500))
    overlap = int(request.data.get('overlap', 50))
    
    temp_path = os.path.join(RAG_DATA_DIR, file.name)
    with open(temp_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)
    
    text, error = extract_text_from_file(temp_path)
    if error:
        os.remove(temp_path)
        return JsonResponse({'error': f'解析文件失败: {error}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    os.remove(temp_path)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    
    chunks = chunk_text(text, strategy, chunk_size, overlap)
    
    preview_chunks = [{'index': i, 'content': chunk, 'selected': True} for i, chunk in enumerate(chunks)]
    
    return JsonResponse({
        'preview': True,
        'filename': file.name,
        'chunks': preview_chunks,
        'strategy': strategy
    })


@csrf_exempt
@api_view(['POST'])
def save_chunks(request):
    data = request.data
    filename = data.get('filename', '')
    strategy = data.get('strategy', 'fixed')
    selected_chunks = data.get('selected_chunks', [])
    
    if not selected_chunks:
        return JsonResponse({'error': '请至少选择一个切片'}, status=status.HTTP_400_BAD_REQUEST)
    
    global faiss_index, documents
    
    try:
        vectors = get_embeddings(selected_chunks)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    import numpy as np
    vectors = np.array(vectors).astype('float32')
    
    if faiss_index is None:
        import faiss
        dim = vectors.shape[1]
        faiss_index = faiss.IndexFlatL2(dim)
    
    faiss_index.add(vectors)
    
    doc_id = len(documents)
    for i, chunk in enumerate(selected_chunks):
        documents.append({
            'id': f'{doc_id}_{i}',
            'filename': filename,
            'chunk_index': i,
            'content': chunk,
            'strategy': strategy
        })
    
    import faiss
    faiss.write_index(faiss_index, FAISS_INDEX_FILE + '.index')
    with open(DOCS_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    return JsonResponse({
        'success': True,
        'filename': filename,
        'chunks': len(selected_chunks),
        'strategy': strategy
    })


@api_view(['GET'])
def get_status(request):
    global faiss_index, documents
    if faiss_index is None or len(documents) == 0:
        load_faiss_index()
    
    docs_list = []
    if documents:
        file_names = set(d['filename'] for d in documents)
        for fname in file_names:
            count = sum(1 for d in documents if d['filename'] == fname)
            docs_list.append({'filename': fname, 'count': count})
    
    return JsonResponse({
        'has_index': faiss_index is not None,
        'doc_count': len(documents),
        'docs': docs_list,
        'embedding_model': EMBEDDING_MODEL,
        'rerank_model': RERANK_MODEL
    })


@api_view(['POST'])
def delete_document(request):
    global faiss_index, documents
    filename = request.data.get('filename', '')
    
    if not filename:
        return JsonResponse({'error': '请指定要删除的文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    if faiss_index is None or len(documents) == 0:
        load_faiss_index()
    
    if faiss_index is None:
        return JsonResponse({'error': '知识库为空'}, status=status.HTTP_400_BAD_REQUEST)
    
    import numpy as np
    
    indices_to_keep = [i for i, d in enumerate(documents) if d['filename'] != filename]
    
    if len(indices_to_keep) == len(documents):
        return JsonResponse({'error': '文件不存在'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(indices_to_keep) == 0:
        faiss_index = None
        documents = []
        if os.path.exists(FAISS_INDEX_FILE + '.index'):
            os.remove(FAISS_INDEX_FILE + '.index')
        if os.path.exists(DOCS_FILE):
            os.remove(DOCS_FILE)
    else:
        import faiss
        dim = faiss_index.d
        new_index = faiss.IndexFlatL2(dim)
        
        new_docs = []
        for i in indices_to_keep:
            new_docs.append(documents[i])
            vec = faiss_index.reconstruct(i)
            new_index.add(vec.reshape(1, -1))
        
        faiss_index = new_index
        documents = new_docs
        
        faiss.write_index(faiss_index, FAISS_INDEX_FILE + '.index')
        with open(DOCS_FILE, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
    
    return JsonResponse({'success': True})


def load_faiss_index():
    global faiss_index, documents
    if os.path.exists(FAISS_INDEX_FILE + '.index'):
        import faiss
        faiss_index = faiss.read_index(FAISS_INDEX_FILE + '.index')
    if os.path.exists(DOCS_FILE):
        with open(DOCS_FILE, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    return faiss_index, documents


@api_view(['POST'])
def chat(request):
    question = request.data.get('question', '').strip()
    if not question:
        return JsonResponse({'error': '请输入问题'}, status=status.HTTP_400_BAD_REQUEST)
    
    use_rerank = request.data.get('use_rerank', False)
    
    history = []
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    
    global faiss_index, documents
    load_faiss_index()
    
    if faiss_index is None or len(documents) == 0:
        return JsonResponse({'error': '请先上传文档'}, status=status.HTTP_400_BAD_REQUEST)
    
    question_vector = get_embeddings([question])
    import numpy as np
    question_vector = np.array(question_vector).astype('float32')
    
    top_k = 10
    distances, indices = faiss_index.search(question_vector, min(top_k, len(documents)))
    
    retrieved_chunks = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(documents):
            retrieved_chunks.append({
                'content': documents[idx]['content'],
                'filename': documents[idx]['filename'],
                'score': float(distances[0][i]),
                'index': idx
            })
    
    if use_rerank and RERANK_MODEL:
        chunk_texts = [c['content'] for c in retrieved_chunks]
        reranked = rerank(question, chunk_texts, top_k=5)
        reranked_indices = [chunk_texts.index(c) for c in reranked]
        retrieved_chunks = [retrieved_chunks[i] for i in reranked_indices]
    
    context = '\n\n'.join([f'[{c["filename"]}]\n{c["content"]}' for c in retrieved_chunks])
    
    prompt = f'''基于以下知识库内容回答问题。如果知识库中没有相关信息，请如实告知。

知识库内容：
{context}

问题：{question}

回答：'''

    try:
        llm_url = f'{LLM_BASE_URL}/v1/chat/completions'
        
        payload = {
            'model': LLM_MODEL,
            'messages': [
                {'role': 'system', 'content': '你是一个专业的AI助手，基于提供的知识库内容回答问题。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'top_p': 0.9
        }
        
        resp = requests.post(llm_url, json=payload, headers={
            'Authorization': f'Bearer {LLM_API_KEY}',
            'Content-Type': 'application/json'
        }, timeout=60)
        
        result = resp.json()
        answer = result['choices'][0]['message']['content']
        
    except Exception as e:
        answer = f'调用LLM失败: {str(e)}'
    
    history.append({'role': 'user', 'content': question})
    history.append({'role': 'assistant', 'content': answer})
    
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    return JsonResponse({
        'answer': answer,
        'retrieved_chunks': retrieved_chunks[:5],
        'history': history
    })


@api_view(['GET'])
def get_history(request):
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    return JsonResponse({'history': history})


@api_view(['POST'])
def clear_history(request):
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    return JsonResponse({'success': True})


urlpatterns = [
    path('upload/', upload_document, name='rag-upload'),
    path('save/', save_chunks, name='rag-save'),
    path('status/', get_status, name='rag-status'),
    path('delete/', delete_document, name='rag-delete'),
    path('chat/', chat, name='rag-chat'),
    path('history/', get_history, name='rag-history'),
    path('clear/', clear_history, name='rag-clear'),
]
