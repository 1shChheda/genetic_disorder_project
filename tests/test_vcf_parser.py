import os
import pytest
from src.parser.vcf_parser import VCFParser

def test_parse_metadata():
    test_file = os.path.join(os.path.dirname(__file__), '../data/raw/sample.vcf')
    parser = VCFParser(test_file)
    
    # parse metadata
    metadata = parser.parse_metadata()
    
    # checkin metadata is non-empty and a list
    assert isinstance(metadata, list) and len(metadata) > 0
    assert all(line.startswith("##") for line in metadata)
    
# c0mment out later! (saving metadata file)
    # check metadata file
    output_path = os.path.join(parser.output_dir, "metadata.txt")
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as file:
        saved_metadata = [line.strip() for line in file.readlines()]
    
    # comparing the in-memory metadata with the saved file content
    assert saved_metadata == metadata