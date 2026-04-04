# -*- coding:utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, abort, Response, session, flash
import json
import os
import shutil
from werkzeug.utils import secure_filename
import datetime
import tempfile

app = Flask(__name__)
app.secret_key = 'pkc'  # 用于会话管理

# 设置文件路径
JSON_FILE = os.path.join(os.path.dirname(__file__), 'ys.json')
TOKEN_USAGE_FILE = os.path.join(os.path.dirname(__file__), 'token_usage.json')
# BG_SOUND_DIR = 'bgSound'  # 背景音文件夹

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
    return Response(json_data, mimetype='application/json; charset=utf-8')

# 添加分类
def add_category(audio_colors, name, token, sort, desc, url, alias, type):
    if name not in audio_colors:
        audio_colors[name] = {
            'token': token,
            'sort': sort,
            'desc': desc,
            'url': url,
            'alias': alias,
            'type': type,
            'list': []
        }
        if save_json_file(JSON_FILE, audio_colors):
            return f"分类【{name}】 已添加。"
        else:
            return f"分类【{name}】 添加失败，保存文件出错。"
    else:
        return f"分类【{name}】 已存在。"

# 修改分类
def edit_category(audio_colors, old_name, new_name, token, sort, desc, url, alias, type):
    if old_name in audio_colors:
        audio_colors[new_name] = {
            'token': token,
            'sort': sort,
            'desc': desc,
            'url': url,
            'alias': alias,
            'type': type,
            'list': audio_colors[old_name]['list']
        }
        del audio_colors[old_name]
        if save_json_file(JSON_FILE, audio_colors):
            return f"分类【{old_name}】 已修改为 【{new_name}】。"
        else:
            return f"分类【{old_name}】 修改失败，保存文件出错。"
    else:
        return f"分类【{old_name}】 不存在。"

# 删除分类
def delete_category(audio_colors, name):
    if name in audio_colors:
        del audio_colors[name]
        if save_json_file(JSON_FILE, audio_colors):
            return f"分类【{name}】 已删除。"
        else:
            return f"分类【{name}】 删除失败，保存文件出错。"
    else:
        return f"分类【{name}】 不存在。"

# 添加音色到分类
def add_to_list(audio_colors, category_name, name, desc, vid, img):
    if category_name in audio_colors:
        # 检查是否已存在同名音色
        for item in audio_colors[category_name]['list']:
            if item['name'] == name:
                return f"音色【{name}】 已存在。"
        # 添加新音色
        audio_colors[category_name]['list'].append({
            'name': name,
            'desc': desc,
            'vid': vid,
            'img': img
        })
        if save_json_file(JSON_FILE, audio_colors):
            return f"音色【{name}】 已添加到分类 【{category_name}】。"
        else:
            return f"音色【{name}】 添加失败，保存文件出错。"
    else:
        return f"分类【{category_name}】 不存在。"

# 修改分类中的音色
def edit_list_item(audio_colors, category_name, old_name, new_name, desc, vid, img):
    if category_name in audio_colors:
        for item in audio_colors[category_name]['list']:
            if item['name'] == old_name:
                item['name'] = new_name
                item['desc'] = desc
                item['vid'] = vid
                item['img'] = img
                if save_json_file(JSON_FILE, audio_colors):
                    return f"音色【{old_name}】 已修改为 【{new_name}】。"
                else:
                    return f"音色【{old_name}】 修改失败，保存文件出错。"
        return f"音色【{old_name}】 不存在。"
    else:
        return f"分类【{category_name}】 不存在。"

# 从分类中删除音色
def delete_from_list(audio_colors, category_name, name):
    if category_name in audio_colors:
        for item in audio_colors[category_name]['list']:
            if item['name'] == name:
                audio_colors[category_name]['list'].remove(item)
                if save_json_file(JSON_FILE, audio_colors):
                    return f"音色【{name}】 已删除。"
                else:
                    return f"音色【{name}】 删除失败，保存文件出错。"
        return f"音色【{name}】 不存在。"
    else:
        return f"分类【{category_name}】 不存在。"

# 登录页面
@app.route('/')
def login():
    return render_template('login.html', titleName=PKC_TITLE, PKC_VERSION=PKC_VERSION)

# 登录处理
@app.route('/login', methods=['POST'])
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
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    audio_colors = read_json_file(JSON_FILE)
    ysCount = len(audio_colors)
    curtabName = None
    response = None
    first_category_name = None
    first_category_audio_colors = []
    
    # 获取第一个分类的名称和音色列表
    if audio_colors:
        first_category_name = next(iter(audio_colors))
        if 'list' in audio_colors[first_category_name]:
            first_category_audio_colors = audio_colors[first_category_name]['list']
    
    if request.method == 'POST':
        action = request.form.get('action')
        curtabName = action
        
        if action == 'add_category':
            name = request.form.get('name')
            token = request.form.get('token', '')
            sort = request.form.get('sort', 0)
            desc = request.form.get('desc', '')
            url = request.form.get('url', '')
            alias = request.form.get('alias', '')
            type = request.form.get('type', 'custom')
            response = add_category(audio_colors, name, token, sort, desc, url, alias, type)
        
        elif action == 'edit_category':
            old_name = request.form.get('old_name')
            new_name = request.form.get('new_name')
            token = request.form.get('token', '')
            sort = request.form.get('sort', 0)
            desc = request.form.get('desc', '')
            url = request.form.get('url', '')
            alias = request.form.get('alias', '')
            type = request.form.get('type', 'custom')
            response = edit_category(audio_colors, old_name, new_name, token, sort, desc, url, alias, type)
        
        elif action == 'delete_category':
            name = request.form.get('name')
            response = delete_category(audio_colors, name)
        
        elif action == 'add_to_list':
            category_name = request.form.get('category_name')
            name = request.form.get('name')
            desc = request.form.get('desc', '')
            vid = request.form.get('vid')
            img = request.form.get('img', '')
            response = add_to_list(audio_colors, category_name, name, desc, vid, img)
        
        elif action == 'edit_list_item':
            category_name = request.form.get('category_name')
            old_name = request.form.get('old_name')
            new_name = request.form.get('new_name')
            desc = request.form.get('desc', '')
            vid = request.form.get('vid')
            img = request.form.get('img', '')
            response = edit_list_item(audio_colors, category_name, old_name, new_name, desc, vid, img)
        
        elif action == 'delete_from_list':
            category_name = request.form.get('category_name')
            name = request.form.get('name')
            response = delete_from_list(audio_colors, category_name, name)
        
        elif action == 'backup':
            # 备份数据
            try:
                backup_dir = os.path.join(os.path.dirname(__file__), 'backup')
                os.makedirs(backup_dir, exist_ok=True)
                backup_file = os.path.join(backup_dir, f'ys_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                shutil.copy2(JSON_FILE, backup_file)
                response = f"数据已备份到：{backup_file}"
            except Exception as e:
                response = f"备份失败：{str(e)}"
        
        elif action == 'import':
            # 导入数据
            if 'import_file' not in request.files:
                response = "请选择要导入的文件"
            else:
                file = request.files['import_file']
                if file.filename == '':
                    response = "请选择要导入的文件"
                elif file and file.filename.endswith('.json'):
                    try:
                        imported_data = json.load(file)
                        if save_json_file(JSON_FILE, imported_data):
                            response = "数据导入成功"
                        else:
                            response = "数据导入失败，保存文件出错"
                    except Exception as e:
                        response = f"导入失败：{str(e)}"
                else:
                    response = "请选择JSON格式的文件"
        
        elif action == 'export':
            # 导出数据
            try:
                export_dir = os.path.join(os.path.dirname(__file__), 'export')
                os.makedirs(export_dir, exist_ok=True)
                export_file = os.path.join(export_dir, f'ys_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                shutil.copy2(JSON_FILE, export_file)
                response = f"数据已导出到：{export_file}"
            except Exception as e:
                response = f"导出失败：{str(e)}"
        
        elif action == 'clear_token_usage':
            # 清除token使用记录
            if save_token_usage({}):
                response = "Token使用记录已清除"
            else:
                response = "清除Token使用记录失败"
    
    return render_template('index.html', titleName=PKC_TITLE, PKC_VERSION=PKC_VERSION, PKC_MY=PKC_MY, ysCount=ysCount, first_category_name=first_category_name, first_category_audio_colors=first_category_audio_colors, response=response, curtabName=curtabName)

# 退出登录
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = userConfig.get('端口', '39900')
    app.run(host='0.0.0.0', port=port, debug=False)