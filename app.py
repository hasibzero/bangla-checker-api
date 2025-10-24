import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# --- Configuration ---
app = Flask(__name__)
CORS(app)

bangla_word_set = set()

# --- NEW: List all the dictionary files we want to load ---
# These are all the major wordlist files from that GitHub repository
DICTIONARY_FILES = [
    'BengaliWordList_439.txt',
    'BengaliWordList_112.txt',
    'BengaliWordList_48.txt',
    'BengaliWordList_40.txt',
    'BengaliPhoneticWordFrequency_164.txt' # This one is also a word list
]

# --- Utility Functions ---

def load_dictionary():
    """
    Loads ALL the dictionary files from the list above.
    The 'set' will automatically handle duplicates.
    """
    global bangla_word_set
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    total_words = 0
    
    # --- UPDATED: Loop through every file in our list ---
    for file_name in DICTIONARY_FILES:
        file_path = os.path.join(dir_path, file_name)
        
        try:
            # We read the file with 'utf-8' encoding for Bangla
            with open(file_path, 'r', encoding='utf-8') as f:
                words = f.readlines()
            
            file_word_count = 0
            for word in words:
                clean_word = word.strip()
                if clean_word:
                    # Add the word to our one big set
                    bangla_word_set.add(clean_word)
                    file_word_count += 1
            
            print(f"--- Loaded {file_word_count} words from {file_name} ---")

        except FileNotFoundError:
            # This is not a critical error; maybe the user didn't download all of them.
            # We just print a warning and continue.
            print(f"WARNING: '{file_name}' not found at {file_path}. Skipping.")
        except Exception as e:
            print(f"ERROR reading {file_name}: {e}")
            
    total_words = len(bangla_word_set)
    print(f"--- Total unique words loaded: {total_words} ---")
        
def find_misspelled_words(text):
    """
    Checks text against the loaded dictionary and returns misspelled words.
    """
    if not bangla_word_set:
        print("Dictionary not loaded, cannot check.")
        return []

    # This regex splits text by spaces and common Bangla/English punctuation.
    words = re.split(r'[\s।,.?!;()]+', text)
    
    misspelled = set() # Use a set to avoid duplicate errors
    for word in words:
        if word and word not in bangla_word_set:
            misspelled.add(word)
            
    return list(misspelled)

# --- API Endpoint ---

@app.route('/check', methods=['POST'])
def check_text():
    """
    This is the main API endpoint that the browser extension will call.
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "No 'text' field provided"}), 400
        
        text_to_check = data['text']
        
        # Load the dictionary on the first request.
        # Vercel can put functions to "sleep", so we ensure
        # the dictionary is loaded every time the function "wakes up".
        if not bangla_word_set:
            load_dictionary()

        error_words = find_misspelled_words(text_to_check)
        return jsonify({"errors": error_words})
        
    except Exception as e:
        print(f"Error during /check: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

# Vercel looks for the 'app' variable, so we don't need
# the 'if __name__ == "__main__":' block.

