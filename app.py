from flask import Flask, request, jsonify
from flask_cors import CORS
from bot import legal_bot_response, classify_intent
import traceback

from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/query', methods=['POST'])
def handle_query():
    try:
        # Get user query and optional PDF
        user_query = request.form.get("query", "").strip()
        uploaded_file = request.files.get("file")
        
        print("DEBUG uploaded_file:", uploaded_file)


        if not user_query and not uploaded_file:
            return jsonify({'error': 'Query cannot be empty'}), 400

        # Default question for PDF-only uploads
        if not user_query and uploaded_file:
            user_query = "Summarize this document."
        # Extract PDF text if present
        pdf_text = ""
        if uploaded_file:
            from read_pdf import extract_text_from_pdf_file
            pdf_text = extract_text_from_pdf_file(uploaded_file)

        # Build LLM input
        llm_input = user_query
        if pdf_text:
            llm_input = (
                "You are given a document below.\n"
                "Answer the user's question using ONLY this document.\n\n"
                "DOCUMENT:\n"
                f"{pdf_text}\n\n"
                "QUESTION:\n"
                f"{user_query}"
            )

        # STEP 1: classify intent (question only)
        detected_cat = classify_intent(user_query)
        print(f"--- Detected Intent: {detected_cat.upper()} ---")

        if uploaded_file:
            # PDF present → always use document-aware prompt
            response = legal_bot_response(llm_input, detected_cat)
        elif detected_cat == "other":
            response = (
                "Hi! I'm your BC Legal Assistant. I can help you with specific questions "
                "about **Rent**, **Work**, or **Immigration** in British Columbia. "
                "You can also upload a document for analysis."
            )
        else:
            response = legal_bot_response(user_query, detected_cat)


        print(f"\n[{detected_cat.upper()} BOT]:\n{response}")

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
