"""SocketIO event handlers for real-time features."""
import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from .extensions import socketio, db
from .models import TicketComment

logger = logging.getLogger(__name__)

# Track online users: {user_id: sid}
online_users = {}


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        online_users[current_user.id] = request.sid
        # Join personal notification room
        join_room(f'user_{current_user.id}')
        # Teknisi join global room for new ticket alerts
        if current_user.is_teknisi():
            join_room('teknisi_room')
        logger.info(f'User connected: {current_user.username} (sid={request.sid})')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    if current_user.is_authenticated:
        online_users.pop(current_user.id, None)
        logger.info(f'User disconnected: {current_user.username}')


@socketio.on('join_ticket')
def handle_join_ticket(data):
    """Join a ticket room to receive real-time updates."""
    ticket_id = data.get('ticket_id')
    if ticket_id:
        room = f'ticket_{ticket_id}'
        join_room(room)
        logger.debug(f'{current_user.username} joined room {room}')


@socketio.on('leave_ticket')
def handle_leave_ticket(data):
    """Leave a ticket room."""
    ticket_id = data.get('ticket_id')
    if ticket_id:
        room = f'ticket_{ticket_id}'
        leave_room(room)


@socketio.on('send_message')
def handle_send_message(data):
    """Handle chat message: save to DB and broadcast to ticket room."""
    if not current_user.is_authenticated:
        return

    ticket_id = data.get('ticket_id')
    message = data.get('message', '').strip()

    if not ticket_id or not message:
        return

    # Save to database
    comment = TicketComment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        message=message,
        created_at=datetime.now()
    )
    db.session.add(comment)
    db.session.commit()

    # Broadcast to ticket room
    emit('new_message', {
        'id': comment.id,
        'ticket_id': ticket_id,
        'user_id': current_user.id,
        'user_nama': current_user.nama,
        'user_initial': current_user.nama[0].upper(),
        'message': message,
        'time': 'Baru saja',
        'is_own': False  # Client will check this
    }, room=f'ticket_{ticket_id}')

    logger.info(f'Message sent by {current_user.username} in ticket {ticket_id}')


@socketio.on('typing')
def handle_typing(data):
    """Broadcast typing indicator to other users in ticket room."""
    ticket_id = data.get('ticket_id')
    if ticket_id and current_user.is_authenticated:
        emit('user_typing', {
            'user_id': current_user.id,
            'user_nama': current_user.nama,
            'ticket_id': ticket_id
        }, room=f'ticket_{ticket_id}', include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """Broadcast stop typing to other users in ticket room."""
    ticket_id = data.get('ticket_id')
    if ticket_id and current_user.is_authenticated:
        emit('user_stop_typing', {
            'user_id': current_user.id,
            'ticket_id': ticket_id
        }, room=f'ticket_{ticket_id}', include_self=False)


# --- Helper functions for emitting from routes ---

def emit_ticket_notification(user_id, data):
    """Send a notification to a specific user."""
    socketio.emit('notification', data, room=f'user_{user_id}')


def emit_ticket_update(ticket_id, data):
    """Broadcast ticket update to all viewers of that ticket."""
    socketio.emit('ticket_updated', data, room=f'ticket_{ticket_id}')


def emit_dashboard_update():
    """Notify all teknisi to refresh dashboard stats."""
    socketio.emit('dashboard_update', {}, room='teknisi_room')


def emit_new_ticket_alert(ticket_data):
    """Alert all teknisi about a new ticket."""
    socketio.emit('new_ticket', ticket_data, room='teknisi_room')
