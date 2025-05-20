from nltk.tokenize import sent_tokenize
import streamlit as st

def evaluate_synopsis(article_text, synopsis_text, tokenizer, model):
    """Evaluate the quality of a synopsis based on the original article"""
    from utils.embeddings import compute_chunk_similarities
    
    # Compute similarity metrics
    chunk_similarities, avg_similarity = compute_chunk_similarities(article_text, synopsis_text, tokenizer, model)
    
    # Calculate coverage score (how many chunks are well-represented)
    coverage_threshold = 0.5  # Similarity threshold for "good coverage"
    coverage_percentage = sum(1 for sim in chunk_similarities if sim > coverage_threshold) / len(chunk_similarities)
    
    # Calculate length ratio score (penalize if too short or too long)
    article_word_count = len(article_text.split())
    synopsis_word_count = len(synopsis_text.split())
    ideal_ratio = 0.2  # Synopsis should be ~20% of article length
    actual_ratio = synopsis_word_count / max(1, article_word_count)
    length_ratio_score = 1.0 - min(1.0, abs(actual_ratio - ideal_ratio) / ideal_ratio)
    
    # Calculate coherence score (based on average similarity)
    coherence_score = avg_similarity
    
    # Calculate clarity score (based on sentence structure, simplified here)
    synopsis_sentences = sent_tokenize(synopsis_text)
    avg_sentence_length = sum(len(sent.split()) for sent in synopsis_sentences) / max(1, len(synopsis_sentences))
    clarity_penalty = 0 if 10 <= avg_sentence_length <= 25 else (min(avg_sentence_length, 40) - 25) / 15
    clarity_score = 1.0 - min(1.0, clarity_penalty)
    
    # Calculate final weighted score
    weights = {
        'content_coverage': 0.50,
        'coherence': 0.25,
        'clarity': 0.15,
        'length_ratio': 0.10
    }
    
    scores = {
        'content_coverage': coverage_percentage * 100,
        'coherence': coherence_score * 100,
        'clarity': clarity_score * 100,
        'length_ratio': length_ratio_score * 100
    }
    
    final_score = sum(scores[metric] * weight for metric, weight in weights.items())
    final_score = max(0, min(100, final_score))  # Ensure within 0-100 range
    
    # Generate qualitative feedback
    feedback = []
    
    if scores['content_coverage'] < 60:
        feedback.append("The synopsis misses key information from the article. Consider including more essential points.")
    elif scores['content_coverage'] > 85:
        feedback.append("Excellent coverage of the article's main points.")
        
    if scores['coherence'] < 60:
        feedback.append("The synopsis could be more aligned with the article's focus and structure.")
    elif scores['coherence'] > 85:
        feedback.append("The synopsis captures the essence of the article well.")
        
    if scores['clarity'] < 60:
        feedback.append("Consider simplifying sentence structure for better readability.")
    elif scores['clarity'] > 85:
        feedback.append("The synopsis is clear and well-structured.")
        
    if scores['length_ratio'] < 60:
        if actual_ratio < ideal_ratio:
            feedback.append("The synopsis is too brief relative to the article length.")
        else:
            feedback.append("The synopsis is too detailed for an effective summary.")
    
    # Limit to 2-3 lines of feedback
    if len(feedback) > 3:
        feedback = feedback[:3]
    
    return {
        'final_score': round(final_score, 1),
        'detailed_scores': {k: round(v, 1) for k, v in scores.items()},
        'feedback': feedback
    }