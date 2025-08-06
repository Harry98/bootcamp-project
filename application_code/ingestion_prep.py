import os
import csv
from pathlib import Path

# Input and output folders
input_folder = Path(__file__).parent / "ingestion_docs"
output_folder = input_folder.parent / "output_docs"
output_csv_filename = 'output.csv'

# Ensure output directory exists
os.makedirs(output_folder, exist_ok=True)

# Path to output CSV file
output_csv_path = os.path.join(output_folder, output_csv_filename)

# Gather all .txt files in the input folder
txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]

# Write to CSV
with open(output_csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['title', 'text'])  # Header

    for filename in txt_files:
        filepath = os.path.join(input_folder, filename)
        with open(filepath, mode='r', encoding='utf-8') as file:
            text = file.read().strip()
            title = os.path.splitext(filename)[0]
            writer.writerow([title, text])

print(f"CSV file created at: {output_csv_path} with {len(txt_files)} .txt files.")

from datasets import load_dataset, DatasetDict
from huggingface_hub import HfApi

# Step 1: Load your CSV as Hugging Face Dataset
dataset = load_dataset('csv', data_files=output_csv_path)

# Step 2: Push to Hugging Face
dataset.push_to_hub("ksh01/vector-bootcamp-confluence-dataset")
