from .vcb_parser import VCBEmailParser
from .mbbank_parser import MBBankEmailParser
from .techcom_parser import TechcombankEmailParser
from .momo_parser import MoMoEmailParser

ALL_EMAIL_PARSERS = [
    VCBEmailParser(),
    MBBankEmailParser(),
    TechcombankEmailParser(),
    MoMoEmailParser(),
]


def parse_bank_email(sender: str, subject: str, body_text: str):
    """Tự động chọn parser phù hợp theo ngân hàng/ví điện tử."""
    for parser in ALL_EMAIL_PARSERS:
        if parser.can_parse(sender, subject, body_text):
            return parser.parse(sender, subject, body_text)
    return None
