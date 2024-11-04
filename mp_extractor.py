import pdfplumber
import pandas as pd
from pathlib import Path
import re
from datetime import datetime
from sys import argv

class StatementConverter:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        
    def extract_header_info(self, text):
        """Extract header information from the statement."""
        header = {}
 
        # Regular expressions for header information
        # print(text)
        patterns = {
            'name': r'(.+?)\nCVU:',
            'cvu': r'CVU: (\d+)',
            'cuit': r'CUIT/ CUIL:\s*(\d+)',
            'period': r'Periodo:\s*(.+?)\n',
            'initial_balance': r'Saldo inicial: \$ ([\d,.]+)',
            'final_balance': r'Saldo final: \$ ([\d,.]+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                header[key] = match.group(1).strip()
                
        # Convert monetary values to float
        for key in ['initial_balance', 'final_balance']:
            if key in header:
                header[key] = float(header[key].replace('.', '').replace(',', '.'))
                
        return header

    def parse_transactions(self, text):
        """Extract transaction data from the statement text."""
        # First, let's fix wrapped lines
        lines = text.split('\n')
        processed_lines = []
        current_line = ''
        
        last_line = lines[0]
        for i, line in enumerate(lines):
            # If line starts with a date pattern, it's a new transaction
            if re.match(r'\d{2}-\d{2}-\d{4}', line):
                if re.match(r'(\d{2}-\d{2}-\d{4})\s+(\d+)', line):
                    split_line = line.split(" ")
                    current_line = split_line[0] + " " +  last_line + " " + lines[i + 1] + " " +  " ".join(split_line[1:])
                else:
                    current_line = line
                processed_lines.append(current_line)
            last_line = line
        
        # Don't forget to add the last line
        if current_line:
            processed_lines.append(current_line.strip())
        
        # Join back into text with newlines
        processed_text = '\n'.join(processed_lines)
        
        # Regular expression to match transaction lines
        transaction_pattern = r'(\d{2}-\d{2}-\d{4})\s+(.*?)\s+(\d+)\s+\$\s*([-]?[\d.,]+)\s+\$\s*([\d.,]+)'
        
        transactions = []
        i = 0
        for match in re.finditer(transaction_pattern, processed_text):
            i += 1
            date, description, operation_id, value, balance = match.groups()
            
            # Convert date string to datetime
            date = datetime.strptime(date, '%d-%m-%Y')
            
            # Clean up monetary values
            value = float(value.replace('.', '').replace(',', '.'))
            balance = float(balance.replace('.', '').replace(',', '.'))
            
            transactions.append({
                'date': date,
                'description': description.strip(),
                'operation_id': operation_id,
                'value': value,
                'balance': balance
            })
            
        print("Rows Captured: " + str(i))
        return transactions

    def convert_to_excel(self, output_path):
        """Convert PDF statement to Excel file."""
        # Read PDF
        with pdfplumber.open(self.pdf_path) as pdf:
            text = '\n'.join(page.extract_text() for page in pdf.pages)
        
        # Extract header information
        header_info = self.extract_header_info(text)
        
        # Parse transactions
        transactions = self.parse_transactions(text)
        
        # Create DataFrames
        transactions_df = pd.DataFrame(transactions)
        header_df = pd.DataFrame([header_info])
        
        # Calculate summary statistics
        summary = {
            'total_credits': transactions_df[transactions_df['value'] > 0]['value'].sum(),
            'total_debits': transactions_df[transactions_df['value'] < 0]['value'].sum(),
            'total_transactions': len(transactions_df),
            'avg_transaction': transactions_df['value'].mean(),
            'max_credit': transactions_df[transactions_df['value'] > 0]['value'].max(),
            'max_debit': transactions_df[transactions_df['value'] < 0]['value'].min(),
        }
        summary_df = pd.DataFrame([summary])
        
        # Create Excel writer object
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write transactions
            transactions_df.loc[transactions_df["value"] < 0].to_excel(
                writer,
                sheet_name='Transactions',
                index=False
            )

            transactions_df.loc[transactions_df["value"] > 0].to_excel(
                writer,
                sheet_name='Addtions',
                index=False
            )
            
            # Write header information
            header_df.to_excel(
                writer,
                sheet_name='Account Info',
                index=False
            )
            
            # Write summary
            summary_df.to_excel(
                writer,
                sheet_name='Summary',
                index=False
            )
            
            # Auto-adjust columns width
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column = [cell for cell in column]
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

def process_statement():
    """Main function to process the bank statement."""
    if len(argv) < 2:
        raise("Path to input not specified")
        exit(1)

    pdf_path = argv[1]
    date = datetime
    output_path = f"output/output_{date.today().strftime("%Y%m%d")}.xlsx"

    try:
        converter = StatementConverter(pdf_path)
        converter.convert_to_excel(output_path)
        print(f"Successfully converted {pdf_path} to {output_path}")
    except Exception as e:
        print(f"Error processing statement: {str(e)}")
        raise

if __name__ == "__main__":
    process_statement()
