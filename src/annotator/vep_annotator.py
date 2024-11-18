import os
import csv

def annotate_variants(input_csv, output_csv):
    """
    Annotates the parsed_variants.csv with database information.

    Args:
        input_csv (str): Path to the parsed variants CSV.
        output_csv (str): Path to save the annotated CSV.
    """
    # NOTE: dummy placeholder logic for now, to integrate databases like ClinVar, gnomAD etc.
    with open(input_csv, 'r') as in_file, open(output_csv, 'w', newline='') as out_file:
        reader = csv.DictReader(in_file)
        writer = csv.DictWriter(out_file, fieldnames=reader.fieldnames + ['Annotation'])
        writer.writeheader()

        for row in reader:
            # adding dummy annotation
            row['Annotation'] = "ExampleAnnotation"
            writer.writerow(row)
