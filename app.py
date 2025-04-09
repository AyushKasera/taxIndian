from flask import Flask, render_template, request, jsonify
from t1 import IndianTaxCalculator, TaxChatbot  # Import your existing classes

app = Flask(__name__)
chatbot = TaxChatbot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    query = request.form.get('query', '')
    response = chatbot.process_query(query)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)