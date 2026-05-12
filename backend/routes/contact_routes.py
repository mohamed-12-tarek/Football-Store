import re
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from models.db_messages import (
    save_user_message,
    get_all_messages,
    get_message_by_id,
    update_message_response,
)
from utils.email_utils import send_email

contact_bp = Blueprint('contact_bp', __name__)


def _get_cart_count():
    cart = session.get('cart', {})
    return sum(item['quantity'] for item in cart.values())


def _get_today_hours():
    today = datetime.now()
    return f"Today ({today.strftime('%A')}): 9 AM - 6 PM"


def _build_response_email(message, response_text):
    return (
        f"Hi {message['name']},\n\n"
        "Thanks for contacting Football Store support. "
        "A member of our admin team has replied to your message.\n\n"
        f"Subject: {message['subject']}\n"
        "----------------------------------------\n"
        f"Your original message:\n{message['message']}\n"
        "----------------------------------------\n\n"
        "Our response:\n"
        f"{response_text}\n\n"
        "If you have any further questions, just reply to this email.\n\n"
        "Best regards,\n"
        "Football Store Support Team"
    )


@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not all([name, email, subject, message]):
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('contact_bp.contact'))

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            flash('Please provide a valid email address.', 'error')
            return redirect(url_for('contact_bp.contact'))

        try:
            save_user_message(name, email, subject, message)
            flash('Thanks for reaching out! We will get back to you soon.', 'success')
        except Exception as exc:
            flash(f'Unable to send message: {exc}', 'error')

        return redirect(url_for('contact_bp.contact'))

    return render_template(
        'contact.html',
        cart_count=_get_cart_count(),
        today_hours=_get_today_hours(),
    )


@contact_bp.route('/admin/messages')
def admin_messages():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        flash('Access denied - Admin only area.', 'error')
        return redirect(url_for('index'))

    messages = get_all_messages()
    return render_template(
        'admin/messages.html',
        messages=messages,
        cart_count=_get_cart_count(),
    )


@contact_bp.route('/admin/messages/<int:message_id>', methods=['GET', 'POST'])
def admin_message_detail(message_id):
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    if not session.get('is_admin'):
        flash('Access denied - Admin only area.', 'error')
        return redirect(url_for('index'))

    message = get_message_by_id(message_id)
    if not message:
        flash('Message not found.', 'error')
        return redirect(url_for('contact_bp.admin_messages'))

    if request.method == 'POST':
        response_text = request.form.get('response', '').strip()
        status = request.form.get('status', 'Replied')

        if not response_text:
            flash('Response cannot be empty.', 'error')
            return redirect(url_for('contact_bp.admin_message_detail', message_id=message_id))

        try:
            update_message_response(message_id, response_text, status)
            flash('Response saved successfully.', 'success')
            email_subject = f"Re: {message['subject']} - Football Store Support"
            email_body = _build_response_email(message, response_text)
            sent, error = send_email(message['email'], email_subject, email_body)
            if not sent:
                flash(f'Response saved but email notification failed: {error}', 'warning')
        except Exception as exc:
            flash(f'Unable to update response: {exc}', 'error')

        return redirect(url_for('contact_bp.admin_message_detail', message_id=message_id))

    return render_template(
        'admin/message_detail.html',
        message=message,
        cart_count=_get_cart_count(),
    )

