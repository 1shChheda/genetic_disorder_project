import os
import pytest
import pandas as pd
from src.parser.vcf_parser import VCFParser

def test_parse_vcf():
    test_file = os.path.join(os.path.dirname(__file__), '../data/raw/sample.vcf')
    parser = VCFParser(test_file)
    
    # parse the file (metadata + variants)
    metadata, variants = parser.parse()
    
    # checkin metadata is non-empty and a list
    assert isinstance(metadata, list) and len(metadata) > 0
    
    # checking variants df
    assert isinstance(variants, pd.DataFrame)
    assert not variants.empty
    assert set(["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER"]).issubset(variants.columns)
