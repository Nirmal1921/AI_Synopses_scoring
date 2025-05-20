import os
import re
import tempfile
import torch
import nltk
from nltk.tokenize import sent_tokenize

# Ensure NLTK data is downloaded
def ensure_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

def anonymize_text(text):
    """
    Replace names, dates, and specific identifiers with placeholders.
    This is a simple implementation - a more robust solution would use NER.
    """
    # Replace dates (simple pattern)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE]', text)
    text = re.sub(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b', '[DATE]', text)
    
    # Replace emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Replace phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
    
    # Replace URLs
    text = re.sub(r'https?://\S+', '[URL]', text)
    
    # Replace proper nouns (crude approximation - would be better with NER)
    # Look for capitalized words not at the start of sentences
    sentences = sent_tokenize(text)
    anonymized_sentences = []
    
    for sentence in sentences:
        words = sentence.split()
        if len(words) > 0:
            # Keep the first word as is (could be capitalized as start of sentence)
            new_sentence = [words[0]]
            
            # Process remaining words
            for word in words[1:]:
                # If word starts with capital letter and isn't a common word that might be capitalized
                if (word[0].isupper() and 
                    word.lower() not in ['i', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                                         'saturday', 'sunday', 'january', 'february', 'march', 'april', 
                                         'may', 'june', 'july', 'august', 'september', 'october', 
                                         'november', 'december']):
                    new_sentence.append('[NAME]')
                else:
                    new_sentence.append(word)
            
            anonymized_sentences.append(" ".join(new_sentence))
        else:
            anonymized_sentences.append(sentence)
    
    return " ".join(anonymized_sentences)

def create_temp_file(content, suffix='.txt'):
    """Create a temporary file with the given content and return its path"""
    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=suffix) as temp:
        temp.write(content)
        return temp.name

def cleanup_temp_files(file_paths):
    """Clean up temporary files"""
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass  # Silent failure is acceptable for cleanup