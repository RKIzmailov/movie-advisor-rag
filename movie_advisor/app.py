from flask import Flask, request, jsonify
import uuid
import logging
from rag import rag 

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Generate a conversation ID
    conversation_id = str(uuid.uuid4())
    
    try:
        answer = rag(question)
        result = jsonify({
            'conversation_id': conversation_id,
            'question': question,
            'result': answer,
        })
        
        return result
    
    except Exception as e:
        logging.error(f"Error processing question: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your question'}), 500

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    conversation_id = data.get('conversation_id')
    feedback = data.get('feedback')
    
    if not conversation_id or feedback not in [1, -1]:
        return jsonify({'error': 'Invalid input'}), 400
    
    # For now, just acknowledge receiving the feedback
    # TODO: Implement database writing logic here
    
    return jsonify({
        'message': 'Feedback received. Thank you!',
        'conversation_id': conversation_id,
        'feedback': feedback
    })

if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        logging.error(f"Failed to start the Flask app: {str(e)}")