import os

class VCFParser:
    def __init__(self, file_path, output_dir="../data/processed"):
        self.file_path = file_path
        self.output_dir = output_dir
        self.metadata = None

    def parse_metadata(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File {self.file_path} not found")

        # extracting metadata only
        self.metadata = self._extract_metadata()

        # save metadata to file
        # comment out later!
        self._save_metadata()
        
        return self.metadata

    def _extract_metadata(self):
        metadata = []
        with open(self.file_path, 'r') as file:
            for line in file:
                if line.startswith("##"):
                    metadata.append(line.strip())
                else:
                    break
        return metadata

# comment out later!, just to show metadata is getting extracted/removed
    def _save_metadata(self):
        os.makedirs(self.output_dir, exist_ok=True)
        metadata_file_path = os.path.join(self.output_dir, "metadata.txt")
        
        with open(metadata_file_path, 'w') as file:
            for line in self.metadata:
                file.write(line + "\n")
        
        print(f"Metadata saved to: {metadata_file_path}")