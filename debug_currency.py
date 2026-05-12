#!/usr/bin/env python3
# Debug currency switching

import sys
sys.path.insert(0, '.')

from app import app
from utils.currency_service import currency_service
from models.db_currencies import get_all_currencies

print('=== Currency Switching Debug ===')

with app.app_context():
    # Test getting currencies
    currencies = get_all_currencies(active_only=True)
    print(f'Available currencies: {len(currencies)}')
    for currency in currencies:
        print(f'  {currency["code"]}: {currency["name"]} ({currency["symbol"]}) - Rate: {currency["exchange_rate"]}')

    print()

    # Test format_currency_price function
    from flask import session

    # Simulate session with no currency set
    session.clear()
    user_currency = currency_service.get_user_currency(session)
    print(f'Default user currency: {user_currency["code"]} ({user_currency["symbol"]})')

    # Test price formatting
    test_price = 100.0
    formatted = currency_service.format_price(test_price, 'USD')
    print(f'Price in USD: {formatted}')

    formatted_eur = currency_service.format_price(test_price, 'EUR')
    print(f'Price in EUR: {formatted_eur}')

    # Test conversion
    converted_price = currency_service.convert_price(test_price, 'USD', 'EUR')
    print(f'100 USD in EUR: {converted_price}')

    # Test display price function
    price_info = currency_service.get_display_price(test_price, 'USD', 'EUR')
    print(f"Display price (USD to EUR): {price_info['amount']}, {price_info['formatted']}")

    print()
    print('=== Session Test ===')

    # Test setting currency in session
    success = currency_service.set_user_currency(session, 'EUR')
    print(f'Set currency to EUR: {success}')

    user_currency_after = currency_service.get_user_currency(session)
    print(f'User currency after setting: {user_currency_after["code"]}')

    # Test format_currency_price with session
    from flask import g
    app.preprocess_request()

    # Test the context processor function
    utility_functions = app.context_processor(lambda: None)()['utility_processor']()
    format_func = utility_functions['format_currency_price']

    result = format_func(test_price, None, 'USD')  # No user currency specified, should use session
    print(f'Format currency price result: {result}')

