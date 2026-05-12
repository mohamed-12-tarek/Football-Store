from models.db_currencies import get_currency_by_code, get_base_currency, get_currency_by_id
import decimal
from decimal import Decimal, ROUND_HALF_UP

class CurrencyService:
    """Service for handling currency conversion and formatting"""

    @staticmethod
    def convert_price(base_price, from_currency_code, to_currency_code):
        """
        Convert a price from one currency to another

        Args:
            base_price (float): Price in base currency units
            from_currency_code (str): Source currency code (e.g., 'USD')
            to_currency_code (str): Target currency code (e.g., 'EUR')

        Returns:
            float: Converted price, or None if conversion fails
        """
        if base_price is None:
            return 0.0

        amount = float(base_price)

        base_currency = get_base_currency()
        default_rate = 1.0
        if base_currency and base_currency.get('exchange_rate'):
            try:
                default_rate = float(base_currency['exchange_rate'])
            except (TypeError, ValueError):
                default_rate = 1.0

        def _rate_for(code):
            if not code:
                return default_rate
            currency = get_currency_by_code(code)
            if currency and currency.get('exchange_rate'):
                try:
                    rate = float(currency['exchange_rate'])
                    if rate > 0:
                        return rate
                except (TypeError, ValueError):
                    pass
            return default_rate

        from_rate = _rate_for(from_currency_code)
        to_rate = _rate_for(to_currency_code)

        if from_rate <= 0:
            from_rate = default_rate or 1.0
        if to_rate <= 0:
            to_rate = default_rate or 1.0

        # Convert amounts relative to a shared reference so that weaker currencies
        # (smaller exchange rates) always produce smaller converted prices.
        converted_price = (amount / from_rate) * to_rate
        return converted_price

    @staticmethod
    def format_price(price, currency_code, decimals=2):
        """
        Format a price with EGP currency symbol

        Args:
            price (float): Price amount
            currency_code (str): Currency code (will always use EGP)
            decimals (int): Number of decimal places

        Returns:
            str: Formatted price string (e.g., 'EGP29.99', 'EGP19.99')
        """
        # Always use EGP
        egp_currency = get_currency_by_code('EGP')
        safe_price = float(price or 0)
        
        if not egp_currency:
            # Fallback if EGP doesn't exist
            symbol = currency_code if currency_code else 'EGP'
            return f"{symbol}{safe_price:.{decimals}f}"

        # Round to specified decimal places
        rounded_price = CurrencyService.round_price(safe_price, decimals)

        # Format with EGP symbol
        symbol = egp_currency.get('symbol', 'EGP')
        return f"{symbol}{rounded_price:.{decimals}f}"

    @staticmethod
    def round_price(price, decimals=2):
        """
        Round a price to specified decimal places

        Args:
            price (float): Price to round
            decimals (int): Number of decimal places

        Returns:
            float: Rounded price
        """
        decimal_price = Decimal(str(price))
        return float(decimal_price.quantize(Decimal('0.' + '0' * decimals), rounding=ROUND_HALF_UP))

    @staticmethod
    def get_user_currency(session):
        """
        Always return EGP currency

        Args:
            session: Flask session object (can be None)

        Returns:
            dict: EGP currency information
        """
        # Always return EGP
        egp_currency = get_currency_by_code('EGP')
        if egp_currency:
            return egp_currency
        
        # Fallback if EGP doesn't exist
        base_currency = get_base_currency()
        if base_currency:
            return base_currency
        
        # Last resort fallback
        return {'code': 'EGP', 'symbol': 'EGP', 'exchange_rate': 1.0, 'is_base': True}

    @staticmethod
    def set_user_currency(session, currency_code):
        """
        Set the user's selected currency in session

        Args:
            session: Flask session object
            currency_code (str): Currency code to set

        Returns:
            bool: True if currency was set successfully
        """
        currency = get_currency_by_code(currency_code)
        if currency:
            session['currency_code'] = currency_code
            return True
        return False

    @staticmethod
    def get_display_price(product_price, product_currency_code, user_currency_code):
        """
        Get the price to display for a product in user's currency

        Args:
            product_price (float): Product price in its original currency
            product_currency_code (str): Product's currency code
            user_currency_code (str): User's selected currency code

        Returns:
            dict: {'amount': float, 'formatted': str, 'symbol': str, 'currency_code': str}
        """
        base_currency = get_base_currency()
        base_code = base_currency['code'] if base_currency else None

        from_code = product_currency_code or base_code or user_currency_code
        to_code = user_currency_code or base_code or from_code

        converted_price = CurrencyService.convert_price(
            product_price,
            from_code,
            to_code
        )

        formatted_price = CurrencyService.format_price(converted_price, to_code)
        currency = get_currency_by_code(to_code) or base_currency
        symbol = currency['symbol'] if currency else '$'

        return {
            'amount': converted_price,
            'formatted': formatted_price,
            'symbol': symbol,
            'currency_code': to_code
        }

    @staticmethod
    def calculate_cart_total(cart_items, user_currency_code):
        """
        Calculate cart total in user's currency

        Args:
            cart_items: List of cart items with price and quantity
            user_currency_code (str): User's currency code

        Returns:
            tuple: (total_in_base, total_converted, formatted_total)
        """
        total_in_base = 0
        base_currency = get_base_currency()
        base_code = base_currency['code'] if base_currency else user_currency_code

        for item in cart_items:
            # Convert item price to base currency first
            source_code = item.get('currency_code') or base_code
            item_base_price = CurrencyService.convert_price(
                item.get('price'),
                source_code,
                base_code
            )
            total_in_base += item_base_price * item.get('quantity', 1)

        # Convert total to user's currency
        total_converted = CurrencyService.convert_price(
            total_in_base,
            base_code,
            user_currency_code
        )
        formatted_total = CurrencyService.format_price(total_converted, user_currency_code)
        return total_in_base, total_converted, formatted_total

# Global instance for easy access
currency_service = CurrencyService()
