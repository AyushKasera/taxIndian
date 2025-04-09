import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import re
# nltk.download()
# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Training data for intent recognition
training_data = [
    ("I have 1000000 income and 10K home loan and 50K house rent how much tax", "tax_calculation"),
    ("Calculate tax for 500000 income and 20K loan", "tax_calculation"),
    ("How much tax do I pay for 1500000 income", "tax_calculation"),
    ("Tell me about tax slabs", "tax_info"),
    ("What are the tax rates", "tax_info"),
    ("Hi, how are you", "greeting"),
    ("Goodbye", "goodbye"),
]

# Separate sentences and labels
sentences, labels = zip(*training_data)

# Preprocess text
stop_words = set(stopwords.words('english'))

def preprocess(text):
    tokens = word_tokenize(text.lower())
    return ' '.join([word for word in tokens if word not in stop_words and word.isalnum()])

processed_sentences = [preprocess(sentence) for sentence in sentences]

# Vectorize the text
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(processed_sentences)
y = labels

# Train a simple classifier
classifier = MultinomialNB()
classifier.fit(X, y)

# Indian Tax Slabs for FY 2025-26 (New Regime, simplified for example)
tax_slabs = [
    (300000, 0),        # Up to 3,00,000: 0%
    (600000, 0.05),     # 3,00,001 - 6,00,000: 5%
    (900000, 0.10),     # 6,00,001 - 9,00,000: 10%
    (1200000, 0.15),    # 9,00,001 - 12,00,000: 15%
    (1500000, 0.20),    # 12,00,001 - 15,00,000: 20%
    (float('inf'), 0.30) # Above 15,00,000: 30%
]

# Function to calculate tax based on income (New Regime)
def calculate_tax(income, home_loan_interest=0, house_rent=0):
    # Standard deduction in new regime (FY 2025-26): ₹75,000
    standard_deduction = 75000
    # Home loan interest deduction (simplified, assuming self-occupied property, max ₹2,00,000)
    home_loan_deduction = min(home_loan_interest, 200000)
    # House rent doesn't directly affect tax in new regime (HRA not applicable), included for future extension
    
    taxable_income = max(0, income - standard_deduction - home_loan_deduction)
    tax = 0
    
    # Calculate tax based on slabs
    previous_limit = 0
    for limit, rate in tax_slabs:
        if taxable_income > previous_limit:
            taxable_in_slab = min(taxable_income, limit) - previous_limit
            tax += taxable_in_slab * rate
            previous_limit = limit
        else:
            break
    
    # Add 4% Health & Education Cess
    cess = tax * 0.04
    total_tax = tax + cess
    
    # Rebate under Section 87A: If taxable income ≤ ₹7,00,000, tax is 0
    if taxable_income <= 700000:
        total_tax = 0
    
    return round(total_tax)

# Function to extract numbers from query
def extract_numbers(query):
    numbers = re.findall(r'\d+', query)
    if len(numbers) >= 1:
        income = int(numbers[0]) * (100000 if 'lakh' in query.lower() else 1)
        home_loan = int(numbers[1]) * 1000 if len(numbers) > 1 and 'loan' in query.lower() else 0
        house_rent = int(numbers[2]) * 1000 if len(numbers) > 2 and 'rent' in query.lower() else 0
        return income, home_loan, house_rent
    return None, None, None

# Chatbot response function
def chatbot_response(query):
    processed_query = preprocess(query)
    X_query = vectorizer.transform([processed_query])
    intent = classifier.predict(X_query)[0]
    
    if intent == "tax_calculation":
        income, home_loan, house_rent = extract_numbers(query)
        if income is not None:
            tax = calculate_tax(income, home_loan, house_rent)
            return f"Your tax liability for an income of ₹{income:,} with ₹{home_loan:,} home loan interest and ₹{house_rent:,} house rent is ₹{tax:,} (New Regime, FY 2025-26)."
        return "Please provide valid income details (e.g., 'I have 1000000 income')."
    
    elif intent == "tax_info":
        return "In the New Regime (FY 2025-26): Up to ₹3L: 0%, ₹3L-6L: 5%, ₹6L-9L: 10%, ₹9L-12L: 15%, ₹12L-15L: 20%, Above ₹15L: 30%. Plus 4% cess."
    
    elif intent == "greeting":
        return "Hello! I'm here to help with your tax queries. How can I assist you?"
    
    elif intent == "goodbye":
        return "Goodbye! Feel free to come back with more tax questions."
    
    return "Sorry, I didn't understand that. Please ask about tax calculation or tax slabs!"

# Main chatbot loop
def run_chatbot():
    print("Welcome to the Indian Tax Chatbot! (Type 'exit' to quit)")
    while True:
        query = input("You: ")
        if query.lower() == 'exit':
            print("Chatbot: Goodbye!")
            break
        response = chatbot_response(query)
        print(f"Chatbot: {response}")

# Example run
if __name__ == "__main__":
    run_chatbot()