from abc import ABC, abstractmethod

class BaseAnnotator(ABC):
    @abstractmethod
    def setup(self):
        """Initialize required resources"""
        pass
        
    @abstractmethod
    def annotate(self, input_file, output_file):
        """Annotate variants and save results"""
        pass
        
    @abstractmethod
    def cleanup(self):
        """Cleanup resources"""
        pass
