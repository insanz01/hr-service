from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
from database import init_db, get_db_connection
from models import User, Todo

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'message': 'Selamat datang di Flask API Minimalis',
        'version': '1.0.0',
        'endpoints': {
            'users': '/api/users',
            'todos': '/api/todos',
            'user_detail': '/api/users/<id>',
            'todo_detail': '/api/todos/<id>'
        }
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT * FROM users').fetchall()
        conn.close()

        result = []
        for user in users:
            result.append({
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'created_at': user['created_at']
            })

        return jsonify({'users': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()

        if not data or not 'name' in data or not 'email' in data:
            return jsonify({'error': 'Name dan email harus diisi'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            (data['name'], data['email'])
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'id': user_id,
            'name': data['name'],
            'email': data['email'],
            'message': 'User berhasil dibuat'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        if user is None:
            return jsonify({'error': 'User tidak ditemukan'}), 404

        return jsonify({
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'created_at': user['created_at']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Data harus disediakan'}), 400

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if user is None:
            conn.close()
            return jsonify({'error': 'User tidak ditemukan'}), 404

        name = data.get('name', user['name'])
        email = data.get('email', user['email'])

        conn.execute(
            'UPDATE users SET name = ?, email = ? WHERE id = ?',
            (name, email, user_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            'id': user_id,
            'name': name,
            'email': email,
            'message': 'User berhasil diupdate'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if user is None:
            conn.close()
            return jsonify({'error': 'User tidak ditemukan'}), 404

        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'User berhasil dihapus'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos', methods=['GET'])
def get_todos():
    try:
        user_id = request.args.get('user_id')
        conn = get_db_connection()

        if user_id:
            todos = conn.execute('SELECT * FROM todos WHERE user_id = ?', (user_id,)).fetchall()
        else:
            todos = conn.execute('SELECT * FROM todos').fetchall()

        conn.close()

        result = []
        for todo in todos:
            result.append({
                'id': todo['id'],
                'title': todo['title'],
                'description': todo['description'],
                'completed': bool(todo['completed']),
                'user_id': todo['user_id'],
                'created_at': todo['created_at']
            })

        return jsonify({'todos': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos', methods=['POST'])
def create_todo():
    try:
        data = request.get_json()

        if not data or not 'title' in data or not 'user_id' in data:
            return jsonify({'error': 'Title dan user_id harus diisi'}), 400

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (data['user_id'],)).fetchone()

        if user is None:
            conn.close()
            return jsonify({'error': 'User tidak ditemukan'}), 404

        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO todos (title, description, user_id, completed) VALUES (?, ?, ?, ?)',
            (data['title'], data.get('description', ''), data['user_id'], False)
        )
        conn.commit()
        todo_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'id': todo_id,
            'title': data['title'],
            'description': data.get('description', ''),
            'completed': False,
            'user_id': data['user_id'],
            'message': 'Todo berhasil dibuat'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    try:
        data = request.get_json()

        conn = get_db_connection()
        todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()

        if todo is None:
            conn.close()
            return jsonify({'error': 'Todo tidak ditemukan'}), 404

        title = data.get('title', todo['title'])
        description = data.get('description', todo['description'])
        completed = data.get('completed', todo['completed'])

        conn.execute(
            'UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?',
            (title, description, completed, todo_id)
        )
        conn.commit()
        conn.close()

        return jsonify({
            'id': todo_id,
            'title': title,
            'description': description,
            'completed': bool(completed),
            'user_id': todo['user_id'],
            'message': 'Todo berhasil diupdate'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        conn = get_db_connection()
        todo = conn.execute('SELECT * FROM todos WHERE id = ?', (todo_id,)).fetchone()

        if todo is None:
            conn.close()
            return jsonify({'error': 'Todo tidak ditemukan'}), 404

        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Todo berhasil dihapus'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint tidak ditemukan'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Terjadi kesalahan internal'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)