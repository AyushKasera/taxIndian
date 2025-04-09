import re
from datetime import datetime

class IndianTaxCalculator:
    def __init__(self):
        # Tax slabs for FY 2024-25
        self.tax_slabs_old = [
            (0, 250000, 0),
            (250001, 500000, 5),
            (500001, 1000000, 20),
            (1000001, float('inf'), 30)
        ]
        
        self.tax_slabs_new = [
            (0, 300000, 0),
            (300001, 600000, 5),
            (600001, 900000, 10),
            (900001, 1200000, 15),
            (1200001, 1500000, 20),
            (1500001, float('inf'), 30)
        ]
        
        # Initialize all deductions from the Excel file
        self.deductions = {
            '80C': {'limit': 150000, 'desc': "Investments (PF, PPF, LIC, etc.)"},
            '80CCC': {'limit': 150000, 'combined_with': '80C', 'desc': "Pension funds"},
            '80CCD(1)': {'limit': 150000, 'combined_with': '80C', 'calc': lambda x: min(0.1*x, 150000), 'desc': "NPS contributions"},
            '80CCD(1B)': {'limit': 50000, 'desc': "Additional NPS"},
            '80CCH': {'limit': float('inf'), 'desc': "Agniveer Corpus Fund"},
            '80D': {'limit': 25000, 'senior_limit': 50000, 'desc': "Health insurance"},
            '80DD': {'limit': 75000, 'severe_limit': 125000, 'desc': "Disabled dependent"},
            '80DDB': {'limit': 40000, 'senior_limit': 100000, 'desc': "Medical treatment"},
            '80E': {'limit': float('inf'), 'desc': "Education loan interest"},
            '80EE': {'limit': 50000, 'desc': "First-time home loan"},
            '80EEA': {'limit': 150000, 'desc': "Affordable housing loan"},
            '80EEB': {'limit': 150000, 'desc': "Electric vehicle loan"},
            '80G': {'limit': float('inf'), 'desc': "Charitable donations"},
            '80GG': {'limit': 60000, 'calc': lambda x: min(5000*12, 0.25*x, x-0.1*x), 'desc': "Rent paid"},
            '80GGA': {'limit': float('inf'), 'desc': "Scientific research donations"},
            '80TTA': {'limit': 10000, 'desc': "Savings account interest"},
            '80TTB': {'limit': 50000, 'desc': "Senior citizen interest income"},
            '80U': {'limit': 75000, 'severe_limit': 125000, 'desc': "Self-disability"},
            '24(b)': {'limit': 200000, 'desc': "Home loan interest"},
            '80RRB': {'limit': 300000, 'desc': "Patent royalties"},
            '80QQB': {'limit': 300000, 'desc': "Author royalties"},
            'standard': {'limit': 50000, 'desc': "Standard deduction"}
        }

    def convert_word_to_number(self, amount_str):
        """Convert Indian number words to numeric value"""
        amount_str = amount_str.lower().replace(',', '').replace(' ', '')
        
        # Handle crore
        if 'crore' in amount_str:
            num = float(amount_str.replace('crore', '')) * 10000000
            return int(num)
        
        # Handle lakh
        if 'lac' in amount_str or 'lakh' in amount_str:
            num = float(re.sub(r'la[ck]h', '', amount_str)) * 100000
            return int(num)
        
        # Handle thousand
        if 'thousand' in amount_str or 'k' in amount_str:
            num = float(re.sub(r'thousand|k', '', amount_str)) * 1000
            return int(num)
        
        return None

    def convert_amount_to_numeric(self, amount_str):
        """Convert any amount format to numeric value"""
        if isinstance(amount_str, (int, float)):
            return int(amount_str)
            
        amount_str = str(amount_str).strip().lower()
        
        # Remove commas and spaces
        amount_str = amount_str.replace(',', '').replace(' ', '')
        
        # Handle pure numeric values
        if re.match(r'^\d+$', amount_str):
            return int(amount_str)
            
        # Handle abbreviations (5L, 10Cr, 25K)
        abbrev_map = {
            'l': 100000,
            'lac': 100000,
            'lakh': 100000,
            'cr': 10000000,
            'crore': 10000000,
            'k': 1000,
            'thousand': 1000
        }
        
        # Find the unit and multiplier
        for unit, multiplier in abbrev_map.items():
            if unit in amount_str:
                num_part = amount_str.replace(unit, '')
                if num_part:
                    return int(float(num_part) * multiplier)
                return multiplier
        
        # Handle word formats (5 lakh, 10 crore)
        word_patterns = [
            (r'(\d+\.?\d*)\s*(la[ck]h)', 100000),
            (r'(\d+\.?\d*)\s*(crore)', 10000000),
            (r'(\d+)\s*(thousand|k)', 1000)
        ]
        
        for pattern, multiplier in word_patterns:
            match = re.search(pattern, amount_str)
            if match:
                return int(float(match.group(1))) * multiplier
                
        return None
    
    def extract_numbers(self, text):
        """Extract all numbers from text in any format"""
        numbers = []
        
        # Standard numeric formats (5,00,000 or 500000)
        numeric_values = [int(num.replace(',', '')) for num in re.findall(r'\d[\d,]*\d+', text)]
        numbers.extend(numeric_values)
        
        # Word formats and abbreviations
        patterns = [
            (r'(\d+\.?\d*)\s*(la[ck]h)', 100000),
            (r'(\d+\.?\d*)\s*(crore)', 10000000),
            (r'(\d+)\s*(thousand|k)', 1000),
            (r'(\d+)\s*(l|cr|k)\b', None)  # For 5L, 10Cr, 25K
        ]
        
        for pattern, multiplier in patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                num = float(match.group(1))
                if multiplier:
                    numbers.append(int(num * multiplier))
                else:
                    unit = match.group(2)
                    if unit == 'l':
                        numbers.append(int(num * 100000))
                    elif unit == 'cr':
                        numbers.append(int(num * 10000000))
                    elif unit == 'k':
                        numbers.append(int(num * 1000))
        
        return numbers


    
    def calculate_tax(self, income, age, deductions, regime='new'):
        taxable_income = income
        applied_deductions = {}
        
        if regime.lower() == 'old':
            # Apply standard deduction
            taxable_income -= self.deductions['standard']['limit']
            applied_deductions['standard'] = self.deductions['standard']['limit']
            
            # Process all other deductions
            for ded_code, ded_amount in deductions.items():
                if ded_code in self.deductions:
                    ded_info = self.deductions[ded_code]
                    
                    # Handle special calculations
                    if 'calc' in ded_info:
                        max_ded = ded_info['calc'](income)
                    else:
                        max_ded = ded_info['limit']
                    
                    # Handle senior citizen limits
                    if 'senior_limit' in ded_info and age >= 60:
                        max_ded = ded_info['senior_limit']
                    
                    # Handle combined limits (like 80C+80CCC+80CCD(1))
                    if 'combined_with' in ded_info:
                        combined_code = ded_info['combined_with']
                        if combined_code in applied_deductions:
                            remaining = self.deductions[combined_code]['limit'] - applied_deductions[combined_code]
                            max_ded = min(max_ded, remaining)
                    
                    actual_ded = min(ded_amount, max_ded)
                    taxable_income -= actual_ded
                    applied_deductions[ded_code] = actual_ded
                    
            slabs = self.tax_slabs_old
        else:
            # New regime only has standard deduction
            taxable_income -= self.deductions['standard']['limit']
            applied_deductions['standard'] = self.deductions['standard']['limit']
            slabs = self.tax_slabs_new
            
        # Calculate tax based on slabs
        tax = 0
        for slab in slabs:
            if taxable_income > slab[0]:
                taxable_in_slab = min(taxable_income, slab[1]) - slab[0]
                tax += taxable_in_slab * (slab[2] / 100)
                
        tax += tax * 0.04  # Cess
        return max(0, tax), taxable_income, applied_deductions

class TaxChatbot:
    def __init__(self):
        self.calculator = IndianTaxCalculator()
        self.user_data = {}
        
    def extract_deductions(self, text):
        """Enhanced to handle all amount formats"""
        deductions = {}
        text_lower = text.lower()
        
        for code in self.calculator.deductions:
            code_lower = code.lower()
            if code_lower in text_lower:
                # Find the text segment after the deduction code
                after_code = text.split(code)[-1][:50]  # Look 50 chars ahead
                
                # Try to extract amount in any format
                amount = None
                
                # Pattern 1: Code followed directly by number (80C 1.5L)
                direct_num = re.search(rf"{code}[^\d]*([\d,.]+[lckr]*)", text, re.IGNORECASE)
                if direct_num:
                    amount_str = direct_num.group(1)
                    amount = self.calculator.convert_amount_to_numeric(amount_str)
                
                # Pattern 2: Any number in the vicinity
                if amount is None:
                    nearby_numbers = self.calculator.extract_numbers(after_code)
                    if nearby_numbers:
                        amount = nearby_numbers[0]
                
                if amount:
                    deductions[code] = amount
        
        # Special handling for home loan
        if 'home loan' in text_lower or 'housing loan' in text_lower:
            loan_numbers = self.calculator.extract_numbers(text)
            if loan_numbers:
                deductions['24(b)'] = min(loan_numbers[-1], 200000)  # Cap at 2L
        
        return deductions

       
    def greet(self):
        return ("Welcome to the Advanced Indian Tax Advisor!\n"
                "I can analyze your taxes under both regimes with all deduction types.\n"
                "Try queries like:\n"
                "- '15L income with 2L 80C and 50K 80D'\n"
                "- 'Compare tax for 12L with home loan 3L'\n"
                "- 'Show me all available deductions'")
    
    def extract_deductions(self, text):
        """Extract deduction codes and amounts from text"""
        deductions = {}
        text_lower = text.lower()
        
        # Find all deduction codes mentioned
        for code in self.calculator.deductions:
            if code.lower() in text_lower:
                # Find the amount after the code
                pattern = re.compile(rf"{code}[^\d]*(\d+[\d,]*\d+)", re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    amount = int(match.group(1).replace(',', ''))
                    deductions[code] = amount
                elif any(char.isdigit() for char in text.split(code)[1][:20]):
                    # Try to find nearby numbers
                    after_code = text.split(code)[1][:20]
                    numbers = re.findall(r'\d+', after_code)
                    if numbers:
                        deductions[code] = int(numbers[0])
        
        # Special handling for common terms
        if 'home loan' in text_lower or 'housing loan' in text_lower:
            numbers = re.findall(r'\d+', text)
            if len(numbers) > 1:
                deductions['24(b)'] = int(numbers[-1])
        
        return deductions
    
    def _compare_regimes(self, income, age, deductions):
        """Calculate and compare both tax regimes"""
        old_tax, old_taxable, old_deductions = self.calculator.calculate_tax(income, age, deductions, 'old')
        new_tax, new_taxable, new_deductions = self.calculator.calculate_tax(income, age, deductions, 'new')
        
        savings = old_tax - new_tax
        recommendation = ("OLD regime" if old_tax < new_tax 
                         else "NEW regime" if new_tax < old_tax 
                         else "BOTH regimes are equal")
        
        comparison = {
            'old': {'tax': old_tax, 'taxable': old_taxable, 'deductions': old_deductions},
            'new': {'tax': new_tax, 'taxable': new_taxable, 'deductions': new_deductions},
            'savings': abs(savings),
            'recommendation': recommendation,
            'better_regime': 'old' if old_tax < new_tax else 'new'
        }
        return comparison
    
    def _generate_deduction_report(self, deductions):
        """Generate report of applied deductions"""
        report = "\n🔹 Applied Deductions:\n"
        for code, amount in deductions.items():
            desc = self.calculator.deductions.get(code, {}).get('desc', code)
            report += f"- {code}: ₹{amount:,} ({desc})\n"
        return report
    
    def _generate_regime_comparison(self, comparison):
        """Generate detailed comparison of both regimes"""
        report = "\n🏦 **Tax Regime Comparison**\n"
        report += "="*60 + "\n"
        
        # Old Regime Details
        report += "🔸 OLD Regime:\n"
        report += f"- Taxable Income: ₹{comparison['old']['taxable']:,}\n"
        report += f"- Tax Liability: ₹{comparison['old']['tax']:,.2f}\n"
        report += self._generate_deduction_report(comparison['old']['deductions'])
        report += "- Slabs: 0-2.5L(0%), 2.5-5L(5%), 5-10L(20%), 10L+(30%)\n\n"
        
        # New Regime Details
        report += "🔸 NEW Regime:\n"
        report += f"- Taxable Income: ₹{comparison['new']['taxable']:,}\n"
        report += f"- Tax Liability: ₹{comparison['new']['tax']:,.2f}\n"
        report += self._generate_deduction_report(comparison['new']['deductions'])
        report += "- Slabs: 0-3L(0%), 3-6L(5%), 6-9L(10%), 9-12L(15%), 12-15L(20%), 15L+(30%)\n\n"
        
        # Recommendation
        report += "💡 **Recommendation**:\n"
        report += f"- {comparison['recommendation']} is better\n"
        if comparison['savings'] > 0:
            report += f"- Potential savings: ₹{comparison['savings']:,.2f}\n"
        
        report += "\nℹ️ Note:\n"
        report += "- Old regime requires investment proofs for deductions\n"
        report += "- New regime has higher basic exemption but fewer deductions\n"
        report += "="*60 + "\n"
        
        return report
    
    def show_all_deductions(self):
        """Display all available deductions"""
        report = "📋 All Available Deductions:\n"
        report += "="*60 + "\n"
        for code, info in self.calculator.deductions.items():
            limit = f"₹{info['limit']:,}" if isinstance(info['limit'], int) else info['limit']
            report += f"🔹 {code} (Max: {limit}): {info['desc']}\n"
        report += "\n💡 Tip: Include deduction codes with amounts in your query\n"
        report += "Example: '15L income with 1.5L 80C and 50K 80D'\n"
        report += "="*60
        return report
    
    def process_query(self, query):
        self.user_data = {'deductions': {}}
        
        # Check for special commands
        if 'show deductions' in query.lower() or 'list deductions' in query.lower():
            return self.show_all_deductions()
        
        # Extract income
        
        numbers = self.calculator.extract_numbers(query)
        if numbers:
            self.user_data['income'] = max(numbers)  # Assume largest number is income
            
        # Extract age if mentioned
        age_match = re.search(r'age\s*(\d+)', query.lower())
        self.user_data['age'] = int(age_match.group(1)) if age_match else 30
        
        # Extract deductions
        self.user_data['deductions'] = self.extract_deductions(query)
        
        # Check regime preference
        self.user_data['regime'] = 'compare'  # Default to comparison
        if 'old regime' in query.lower():
            self.user_data['regime'] = 'old'
        elif 'new regime' in query.lower():
            self.user_data['regime'] = 'new'
        
        if 'income' in self.user_data:
            if self.user_data['regime'] == 'compare':
                comparison = self._compare_regimes(
                    self.user_data['income'],
                    self.user_data['age'],
                    self.user_data['deductions']
                )
                response = f"📊 Analysis for Income: ₹{self.user_data['income']:,}"
                if self.user_data['age'] >= 60:
                    response += f" (Senior Citizen)"
                response += self._generate_regime_comparison(comparison)
            else:
                tax, taxable, deductions = self.calculator.calculate_tax(
                    self.user_data['income'],
                    self.user_data['age'],
                    self.user_data['deductions'],
                    self.user_data['regime']
                )
                response = f"Under {self.user_data['regime'].upper()} regime:\n"
                response += f"- Taxable Income: ₹{taxable:,}\n"
                response += f"- Estimated Tax: ₹{tax:,.2f}\n"
                response += self._generate_deduction_report(deductions)
            
            response += "\n🔍 For more accuracy, please provide:\n"
            response += "- Exact investment amounts under each section\n"
            response += "- Any other income sources or deductions\n"
            return response
        
        return ("Please provide your income amount for tax calculation.\n"
                "Try 'show deductions' to see all available options.")

    def chat(self):
        print(self.greet())
        while True:
            query = input("\nYou: ")
            if query.lower() in ['exit', 'quit', 'bye']:
                print("Bot: Thank you for using the Tax Advisor. Goodbye!")
                break
            response = self.process_query(query)
            print(f"\nBot: {response}")

if __name__ == "__main__":
    chatbot = TaxChatbot()
    
    test_cases = [
        ("I earn 5 lakh rupees", 500000),
        ("My income is 10 crore", 10000000),
        ("80C deduction of 1.5L", 150000),
        ("80D 50 thousand", 50000),
        ("Home loan 3L", 300000),
        ("Salary is 25K per month", 25000),
        ("Invested 2.5Cr in property", 25000000),
        ("80C 1,50,000", 150000),
        ("80CCD(1B) 50k", 50000)
    ]
    
    print("Testing amount parsing:")
    for text, expected in test_cases:
        parsed = chatbot.calculator.extract_numbers(text)
        result = parsed[0] if parsed else None
        print(f"'{text}' -> {result} (Expected: {expected}) {'✅' if result == expected else '❌'}")
    
    # Run normal examples
    examples = [
        "I earn 5 lakh per year with 1.5L in 80C",
        "What's my tax for 10 crore in old regime with 80CCD(1B) 50K",
        "Compare tax for 25K income age 65 with 80D 25 thousand"
    ]
    
    print("\nSmart Tax Advisor - Sample Calculations:")
    for example in examples:
        print(f"\nQuery: {example}")
        print("Response:", chatbot.process_query(example))