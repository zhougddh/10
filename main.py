# -*- coding:utf-8 -*-
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
import os
import shutil
import datetime
import tempfile
from novai_integration import NovaAI
from api302_integration import API302

app = Flask(__name__)
app.secret_key = 'pkc'  # 用于会话管理

# 设置文件路径
JSON_FILE = os.path.join(os.path.dirname(__file__), 'ys.json')
TOKEN_USAGE_FILE = os.path.join(os.path.dirname(__file__), 'token_usage.json')
NOVAI_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'novai_config.json')
API302_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'api302_config.json')

# 初始化NovaAI实例
nova_ai = NovaAI(NOVAI_CONFIG_FILE)

# 初始化302.AI实例
api302 = API302(API302_CONFIG_FILE)

# 读取 JSON 文件
def read_json_file(file):
    if os.path.exists(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取文件失败: {e}")
            return {}
    return {}

# 保存 JSON 文件
def save_json_file(file, data):
    try:
        # 先写入临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json')
        temp_file_path = temp_file.name
        temp_file.close()
        
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # 然后替换原文件
        if os.path.exists(file):
            os.remove(file)
        shutil.move(temp_file_path, file)
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        # 清理临时文件
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        return False

# 加载用户数据
def load_users():
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['users']
    except Exception as e:
        print(f"加载用户数据失败: {e}")
        return []

def get_config():
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载配置失败: {e}")
        return {}

# 加载token使用情况
def load_token_usage():
    return read_json_file(TOKEN_USAGE_FILE)

# 保存token使用情况
def save_token_usage(data):
    return save_json_file(TOKEN_USAGE_FILE, data)

userConfig = get_config()
PKC_USER = os.environ.get('PKC_USER')
PKC_PASSWORD = os.environ.get('PKC_PASSWORD')
PKC_VERSION = os.environ.get('PKC_VERSION')
PKC_TITLE = os.environ.get('PKC_TITLE')
PKC_MY = os.environ.get('PKC_MY')

if PKC_USER is None:
    PKC_USER = userConfig['users'][0]['username'] if 'users' in userConfig and userConfig['users'] else 'admin'
if PKC_PASSWORD is None:
    PKC_PASSWORD = userConfig['users'][0]['password'] if 'users' in userConfig and userConfig['users'] else 'password'
if PKC_VERSION is None:
    PKC_VERSION = 'v1.0.1'
if PKC_TITLE is None:
    PKC_TITLE = userConfig.get('标题', 'PKC音色管理后台')
if PKC_MY is None:
    PKC_MY = userConfig.get('接口密钥', '')

# 导出 JSON 文件
@app.route('/ysList')
def printYsList():
    if len(PKC_MY) > 0:
        if request.method == 'GET':
            my = request.args.get('my')
            if my != PKC_MY:
                return "密钥错误！"
            
            # 检查token是否已经被使用
            token_usage = load_token_usage()
            client_ip = request.remote_addr
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 检查是否有其他IP正在使用此token
            if PKC_MY in token_usage:
                usage_info = token_usage[PKC_MY]
                last_ip = usage_info['ip']
                last_time = usage_info['time']
                
                # 如果不是同一个IP，拒绝访问
                if last_ip != client_ip:
                    return f"该token已被其他设备使用！上次使用IP: {last_ip}，时间: {last_time}"
            
            # 更新token使用信息
            token_usage[PKC_MY] = {
                'ip': client_ip,
                'time': current_time
            }
            save_token_usage(token_usage)
        else:
            return "没权限访问"
    # 将数据转换为格式化的 JSON 字符串
    json_data = json.dumps(read_json_file(JSON_FILE), ensure_ascii=False, indent=4)

    # 创建响应对象，设置内容类型为 JSON
    return json_data

# 测试路由
@app.route('/')
def index():
    return 'Hello, PKC is working!'

# 登录页面
@app.route('/login')
def login():
    return render_template('login.html', titleName=PKC_TITLE, PKC_VERSION=PKC_VERSION)

# 登录处理
@app.route('/login_post', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    users = load_users()
    
    # 验证用户
    for user in users:
        if user['username'] == username and user['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
    
    flash('用户名或密码错误', 'danger')
    return redirect(url_for('login'))

# 管理后台
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return 'Welcome to dashboard!'

# 退出登录
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# NovaAI API 相关路由

# 设置NovaAI API密钥
@app.route('/novai/set_api_key', methods=['POST'])
def set_novai_api_key():
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({'error': 'API密钥不能为空'}), 400
    
    success = nova_ai.set_api_key(api_key)
    if success:
        return jsonify({'success': True, 'message': 'API密钥设置成功'})
    else:
        return jsonify({'error': 'API密钥设置失败'}), 500

# 获取NovaAI音色列表
@app.route('/novai/voices')
def get_novai_voices():
    if len(PKC_MY) > 0:
        my = request.args.get('my')
        if my != PKC_MY:
            return "密钥错误！"
    
    voices = nova_ai.get_voices()
    return jsonify(voices)

# 上传音色到NovaAI
@app.route('/novai/upload_voice', methods=['POST'])
def upload_novai_voice():
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    if 'audio' not in request.files:
        return jsonify({'error': '没有上传音频文件'}), 400
    
    audio_file = request.files['audio']
    voice_name = request.form.get('name', '未命名音色')
    
    if audio_file.filename == '':
        return jsonify({'error': '文件名不能为空'}), 400
    
    # 保存上传的文件
    temp_file = os.path.join(tempfile.gettempdir(), audio_file.filename)
    audio_file.save(temp_file)
    
    # 上传到NovaAI
    result = nova_ai.upload_voice(temp_file, voice_name)
    
    # 删除临时文件
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    return jsonify(result)

# 使用NovaAI进行语音合成
@app.route('/novai/tts', methods=['POST'])
def novai_tts():
    if len(PKC_MY) > 0:
        my = request.args.get('my')
        if my != PKC_MY:
            return "密钥错误！"
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    text = data.get('text')
    voice_id = data.get('voice')
    
    if not text or not voice_id:
        return jsonify({'error': '文本和音色ID不能为空'}), 400
    
    # 生成语音
    output_file = os.path.join(tempfile.gettempdir(), f"novai_output_{datetime.datetime.now().timestamp()}.mp3")
    success = nova_ai.text_to_speech(text, voice_id, output_file)
    
    if success and os.path.exists(output_file):
        # 读取音频文件并返回
        with open(output_file, 'rb') as f:
            audio_data = f.read()
        
        # 删除临时文件
        os.remove(output_file)
        
        # 返回音频数据
        from flask import send_file
        import io
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg')
    else:
        return jsonify({'error': '语音合成失败'}), 500

# 302.AI API 相关路由

# 设置302.AI API密钥
@app.route('/api302/set_api_key', methods=['POST'])
def set_api302_api_key():
    if 'username' not in session:
        return jsonify({'error': '未登录'}), 401
    
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({'error': 'API密钥不能为空'}), 400
    
    success = api302.set_api_key(api_key)
    if success:
        return jsonify({'success': True, 'message': 'API密钥设置成功'})
    else:
        return jsonify({'error': 'API密钥设置失败'}), 500

# 使用302.AI进行语音合成
@app.route('/api302/tts', methods=['POST'])
def api302_tts():
    if len(PKC_MY) > 0:
        my = request.args.get('my')
        if my != PKC_MY:
            return "密钥错误！"
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    text = data.get('text')
    reference_id = data.get('voice')
    
    if not text or not reference_id:
        return jsonify({'error': '文本和参考音色ID不能为空'}), 400
    
    # 生成语音
    output_file = os.path.join(tempfile.gettempdir(), f"api302_output_{datetime.datetime.now().timestamp()}.mp3")
    success = api302.text_to_speech(text, reference_id, output_file)
    
    if success and os.path.exists(output_file):
        # 读取音频文件并返回
        with open(output_file, 'rb') as f:
            audio_data = f.read()
        
        # 删除临时文件
        os.remove(output_file)
        
        # 返回音频数据
        from flask import send_file
        import io
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg')
    else:
        return jsonify({'error': '语音合成失败'}), 500

# Fish Audio 语音合成路由（使用302.AI）
@app.route('/fish/tts', methods=['POST'])
def fish_tts():
    if len(PKC_MY) > 0:
        my = request.args.get('my')
        if my != PKC_MY:
            return "密钥错误！"
    
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    text = data.get('text')
    reference_id = data.get('voice')
    
    if not text or not reference_id:
        return jsonify({'error': '文本和参考音色ID不能为空'}), 400
    
    # 生成语音（使用302.AI）
    output_file = os.path.join(tempfile.gettempdir(), f"fish_output_{datetime.datetime.now().timestamp()}.mp3")
    success = api302.text_to_speech(text, reference_id, output_file)
    
    if success and os.path.exists(output_file):
        # 读取音频文件并返回
        with open(output_file, 'rb') as f:
            audio_data = f.read()
        
        # 删除临时文件
        os.remove(output_file)
        
        # 返回音频数据
        from flask import send_file
        import io
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg')
    else:
        return jsonify({'error': '语音合成失败'}), 500

if __name__ == '__main__':
    port = '39903'  # 使用不同的端口以避免冲突
    app.run(host='0.0.0.0', port=port, debug=True)
