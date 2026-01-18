from flask import Flask, request, jsonify
from flask_cors import CORS
from bot import legal_bot_response, classify_intent
import traceback

from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/query', methods=['POST'])
def handle_query():
    """
    Receives a user query from the frontend and returns the bot's response.
    Expected JSON: {"query": "user question"}
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query field'}), 400
        
        user_query = data['query'].strip()
        
        if not user_query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
            # Test queries


        # STEP 1: Let the AI decide the category
        detected_cat = classify_intent(user_query)
        print(f"--- Detected Intent: {detected_cat.upper()} ---")

        if detected_cat == "other":
            # Provide a specialized response for general chat/greetings
            response = ("Hi! I'm your BC Legal Assistant. I can help you with specific questions "
                        "about **Rent**, **Work**, or **Immigration** in British Columbia. "
                        "How can I help you with those today?")
        else:

        # STEP 2: Get the response using the detected category
            response = legal_bot_response(user_query, detected_cat)

        print(f"\n[{detected_cat.upper()} BOT]:\n{response}")

        # ----------
        
        # -----------
        
        return jsonify({
            'success': True,
            'response': response,
            'category': detected_cat
        }), 200
    
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
