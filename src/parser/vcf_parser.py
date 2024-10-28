import allel
import pandas as pd
import os

class VCFParser:
    def __init__(self, file_path, output_dir="./data/processed"):
        self.file_path = file_path
        self.output_dir = output_dir
        self.metadata = None
        self.variants = None

    def parse(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File {self.file_path} not found")

        # mkdir output directory
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # extracting metadata and variants
        self.metadata = self._extract_metadata()
        self.variants = self._extract_variants()

        # store parsed variants to CSV
        output_path = os.path.join(self.output_dir, "parsed_variants.csv")
        self.variants.to_csv(output_path, index=False)
        print(f"Parsed data has been saved to {output_path}")

        return self.metadata, self.variants

    def _extract_metadata(self):
        metadata = []
        with open(self.file_path, 'r') as file:
            for line in file:
                if line.startswith("##"):
                    metadata.append(line.strip())
                else:
                    break
        return metadata

    def _extract_variants(self):
        callset = allel.read_vcf(self.file_path, fields=['variants/CHROM', 'variants/POS', 
                                                         'variants/ID', 'variants/REF', 
                                                         'variants/ALT', 'variants/QUAL', 
                                                         'variants/FILTER_PASS'])
        
        # flattenin and handle missing data for each field
        def flatten_field(field, default_value=None):
            return [item[0] if isinstance(item, (list, tuple)) and len(item) == 1 else item 
                    for item in callset[field]] if field in callset else [default_value] * len(callset['variants/POS'])

        # creating df with core variant fields
        variants = pd.DataFrame({
            "CHROM": flatten_field('variants/CHROM'),
            "POS": flatten_field('variants/POS'),
            "ID": flatten_field('variants/ID', default_value="."),
            "REF": flatten_field('variants/REF'),
            "ALT": ["|".join(alleles) if isinstance(alleles, (list, tuple)) else alleles 
                    for alleles in callset['variants/ALT']],
            "QUAL": flatten_field('variants/QUAL', default_value="."),
            "FILTER": flatten_field('variants/FILTER_PASS', default_value="PASS"),
        })
        return variants
