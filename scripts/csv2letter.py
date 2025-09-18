import csv
import os
from collections import defaultdict

def process_csv_to_reviewer_files(csv_filename, output_dir="reviewer_files"):
    """
    Process a CSV file and create individual text files for each reviewer
    with comments formatted as points and responses as replies.
    
    Args:
        csv_filename (str): Path to the input CSV file
        output_dir (str): Directory to save the output files
    """
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Dictionary to store data for each reviewer
    reviewer_data = defaultdict(list)
    
    try:
        # Read the CSV file
        with open(csv_filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            print(f"CSV columns: {reader.fieldnames}")
            
            # Check if required columns exist
            required_columns = ['\ufeffComment', 'Reviewer', 'Final Response']
            missing_columns = [col for col in required_columns if col not in reader.fieldnames]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Process each row
            for row in reader:
                reviewer = row['Reviewer'].strip()
                comment = row['\ufeffComment'].strip()
                final_response = row['Final Response'].strip()
                
                # Skip rows with empty reviewer or comment
                if not reviewer or not comment:
                    continue
                
                # Store the data
                reviewer_data[reviewer].append({
                    'comment': comment,
                    'response': final_response
                })
    
    except FileNotFoundError:
        print(f"Error: File '{csv_filename}' not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    # Generate text files for each reviewer
    for reviewer, entries in reviewer_data.items():
        # Clean reviewer name for filename
        safe_filename = "".join(c for c in reviewer if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_filename = safe_filename.replace(' ', '_')
        filename = os.path.join(output_dir, f"{safe_filename}.txt")
        
        try:
            with open(filename, 'w', encoding='utf-8') as outfile:
                
                for _i, entry in enumerate(entries, 1):
                    # Write the comment as a point
                    outfile.write(f"\\begin{{point}}\n")
                    outfile.write(f"{entry['comment']}\n")
                    outfile.write(f"\\end{{point}}\n\n")
                    
                    # Write the response as a reply (only if response exists)
                    if entry['response']:
                        outfile.write(f"\\begin{{reply}}\n")
                        outfile.write(f"{entry['response']}\n")
                        outfile.write(f"\\end{{reply}}\n\n")
                    
            print(f"Created file: {filename}")
            
        except Exception as e:
            print(f"Error writing file for reviewer '{reviewer}': {e}")

def main():
    # Example usage
    csv_file = "input.csv"  # Replace with your CSV file path
    
    # Optional: specify output directory
    output_directory = "reviewer_files"
    
    print(f"\nProcessing CSV file: {csv_file}")
    print(f"Output directory: {output_directory}")
    print("-" * 40)
    
    process_csv_to_reviewer_files(csv_file, output_directory)
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()