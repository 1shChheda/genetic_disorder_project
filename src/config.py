import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '../data')

# VCF file paths
RAW_VCF_PATH = os.path.join(DATA_DIR, 'raw')
PROCESSED_VCF_PATH = os.path.join(DATA_DIR, 'processed')