#!/usr/bin/env python3
# Test script for multi-currency system

import sys
sys.path.insert(0, '.')

from app import app
from models.db import get_db_connection
from models.db_currencies import get_all_currencies

print('=== Multi-Currency System Test ===')

with app.app_context():
    # Test database connection
    conn = get_db_connection()
    if not conn:
        print('❌ Database connection failed')
        exit(1)

    print('✅ Database connection successful')

    cursor = conn.cursor()

    try:
        # Test currencies table
        currencies = get_all_currencies()
        print(f'✅ Currencies loaded: {len(currencies)} currencies')

        # Test products with currency
        cursor.execute('SELECT COUNT(*) FROM products WHERE currency_id IS NOT NULL')
        products_with_currency = cursor.fetchone()[0]
        print(f'✅ Products with currency: {products_with_currency}')

        # Test tickets with currency
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE currency_id IS NOT NULL')
        tickets_with_currency = cursor.fetchone()[0]
        print(f'✅ Tickets with currency: {tickets_with_currency}')

        # Test products query (same as in routes)
        cursor.execute('SELECT p.*, c.code as currency_code, c.symbol as currency_symbol FROM products p LEFT JOIN currencies c ON p.currency_id = c.currency_id')
        products = cursor.fetchall()
        print(f'✅ Products query successful: {len(products)} products')

        # Test tickets query
        cursor.execute('SELECT t.*, c.code as currency_code, c.symbol as currency_symbol FROM tickets t LEFT JOIN currencies c ON t.currency_id = c.currency_id')
        tickets = cursor.fetchall()
        print(f'✅ Tickets query successful: {len(tickets)} tickets')

        print('')
        print('🎉 All tests passed! Multi-currency system is working correctly.')
        print('')
        print('Available currencies:')
        for currency in currencies:
            status = '(Base)' if currency['is_base'] else '(Active)' if currency['is_active'] else '(Inactive)'
            print(f'  {currency["code"]}: {currency["name"]} {currency["symbol"]} - Rate: {currency["exchange_rate"]} {status}')

    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        conn.close()


