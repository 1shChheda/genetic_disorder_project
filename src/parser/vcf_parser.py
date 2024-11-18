import os
import csv
from datetime import datetime

def parse_vcf(input_vcf, output_dir, retain_info_fields=None):
    """
    Parses a VCF file and generates a CSV with necessary variant fields.

    Args:
        input_vcf (str): Path to the input VCF file.
        output_dir (str): Directory to save processed files.
        retain_info_fields (list, optional): List of `INFO` fields to retain.

    Returns:
        str: Path to the folder containing parsed outputs.
    """
    if retain_info_fields is None:
        retain_info_fields = ['AF', 'AC', 'DP', 'Impact']

    #creatinng timestamped folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(output_dir, timestamp)
    os.makedirs(output_folder, exist_ok=True)

    #output file paths
    parsed_csv = os.path.join(output_folder, 'parsed_variants.csv')
    metadata_txt = os.path.join(output_folder, 'metadata.txt')

    with open(input_vcf, 'r') as vcf_file, open(parsed_csv, 'w', newline='') as csv_file:
        reader = vcf_file.readlines()
        writer = csv.writer(csv_file)

        #1)metadata extraction
        metadata = [line for line in reader if line.startswith('##')]
        data_lines = [line for line in reader if not line.startswith('#')]

        #2)save metadata
        with open(metadata_txt, 'w') as meta_file:
            meta_file.writelines(metadata)

        #3)extract header and write new CSV header
        header_line = next(line for line in reader if line.startswith('#CHROM'))
        header = header_line.strip().split('\t')
        info_index = header.index('INFO')

        #4)CSV header
        output_header = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER'] + retain_info_fields
        writer.writerow(output_header)

        #5)parse and write variant data
        for line in data_lines:
            fields = line.strip().split('\t')

            #5a)extract main columns
            chrom, pos, var_id, ref, alt, qual, filter_status, info = (
                fields[0], fields[1], fields[2], fields[3], fields[4], fields[5], fields[6], fields[info_index]
            )

            #skipping rows with missing or low-quality data
            # if qual == '.' or filter_status != 'PASS':
            #     continue

            #5b)arse INFO fields
            info_dict = dict(item.split('=') for item in info.split(';') if '=' in item)
            parsed_info = [info_dict.get(field, '.') for field in retain_info_fields]

            #5c)write row to CSV
            writer.writerow([chrom, pos, var_id, ref, alt, qual, filter_status] + parsed_info)

    return output_folder
