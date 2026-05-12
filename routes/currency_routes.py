from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db_currencies import (
    get_all_currencies,
    get_currency_by_id,
    create_currency,
    update_currency,
    delete_currency,
    get_base_currency
)
from utils.currency_service import currency_service
from config.config import Config

currency_bp = Blueprint('currency', __name__, url_prefix='/admin/currencies')

@currency_bp.route('/')
def currencies():
    """List all currencies for admin"""
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    currencies = get_all_currencies(active_only=False)
    base_currency = get_base_currency()

    return render_template('admin/currencies.html',
                         currencies=currencies,
                         base_currency=base_currency)

@currency_bp.route('/add', methods=['GET', 'POST'])
def add_currency():
    """Add new currency"""
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        symbol = request.form.get('symbol')
        exchange_rate = request.form.get('exchange_rate')
        is_active = request.form.get('is_active') == 'on'
        is_base = request.form.get('is_base') == 'on'

        # Validate required fields
        if not all([name, code, symbol, exchange_rate]):
            flash('All fields are required.', 'error')
            return redirect(url_for('currency.add_currency'))

        try:
            exchange_rate = float(exchange_rate)
            if exchange_rate <= 0:
                raise ValueError("Exchange rate must be positive")
        except ValueError:
            flash('Invalid exchange rate. Must be a positive number.', 'error')
            return redirect(url_for('currency.add_currency'))

        # Validate code format (typically 3 letters)
        if len(code) != 3 or not code.isalpha():
            flash('Currency code must be exactly 3 letters.', 'error')
            return redirect(url_for('currency.add_currency'))

        # Check if code already exists
        existing = [c for c in get_all_currencies(active_only=False) if c['code'].upper() == code.upper()]
        if existing:
            flash('Currency code already exists.', 'error')
            return redirect(url_for('currency.add_currency'))

        if create_currency(name, code.upper(), symbol, exchange_rate, is_active, is_base):
            flash('Currency added successfully.', 'success')
            return redirect(url_for('currency.currencies'))
        else:
            flash('Failed to add currency.', 'error')

    return render_template('admin/currency_form.html', currency=None, action='add')

@currency_bp.route('/edit/<int:currency_id>', methods=['GET', 'POST'])
def edit_currency(currency_id):
    """Edit existing currency"""
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    currency = get_currency_by_id(currency_id)
    if not currency:
        flash('Currency not found.', 'error')
        return redirect(url_for('currency.currencies'))

    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        symbol = request.form.get('symbol')
        exchange_rate = request.form.get('exchange_rate')
        is_active = request.form.get('is_active') == 'on'
        is_base = request.form.get('is_base') == 'on'

        # Validate required fields
        if not all([name, code, symbol, exchange_rate]):
            flash('All fields are required.', 'error')
            return redirect(url_for('currency.edit_currency', currency_id=currency_id))

        try:
            exchange_rate = float(exchange_rate)
            if exchange_rate <= 0:
                raise ValueError("Exchange rate must be positive")
        except ValueError:
            flash('Invalid exchange rate. Must be a positive number.', 'error')
            return redirect(url_for('currency.edit_currency', currency_id=currency_id))

        # Validate code format
        if len(code) != 3 or not code.isalpha():
            flash('Currency code must be exactly 3 letters.', 'error')
            return redirect(url_for('currency.edit_currency', currency_id=currency_id))

        # Check if code already exists (excluding current currency)
        existing = [c for c in get_all_currencies(active_only=False)
                   if c['code'].upper() == code.upper() and c['currency_id'] != currency_id]
        if existing:
            flash('Currency code already exists.', 'error')
            return redirect(url_for('currency.edit_currency', currency_id=currency_id))

        if update_currency(currency_id, name, code.upper(), symbol, exchange_rate, is_active, is_base):
            flash('Currency updated successfully.', 'success')
            return redirect(url_for('currency.currencies'))
        else:
            flash('Failed to update currency.', 'error')

    return render_template('admin/currency_form.html', currency=currency, action='edit')

@currency_bp.route('/delete/<int:currency_id>', methods=['POST'])
def delete_currency_route(currency_id):
    """Delete currency"""
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    currency = get_currency_by_id(currency_id)
    if not currency:
        flash('Currency not found.', 'error')
        return redirect(url_for('currency.currencies'))

    # Prevent deleting base currency
    if currency['is_base']:
        flash('Cannot delete base currency.', 'error')
        return redirect(url_for('currency.currencies'))

    if delete_currency(currency_id):
        flash('Currency deleted successfully.', 'success')
    else:
        flash('Failed to delete currency. It may be referenced by products or orders.', 'error')

    return redirect(url_for('currency.currencies'))

@currency_bp.route('/set-base/<int:currency_id>', methods=['POST'])
def set_base_currency(currency_id):
    """Set currency as base currency"""
    if not session.get('is_admin'):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    currency = get_currency_by_id(currency_id)
    if not currency:
        flash('Currency not found.', 'error')
        return redirect(url_for('currency.currencies'))

    if update_currency(currency_id, currency['name'], currency['code'], currency['symbol'],
                      currency['exchange_rate'], currency['is_active'], True):
        flash(f'{currency["name"]} set as base currency.', 'success')
    else:
        flash('Failed to set base currency.', 'error')

    return redirect(url_for('currency.currencies'))


