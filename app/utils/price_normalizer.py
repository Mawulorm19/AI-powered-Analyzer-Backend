"""
Price Analyzer API - Price Normalization Utilities
Clean and normalize prices from various formats to floats.
"""
import re
from typing import Optional, Tuple


# Currency symbols and their ISO codes
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "C$": "CAD",
    "A$": "AUD",
    "₽": "RUB",
    "R$": "BRL",
    "₩": "KRW",
}

# Exchange rates to USD (simplified - in production, use a real-time API)
EXCHANGE_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "JPY": 0.0067,
    "INR": 0.012,
    "CAD": 0.74,
    "AUD": 0.65,
    "RUB": 0.011,
    "BRL": 0.20,
    "KRW": 0.00075,
}


def clean_price_string(price_str: str) -> str:
    """
    Clean a price string by removing common formatting artifacts.
    
    Args:
        price_str: Raw price string (e.g., "$1,299.99", "€ 99,50")
        
    Returns:
        Cleaned string ready for parsing
    """
    if not price_str:
        return ""
    
    # Remove common prefixes/suffixes
    cleaned = price_str.strip()
    cleaned = re.sub(r'^(from|starting at|price:|now)\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*(per unit|each|/ea)$', '', cleaned, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned


def detect_currency(price_str: str) -> Tuple[str, str]:
    """
    Detect currency from price string.
    
    Args:
        price_str: Price string with currency symbol
        
    Returns:
        Tuple of (currency_code, cleaned_price_string)
    """
    cleaned = clean_price_string(price_str)
    
    # Check for currency symbols
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in cleaned:
            cleaned = cleaned.replace(symbol, "").strip()
            return code, cleaned
    
    # Check for ISO codes
    iso_pattern = r'^(USD|EUR|GBP|JPY|INR|CAD|AUD|RUB|BRL|KRW)\s*'
    match = re.match(iso_pattern, cleaned, re.IGNORECASE)
    if match:
        code = match.group(1).upper()
        cleaned = cleaned[len(match.group(0)):].strip()
        return code, cleaned
    
    # Default to USD
    return "USD", cleaned


def parse_numeric_value(value_str: str) -> Optional[float]:
    """
    Parse a numeric value from string, handling various formats.
    
    Args:
        value_str: String containing numeric value
        
    Returns:
        Float value or None if parsing fails
    """
    if not value_str:
        return None
    
    # Remove all non-numeric characters except . and ,
    cleaned = re.sub(r'[^\d.,\-]', '', value_str)
    
    if not cleaned:
        return None
    
    # Handle negative values
    is_negative = cleaned.startswith('-')
    cleaned = cleaned.lstrip('-')
    
    # Determine decimal separator
    # European format: 1.234,56 or 1234,56
    # US format: 1,234.56 or 1234.56
    
    comma_count = cleaned.count(',')
    dot_count = cleaned.count('.')
    
    if comma_count == 0 and dot_count == 0:
        # Just digits
        try:
            result = float(cleaned)
            return -result if is_negative else result
        except ValueError:
            return None
    
    if comma_count == 0 and dot_count == 1:
        # US format with decimal: 1234.56
        try:
            result = float(cleaned)
            return -result if is_negative else result
        except ValueError:
            return None
    
    if comma_count == 1 and dot_count == 0:
        # Could be European decimal (99,50) or US thousands (1,234)
        parts = cleaned.split(',')
        if len(parts[1]) == 2:
            # Likely European decimal
            cleaned = cleaned.replace(',', '.')
        else:
            # Likely US thousands separator
            cleaned = cleaned.replace(',', '')
        
        try:
            result = float(cleaned)
            return -result if is_negative else result
        except ValueError:
            return None
    
    if dot_count >= 1 and comma_count >= 1:
        # Mixed format - determine by position
        last_dot = cleaned.rfind('.')
        last_comma = cleaned.rfind(',')
        
        if last_dot > last_comma:
            # US format: dots are decimal, commas are thousands
            cleaned = cleaned.replace(',', '')
        else:
            # European format: commas are decimal, dots are thousands
            cleaned = cleaned.replace('.', '').replace(',', '.')
        
        try:
            result = float(cleaned)
            return -result if is_negative else result
        except ValueError:
            return None
    
    # Multiple of same separator - assume thousands
    if comma_count > 1:
        cleaned = cleaned.replace(',', '')
    if dot_count > 1:
        cleaned = cleaned.replace('.', '')
    
    try:
        result = float(cleaned)
        return -result if is_negative else result
    except ValueError:
        return None


def normalize_price(
    price_str: str,
    target_currency: str = "USD"
) -> Tuple[Optional[float], str]:
    """
    Normalize a price string to a float value in the target currency.
    
    Args:
        price_str: Raw price string from any format
        target_currency: Target currency code (default USD)
        
    Returns:
        Tuple of (normalized_price, detected_currency)
    """
    if not price_str:
        return None, "USD"
    
    # Detect and extract currency
    source_currency, cleaned = detect_currency(price_str)
    
    # Parse numeric value
    value = parse_numeric_value(cleaned)
    
    if value is None:
        return None, source_currency
    
    # Convert to target currency
    if source_currency != target_currency:
        source_rate = EXCHANGE_RATES_TO_USD.get(source_currency, 1.0)
        target_rate = EXCHANGE_RATES_TO_USD.get(target_currency, 1.0)
        
        # Convert through USD
        usd_value = value * source_rate
        value = usd_value / target_rate
    
    # Round to 2 decimal places
    value = round(value, 2)
    
    return value, source_currency


def extract_price_range(price_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract price range from strings like "$10 - $20" or "10.00 to 20.00".
    
    Args:
        price_str: Price string potentially containing a range
        
    Returns:
        Tuple of (min_price, max_price)
    """
    if not price_str:
        return None, None
    
    # Check for range patterns
    range_patterns = [
        r'(.+?)\s*[-–—]\s*(.+)',  # $10 - $20
        r'(.+?)\s+to\s+(.+)',      # $10 to $20
        r'(.+?)\s+~\s+(.+)',       # $10 ~ $20
    ]
    
    for pattern in range_patterns:
        match = re.match(pattern, price_str, re.IGNORECASE)
        if match:
            min_price, _ = normalize_price(match.group(1))
            max_price, _ = normalize_price(match.group(2))
            return min_price, max_price
    
    # Single price
    price, _ = normalize_price(price_str)
    return price, price


def calculate_discount_percentage(
    original_price: float,
    current_price: float
) -> float:
    """
    Calculate discount percentage.
    
    Args:
        original_price: Original/list price
        current_price: Current/sale price
        
    Returns:
        Discount percentage (0-100)
    """
    if original_price <= 0 or current_price < 0:
        return 0.0
    
    if current_price >= original_price:
        return 0.0
    
    discount = ((original_price - current_price) / original_price) * 100
    return round(discount, 1)


def format_price(price: float, currency: str = "USD") -> str:
    """
    Format a price for display.
    
    Args:
        price: Numeric price value
        currency: Currency code
        
    Returns:
        Formatted price string
    """
    symbol_map = {v: k for k, v in CURRENCY_SYMBOLS.items()}
    symbol = symbol_map.get(currency, f"{currency} ")
    
    # Format with thousands separator
    if currency in ["JPY", "KRW"]:
        # No decimals for these currencies
        formatted = f"{int(price):,}"
    else:
        formatted = f"{price:,.2f}"
    
    return f"{symbol}{formatted}"
