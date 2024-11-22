import os
import csv
from datetime import datetime


def parse_vcf(input_vcf, output_dir):
    """
    Parses a VCF file and stores essential fields, preserving the INFO field intact.

    Args:
        input_vcf (str): Path to the input VCF file.
        output_dir (str): Directory to save processed files.

    Returns:
        str: Path to the folder containing parsed outputs.
    """
    #creatinng timestamped folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = os.path.join(output_dir, timestamp)
    os.makedirs(output_folder, exist_ok=True)

    #output file paths
    parsed_csv = os.path.join(output_folder, 'parsed_variants.csv')
    metadata_txt = os.path.join(output_folder, 'metadata.txt')

    try:
        with open(input_vcf, 'r') as vcf_file:
            reader = vcf_file.readlines()

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

        # PREPARING output CSV
        with open(parsed_csv, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            #4)CSV header
            output_header = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO']
            writer.writerow(output_header)

            #5)parse and write variant data
            for line in data_lines:
                fields = line.strip().split('\t')

                #5a)extract main columns
                chrom, pos, var_id, ref, alt, qual, filter_status, info = (
                    fields[0], fields[1], fields[2], fields[3], fields[4], fields[5], fields[6], fields[info_index]
                )

                # additional: handle multiple ALT alleles (if there's any "C,A" type value)
                alt_alleles = alt.split(',')
                for allele in alt_alleles:
                    #5c)write row to CSV
                    writer.writerow([chrom, pos, var_id, ref, allele, qual, filter_status, info])

    except Exception as e:
        raise RuntimeError(f"Failed to parse VCF file: {e}")

    return output_folder
