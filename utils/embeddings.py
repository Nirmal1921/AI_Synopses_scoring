import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from nltk.tokenize import sent_tokenize
import streamlit as st

@st.cache_resource
def load_embedding_model():
    """Load the model and tokenizer for embeddings"""
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    return tokenizer, model

def get_embeddings(text, tokenizer, model):
    """Generate embeddings for the given text"""
    # Handle empty or very short texts
    if not text or len(text.strip()) < 5:
        # Return a zero vector of the expected dimension (384 for all-MiniLM-L6-v2)
        return torch.zeros(384)
    
    # Tokenize and get model outputs
    inputs = tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Mean pooling
    attention_mask = inputs["attention_mask"]
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    embeddings = sum_embeddings / sum_mask
    
    # Normalize embeddings
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    return embeddings.squeeze()

def compute_similarity(embedding1, embedding2):
    """Compute cosine similarity between two embeddings"""
    return F.cosine_similarity(embedding1.unsqueeze(0), embedding2.unsqueeze(0)).item()

def compute_chunk_similarities(article_text, synopsis_text, tokenizer, model):
    """
    Split the article into chunks and compute similarity with the synopsis
    to better handle longer texts
    """
    # Split article into chunks of roughly equal size
    article_sentences = sent_tokenize(article_text)
    chunk_size = max(1, len(article_sentences) // 10)  # Aim for about 10 chunks
    article_chunks = [' '.join(article_sentences[i:i+chunk_size]) 
                     for i in range(0, len(article_sentences), chunk_size)]
    
    # Get embeddings for synopsis and article chunks
    synopsis_embedding = get_embeddings(synopsis_text, tokenizer, model)
    chunk_similarities = []
    
    for chunk in article_chunks:
        chunk_embedding = get_embeddings(chunk, tokenizer, model)
        similarity = compute_similarity(synopsis_embedding, chunk_embedding)
        chunk_similarities.append(similarity)
    
    # Return both individual and average similarities
    return chunk_similarities, sum(chunk_similarities) / len(chunk_similarities)