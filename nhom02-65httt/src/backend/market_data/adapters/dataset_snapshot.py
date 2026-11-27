from pathlib import Path
import pandas as pd
from .base import CompetitorSourceAdapter

class DatasetSnapshotAdapter(CompetitorSourceAdapter):
    """Repeatable local adapter for the supplied CSV snapshot."""
    def __init__(self, csv_path: str | Path, **kwargs):
        super().__init__(min_delay=0, max_delay=0, **kwargs)
        self.csv_path = Path(csv_path)

    def fetch(self, **kwargs) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(self.csv_path)
        return pd.read_csv(self.csv_path)
