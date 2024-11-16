import os
import csv
from datetime import datetime

def parse_vcf(input_vcf, output_dir, retain_info_fields=None):
    """
    Parses a VCF file and generates timestamped outputs.

    Args:
        input_vcf (str): Path to the input VCF file.
        output_dir (str): Directory to store processed files.
        retain_info_fields (list, optional): List of `INFO` fields to retain.
            Defaults to ['AF', 'AC', 'DP', 'Impact'].
    """
    if retain_info_fields is None:
        retain_info_fields = ['AF', 'AC', 'DP', 'Impact']

    #creatinng timestamped folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, timestamp)
    os.makedirs(output_path, exist_ok=True)

    #output file paths
    csv_path = os.path.join(output_path, 'parsed_variants.csv')
    metadata_path = os.path.join(output_path, 'metadata.txt')

    with open(input_vcf, 'r') as vcf_file, open(csv_path, 'w', newline='') as csv_file:
        reader = vcf_file.readlines()
        writer = csv.writer(csv_file)

        #1)metadata extraction
        metadata = [line for line in reader if line.startswith('##')]
        data_lines = [line for line in reader if not line.startswith('#')]

        #2)save metadata
        with open(metadata_path, 'w') as meta_file:
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
            chrom = fields[0]
            pos = fields[1]
            var_id = fields[2]
            ref = fields[3]
            alt = fields[4]
            qual = fields[5]
            filter_status = fields[6]
            info = fields[info_index]

            #skipping rows with missing or low-quality data
            # if qual == '.' or filter_status != 'PASS':
            #     continue

            #5b)arse INFO fields
            info_dict = dict(item.split('=') for item in info.split(';') if '=' in item)
            parsed_info = [info_dict.get(field, '.') for field in retain_info_fields]

            #5c)write row to CSV
            writer.writerow([chrom, pos, var_id, ref, alt, qual, filter_status] + parsed_info)

    print(f"Output files saved in: {output_path}")
