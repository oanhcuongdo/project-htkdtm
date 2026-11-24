import logging
import os
from typing import List
from ingestion.models import RawTransactionDTO

logger = logging.getLogger(__name__)


class GmailAPICollector:
    """
    Adapter kết nối Google Gmail API sử dụng OAuth2 scope 'https://www.googleapis.com/auth/gmail.readonly'.
    Sử dụng khi triển khai kết nối OAuth2 thay cho App Password IMAP.
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path

    def is_configured(self) -> bool:
        return os.path.exists(self.credentials_path) and os.path.exists(self.token_path)

    def collect(self, query: str = "subject:(biến động số dư OR giao dịch)", max_results: int = 50) -> List[RawTransactionDTO]:
        if not self.is_configured():
            logger.info("Gmail API OAuth2 chưa có credentials.json/token.json; sử dụng IMAP fallback.")
            return []
        # Mở rộng khi cấp Google Cloud OAuth credentials thực tế
        return []
