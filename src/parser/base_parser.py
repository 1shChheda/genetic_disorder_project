from abc import ABC, abstractmethod

class BaseParser(ABC):
    """Abstract base class for VCF parsers"""
    
    @abstractmethod
    def parse(self, input_vcf, output_dir):
        # Parse VCF file and save processed output
        pass
