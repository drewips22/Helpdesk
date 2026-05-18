from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from .extensions import socketio

@socketio.on('connect')
def handle_connect():
    pass

@socketio.on('disconnect')
def handle_disconnect():
    pass

@socketio.on('join_ticket')
def on_join_ticket(data):
    ticket_id = data.get('ticket_id')
    if ticket_id:
        room = f"ticket_{ticket_id}"
        join_room(room)

@socketio.on('send_message')
def on_send_message(data):
    ticket_id = data.get('ticket_id')
    message = data.get('message')
    if ticket_id and message:
        room = f"ticket_{ticket_id}"
        # Broadcast the message to the room
        # Usually you would save to database here first
        emit('new_message', {
            'user_id': current_user.id if current_user.is_authenticated else 0,
            'user_nama': current_user.nama if current_user.is_authenticated else 'Anonim',
            'user_initial': current_user.nama[0].upper() if current_user.is_authenticated else 'A',
            'message': message,
            'time': 'Baru saja'
        }, room=room)

@socketio.on('typing')
def on_typing(data):
    ticket_id = data.get('ticket_id')
    if ticket_id and current_user.is_authenticated:
        room = f"ticket_{ticket_id}"
        emit('user_typing', {
            'user_nama': current_user.nama
        }, room=room, include_self=False)

@socketio.on('stop_typing')
def on_stop_typing(data):
    ticket_id = data.get('ticket_id')
    if ticket_id:
        room = f"ticket_{ticket_id}"
        emit('user_stop_typing', {}, room=room, include_self=False)
