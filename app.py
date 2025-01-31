from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 设置安全的随机密钥

# 数据存储路径
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

# 初始化数据目录和文件
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)

# --------------- 通用函数 ---------------
def load_users():
    """加载所有用户数据"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    """保存用户数据"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def get_current_user():
    """获取当前登录用户"""
    if 'user_id' in session:
        users = load_users()
        for user in users:
            if user['id'] == session['user_id']:
                return user
    return None

# --------------- 路由定义 ---------------
@app.route('/')
def index():
    """主页（需登录）"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('index.html', username=user['username'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()
        if any(u['username'] == username for u in users):
            return render_template('register.html', error='用户名已存在')

        new_user = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': generate_password_hash(password),
            'forms': []
        }
        users.append(new_user)
        save_users(users)

        session['user_id'] = new_user['id']
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        users = load_users()
        user = next((u for u in users if u['username'] == username), None)

        if not user or not check_password_hash(user['password'], password):
            return render_template('login.html', error='用户名或密码错误')

        session['user_id'] = user['id']
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用户退出"""
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/get_data')
def get_data():
    """获取当前用户数据"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401
    return jsonify({'forms': user.get('forms', [])})

@app.route('/add_form', methods=['POST'])
def add_form():
    """新增表单"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401

    form_name = request.json.get('form_name')
    if not form_name:
        return jsonify({'error': '表单名称不能为空'}), 400

    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            u['forms'].append({
                'form_name': form_name,
                'warriors': []
            })
            save_users(users)
            return jsonify({'success': True})
    return jsonify({'error': '用户不存在'}), 404

@app.route('/add_warrior', methods=['POST'])
def add_warrior():
    """新增武将"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401

    data = request.json
    form_name = data.get('form_name')
    warrior_name = data.get('warrior_name')

    if not warrior_name:
        return jsonify({'error': '武将名称不能为空'}), 400

    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            for form in u['forms']:
                if form['form_name'] == form_name:
                    if any(w['warrior_name'] == warrior_name for w in form['warriors']):
                        return jsonify({'error': '武将已存在'}), 400
                    form['warriors'].append({
                        'warrior_name': warrior_name,
                        'wins': 0,
                        'losses': 0,
                        'win_rate': '0%'
                    })
                    save_users(users)
                    return jsonify({'success': True})
    return jsonify({'error': '表单不存在'}), 404

@app.route('/update_record', methods=['POST'])
def update_record():
    """更新胜负场次"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401

    data = request.json
    form_name = data.get('form_name')
    warrior_name = data.get('warrior_name')
    field = data.get('field')
    value = max(0, int(data.get('value')))  # 确保非负

    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            for form in u['forms']:
                if form['form_name'] == form_name:
                    for warrior in form['warriors']:
                        if warrior['warrior_name'] == warrior_name:
                            warrior[field] = value
                            total = warrior['wins'] + warrior['losses']
                            warrior['win_rate'] = f"{round((warrior['wins'] / total) * 100, 2)}%" if total > 0 else '0%'
                            save_users(users)
                            return jsonify({'success': True})
    return jsonify({'error': '数据未找到'}), 404

@app.route('/delete_form', methods=['POST'])
def delete_form():
    """删除表单"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401

    form_name = request.json.get('form_name')
    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            u['forms'] = [f for f in u['forms'] if f['form_name'] != form_name]
            save_users(users)
            return jsonify({'success': True})
    return jsonify({'error': '操作失败'}), 400

@app.route('/delete_warrior', methods=['POST'])
def delete_warrior():
    """删除武将"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未登录'}), 401

    data = request.json
    form_name = data.get('form_name')
    warrior_name = data.get('warrior_name')

    users = load_users()
    for u in users:
        if u['id'] == user['id']:
            for form in u['forms']:
                if form['form_name'] == form_name:
                    form['warriors'] = [w for w in form['warriors'] if w['warrior_name'] != warrior_name]
                    save_users(users)
                    return jsonify({'success': True})
    return jsonify({'error': '数据未找到'}), 404

if __name__ == '__main__':
    app.run(debug=True)