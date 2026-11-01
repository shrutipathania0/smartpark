import re

class PlateValidator:
    """
    Validates and normalizes Indian vehicle registration plates.
    Supports standard state formats (e.g. DL01AB1234, MH12DE5678),
    Bharat Series (e.g. 22BH1234AA), and vintage formats.
    """

    VALID_STATE_CODES = {
        "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DN", "DL",
        "GA", "GJ", "HR", "HP", "JK", "JH", "KA", "KL", "LA", "LD",
        "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PY", "PB", "RJ",
        "SK", "TN", "TS", "TR", "UP", "UK", "UA", "WB", "BH"
    }

    # Number-to-letter mapping for positions where letters are expected
    NUM_TO_CHAR = {
        '0': 'O',
        '1': 'I',
        '2': 'Z',
        '4': 'A',
        '5': 'S',
        '6': 'G',
        '8': 'B'
    }

    # Letter-to-number mapping for positions where digits are expected
    CHAR_TO_NUM = {
        'O': '0',
        'D': '0',
        'Q': '0',
        'I': '1',
        'L': '1',
        'Z': '2',
        'A': '4',
        'S': '5',
        'G': '6',
        'B': '8'
    }

    @classmethod
    def clean_text(cls, raw_text: str) -> str:
        """Removes all whitespace, hyphens, dots, and special symbols; converts to uppercase."""
        if not raw_text:
            return ""
        # Remove IND country code prefix if separated
        text = raw_text.strip().upper()
        text = re.sub(r'[^A-Z0-9]', '', text)
        if text.startswith("IND") and len(text) > 7:
            # Often 'IND' prefix appears on HSRP plates
            text = text[3:]
        return text

    @classmethod
    def normalize_indian_plate(cls, raw_text: str) -> tuple[str, bool, str]:
        """
        Normalizes OCR text into standard Indian registration format using contextual character correction.
        Returns: (normalized_text, is_valid, format_type)
        """
        clean = cls.clean_text(raw_text)
        if not clean or len(clean) < 6:
            return clean, False, "UNKNOWN"

        # Check Bharat (BH) Series: YY BH NNNN XX (e.g. 22BH1234AA)
        if len(clean) in [9, 10] and ("BH" in clean[:4] or clean[2:4] == "8H"):
            normalized_bh = cls._normalize_bh_format(clean)
            if normalized_bh:
                return normalized_bh, True, "BH_SERIES"

        # Standard Indian Format: SS NN [LL / LLL] NNNN (total 9-10 chars)
        # e.g., MH12DE1433, DL01AB1234, KA05G1234
        if 8 <= len(clean) <= 11:
            normalized_std = cls._normalize_standard_format(clean)
            if normalized_std:
                return normalized_std, True, "STANDARD"

        # Vintage / 2-letter format: SS L NNNN or SS LL NNNN (e.g., DL A 1234)
        if 6 <= len(clean) <= 8:
            normalized_vintage = cls._normalize_vintage_format(clean)
            if normalized_vintage:
                return normalized_vintage, True, "VINTAGE"

        return clean, False, "UNVALIDATED"

    @classmethod
    def _normalize_standard_format(cls, text: str) -> str:
        """Applies positional character correction for Standard Format: SS NN [LL] NNNN"""
        chars = list(text)
        n = len(chars)

        # 1. First 2 characters must be State Code letters
        for i in range(min(2, n)):
            if chars[i] in cls.NUM_TO_CHAR:
                chars[i] = cls.NUM_TO_CHAR[chars[i]]

        state_code = "".join(chars[:2])
        if state_code not in cls.VALID_STATE_CODES:
            # Try specific common state misreads e.g., 0L -> DL, D1 -> DL
            if state_code.startswith("0") or state_code.startswith("O"):
                chars[0] = "D"
            if state_code.endswith("1") or state_code.endswith("I"):
                chars[1] = "L"
            state_code = "".join(chars[:2])

        # 2. Next 2 characters must be RTO digits
        for i in range(2, min(4, n)):
            if chars[i] in cls.CHAR_TO_NUM:
                chars[i] = cls.CHAR_TO_NUM[chars[i]]

        # 3. Last 4 characters must be 4 registration digits
        for i in range(max(4, n - 4), n):
            if chars[i] in cls.CHAR_TO_NUM:
                chars[i] = cls.CHAR_TO_NUM[chars[i]]

        # 4. Middle characters (between position 4 and n-4) must be series letters
        for i in range(4, n - 4):
            if chars[i] in cls.NUM_TO_CHAR:
                chars[i] = cls.NUM_TO_CHAR[chars[i]]

        candidate = "".join(chars)
        # Verify with regex
        pattern = r'^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$'
        if re.match(pattern, candidate):
            return candidate
        return ""

    @classmethod
    def _normalize_bh_format(cls, text: str) -> str:
        """Applies positional character correction for Bharat Series: YY BH NNNN XX"""
        chars = list(text)
        n = len(chars)
        # First 2: Year digits
        for i in range(2):
            if chars[i] in cls.CHAR_TO_NUM:
                chars[i] = cls.CHAR_TO_NUM[chars[i]]
        # Next 2: "BH"
        chars[2] = "B"
        chars[3] = "H"
        # Next 4: Digits
        for i in range(4, 8):
            if i < n and chars[i] in cls.CHAR_TO_NUM:
                chars[i] = cls.CHAR_TO_NUM[chars[i]]
        # Last 1-2: Letters
        for i in range(8, n):
            if chars[i] in cls.NUM_TO_CHAR:
                chars[i] = cls.NUM_TO_CHAR[chars[i]]

        candidate = "".join(chars)
        if re.match(r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$', candidate):
            return candidate
        return ""

    @classmethod
    def _normalize_vintage_format(cls, text: str) -> str:
        chars = list(text)
        n = len(chars)
        # First 2 letters
        for i in range(2):
            if chars[i] in cls.NUM_TO_CHAR:
                chars[i] = cls.NUM_TO_CHAR[chars[i]]
        # Middle 1-2 letters
        for i in range(2, n - 4):
            if chars[i] in cls.NUM_TO_CHAR:
                chars[i] = cls.NUM_TO_CHAR[chars[i]]
        # Last 4 digits
        for i in range(n - 4, n):
            if chars[i] in cls.CHAR_TO_NUM:
                chars[i] = cls.CHAR_TO_NUM[chars[i]]

        candidate = "".join(chars)
        if re.match(r'^[A-Z]{2}[A-Z]{1,2}[0-9]{4}$', candidate):
            return candidate
        return ""

