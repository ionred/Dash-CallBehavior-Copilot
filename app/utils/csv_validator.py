"""CSV validation utilities."""
import csv
import io


class CSVValidator:
    """Validates CSV files for account number uploads."""
    
    @staticmethod
    def validate_csv_content(file_content):
        """
        Validate CSV file content for account numbers.
        
        Args:
            file_content: String content of CSV file
        
        Returns:
            Tuple of (valid, account_numbers, error_message)
            - valid: Boolean indicating if validation passed
            - account_numbers: List of valid account numbers
            - error_message: Error message if validation failed, None otherwise
        """
        try:
            # Parse CSV content
            csv_file = io.StringIO(file_content)
            reader = csv.reader(csv_file)
            
            # Read all rows
            rows = list(reader)
            
            if not rows:
                return False, [], "CSV file is empty."
            
            # Check if we have exactly one column
            first_row_cols = len(rows[0]) if rows else 0
            if first_row_cols == 0:
                return False, [], "CSV file has no columns."
            
            if first_row_cols > 1:
                return False, [], f"CSV file should have exactly one column, but has {first_row_cols} columns."
            
            # Check if first row is a header (contains non-digit characters)
            skip_first = False
            if rows[0][0].strip() and not rows[0][0].strip().isdigit():
                skip_first = True
            
            # Validate account numbers
            account_numbers = []
            start_row = 1 if skip_first else 0
            
            for idx, row in enumerate(rows[start_row:], start=start_row + 1):
                if not row or not row[0].strip():
                    # Skip empty rows
                    continue
                
                account_num = row[0].strip()
                
                # Check if account number contains only digits
                if not account_num.isdigit():
                    return False, [], f"Row {idx}: Account number '{account_num}' contains non-digit characters."
                
                # Check length (max 15 characters based on schema)
                if len(account_num) > 15:
                    return False, [], f"Row {idx}: Account number '{account_num}' exceeds maximum length of 15 characters."
                
                account_numbers.append(account_num)
            
            if not account_numbers:
                return False, [], "No valid account numbers found in CSV file."
            
            # Check for duplicates
            unique_accounts = set(account_numbers)
            if len(unique_accounts) < len(account_numbers):
                duplicate_count = len(account_numbers) - len(unique_accounts)
                return False, [], f"CSV file contains {duplicate_count} duplicate account number(s). Please remove duplicates."
            
            return True, account_numbers, None
            
        except Exception as e:
            return False, [], f"Error parsing CSV file: {str(e)}"
