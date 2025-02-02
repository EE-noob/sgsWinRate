from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# 存储武将胜率数据
stats = {}

@app.route('/')
def index():
    return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>三国杀胜率记录</title>
        </head>
        <body>
            <h1>三国杀胜率记录</h1>
            <input id="generalName" placeholder="输入武将名">
            <button onclick="addWin()">增加胜场</button>
            <button onclick="addLoss()">增加败场</button>
            <p id="result"></p>

            <script>
                function addWin() {
                    const name = document.getElementById('generalName').value;
                    fetch(`/api/add_win`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name })
                    })
                    .then(response => response.json())
                    .then(data => document.getElementById('result').textContent = data.message);
                }

                function addLoss() {
                    const name = document.getElementById('generalName').value;
                    fetch(`/api/add_loss`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name })
                    })
                    .then(response => response.json())
                    .then(data => document.getElementById('result').textContent = data.message);
                }
            </script>
        </body>
        </html>
    '''

@app.route('/api/add_win', methods=['POST'])
def add_win():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"message": "请输入武将名"}), 400

    stats.setdefault(name, {'wins': 0, 'losses': 0})
    stats[name]['wins'] += 1
    return jsonify({"message": f"武将 {name} 的胜场: {stats[name]['wins']}"})

@app.route('/api/add_loss', methods=['POST'])
def add_loss():
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"message": "请输入武将名"}), 400

    stats.setdefault(name, {'wins': 0, 'losses': 0})
    stats[name]['losses'] += 1
    return jsonify({"message": f"武将 {name} 的败场: {stats[name]['losses']}"})

if __name__ == '__main__':
    app.run(debug=True)
