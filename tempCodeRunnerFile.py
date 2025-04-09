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