# -*- coding:utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, abort, Response, session, flash
import json
import os
import shutil
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
app.secret_key = 'pkc'  # 用于会话管理

# 设置文件路径
JSON_FILE = 'ys.json'
# BG_SOUND_DIR = 'bgSound'  # 背景音文件夹

# 读取 JSON 文件
def read_json_file(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 加载用户数据
def load_users():
    with open('config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['users']

def get_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

userConfig = get_config()
PKC_USER = os.environ.get('PKC_USER')
PKC_PASSWORD = os.environ.get('PKC_PASSWORD')
PKC_VERSION = os.environ.get('PKC_VERSION')
PKC_TITLE = os.environ.get('PKC_TITLE')
PKC_MY = os.environ.get('PKC_MY')

if PKC_USER is None:
    PKC_USER = userConfig['users'][0]['username']
if PKC_PASSWORD is None:
    PKC_PASSWORD = userConfig['users'][0]['password']
if PKC_VERSION is None:
    PKC_VERSION = 'v1.0.1'
if PKC_TITLE is None:
    PKC_TITLE = userConfig['标题']
if PKC_MY is None:
    PKC_MY = userConfig['接口密钥']

# 导出 JSON 文件
@app.route('/ysList')
def printYsList():
    if len(PKC_MY) > 0:
        if request.method == 'GET':
            my = request.args.get('my')
            if my != PKC_MY:
                return "密钥错误！"
        else:
            return "没权限访问"
    # 将数据转换为格式化的 JSON 字符串
    json_data = json.dumps(read_json_file(JSON_FILE), ensure_ascii=False, indent=4)

    # 创建响应对象，设置内容类型为 JSON
    return Response(json_data, mimetype='application/json; charset=utf-8')
# 保存 JSON 文件
def save_json_file(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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
        save_json_file(JSON_FILE, audio_colors)
        return f"分类【{name}】 已添加。"
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
        if new_name != old_name:
            del audio_colors[old_name]
        save_json_file(JSON_FILE, audio_colors)
        return f"分类【{old_name}】 已修改为【{new_name}】。"
    else:
        return f"分类【{old_name}】 不存在。"

# 删除分类
def delete_category(audio_colors, name):
    if name in audio_colors:
        del audio_colors[name]
        save_json_file(JSON_FILE, audio_colors)
        return f"分类【{name}】 已删除。"
    else:
        return f"分类【{name}】 不存在。"

# 管理分类中的 list
def add_to_list(audio_colors, category_name, name, desc, vid, img):
    if category_name in audio_colors:
        if vid_exists(audio_colors, vid):
            return f"音色 ID【{vid}】 已存在。"
        else:
            audio_colors[category_name]['list'].append({
                'name': name,
                'desc': desc,
                'img': img,
                'vid': vid
            })
            save_json_file(JSON_FILE, audio_colors)
            return f"音色【{name}】 已添加到分类【{category_name}】。"
    else:
        return f"分类【{category_name}】 不存在。"

def edit_list_item(audio_colors, category_name, old_name, new_name, desc, vid, img):
    if category_name in audio_colors:
        for i, item in enumerate(audio_colors[category_name]['list']):
            if item['name'] == old_name:
                if item['vid'] != vid and vid_exists(audio_colors, vid):
                    return f"音色 ID【{vid}】 已存在。"
                else:
                    audio_colors[category_name]['list'][i] = {
                        'name': new_name,
                        'desc': desc,
                        'img': img,
                        'vid': vid
                    }
                    save_json_file(JSON_FILE, audio_colors)
                    return f"音色【{old_name}】 已修改为【{new_name}】。"
        return f"音色【{old_name}】 不存在于分类【{category_name}】。"
    else:
        return f"分类【{category_name}】不存在。"

# 删除 list 中的音色
def delete_from_list(audio_colors, category_name, name):
    if category_name in audio_colors:
        audio_colors[category_name]['list'] = [
            item for item in audio_colors[category_name]['list'] if item['name'] != name
        ]
        save_json_file(JSON_FILE, audio_colors)
        return f"音色【{name}】已从分类【{category_name}】删除。"
    else:
        return f"分类【{category_name}】 不存在。"

# 检查音色 ID 是否已存在
def vid_exists(audio_colors, vid):
    for category_data in audio_colors.values():
        for item in category_data['list']:
            if item['vid'] == vid:
                return True
    return False

def backup_json_file(file):
    # 获取当前时间
    backup_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # 创建备份目录
    backup_dir = 'backup'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    # 生成备份文件名
    backup_file = os.path.join(backup_dir, f"{os.path.basename(file)}_{backup_time}.json")
    # 复制文件到备份目录
    shutil.copyfile(file, backup_file)
    return f"备份成功，备份文件名为：{backup_dir}/{file}_{backup_time}.json"

# 导出 JSON 文件
@app.route('/export')
def export_json():
    if 'username' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('index'))
    return send_from_directory(os.path.dirname(JSON_FILE), os.path.basename(JSON_FILE), as_attachment=True)
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('已成功注销！', 'info')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('login.html', titleName=PKC_TITLE, PKC_VERSION=PKC_VERSION)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # users = load_users()
    users = [{"username": PKC_USER, "password": PKC_PASSWORD}]

    # 验证用户
    for user in users:
        if user['username'] == username and user['password'] == password:
            session['username'] = username
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))

    flash('用户名或密码错误！', 'danger')
    return render_template('login.html', titleName=PKC_TITLE, PKC_VERSION=PKC_VERSION)

# 处理表单提交
@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    audio_colors = read_json_file(JSON_FILE)
    response = None
    curtabName = None
    if 'username' not in session:
        flash('请先登录！', 'warning')
        return redirect(url_for('index'))
    # if request.method == 'GET':
    #     # 获取 URL 参数 y 的值
    #     y = request.args.get('y', type=int)
    if request.method == 'POST':
        action = request.form.get('action')

        # 添加分类
        if action == 'add_category':
            name = request.form.get('name')
            token = request.form.get('token')
            sort = request.form.get('sort')
            desc = request.form.get('desc')
            url = request.form.get('url')
            alias = request.form.get('alias')
            type = request.form.get('type')
            curtabName='addCategory'
            response = add_category(audio_colors, name, token, sort, desc, url, alias, type)

        # 修改分类
        elif action == 'edit_category':
            old_name = request.form.get('old_name')
            new_name = request.form.get('new_name')
            token = request.form.get('token')
            sort = request.form.get('sort')
            desc = request.form.get('desc')
            url = request.form.get('url')
            alias = request.form.get('alias')
            type = request.form.get('type')
            response = edit_category(audio_colors, old_name, new_name, token, sort, desc, url, alias, type)
            curtabName='editCategory'

    # 删除分类
        elif action == 'delete_category':
            name = request.form.get('name')
            response = delete_category(audio_colors, name)
            curtabName='deleteCategory'

        # 添加到 list
        elif action == 'add_to_list':
            category_name = request.form.get('category_name')
            name = request.form.get('name')
            desc = request.form.get('desc')
            vid = request.form.get('vid')
            img = request.form.get('img')
            response = add_to_list(audio_colors, category_name, name, desc, vid, img)
            curtabName='addToList'

        # 修改 list 中的音色
        elif action == 'edit_list_item':
            category_name = request.form.get('category_name')
            old_name = request.form.get('old_name')
            new_name = request.form.get('new_name')
            desc = request.form.get('desc')
            vid = request.form.get('vid')
            img = request.form.get('img')
            response = edit_list_item(audio_colors, category_name, old_name, new_name, desc, vid, img)
            curtabName='editListItem'

    # 删除 list 中的音色
        elif action == 'delete_from_list':
            category_name = request.form.get('category_name')
            name = request.form.get('name')
            response = delete_from_list(audio_colors, category_name, name)
            curtabName='deleteFromList'
    # 备份
        elif action == 'backup':
            response = backup_json_file(JSON_FILE)
            curtabName='backup'
    # 导出
        elif action == 'export':
           # 重定向给 当前路由/export
           return redirect(url_for('export_json'))  # 重定向到 export_json 路由
        # 导入
        elif action == 'import':
            if 'import_file' in request.files:
                file = request.files['import_file']
                if file.filename.endswith('.json'):
                    backup_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                    backup_dir = 'backup'
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    # 生成备份文件名
                    backup_file = os.path.join(backup_dir, f"{os.path.basename(JSON_FILE)}_{backup_time}.json")
                    # os.rename(JSON_FILE, backup_file)
                    # 复制文件
                    shutil.copy2(JSON_FILE, backup_file)
                    # 删除原文件
                    os.remove(JSON_FILE)
                    file.save(JSON_FILE)
                    response = f"导入成功，原文件已备份为：{backup_file}"
                else:
                    response = "导入失败，请上传正确的 JSON 文件。"
            else:
                response = "导入失败，请上传文件。"
            curtabName='import'

# 读取所有音色
    audio_colors = read_json_file(JSON_FILE)
    # 获取第一个分类的名称和音色列表
    first_category_name = list(audio_colors.keys())[0] if audio_colors else None
    first_category_audio_colors = audio_colors.get(first_category_name, {}).get('list', [])
    return render_template('index.html',
                       audio_colors=audio_colors,
                       ysCount=len(audio_colors),
                       first_category_name=first_category_name,
                       first_category_audio_colors=first_category_audio_colors,
                       curtabName=curtabName,
                       titleName=PKC_TITLE,
                       PKC_VERSION=PKC_VERSION,
                       PKC_MY=PKC_MY,
                       response=response)  # 将 response 传递到模板


if __name__ == '__main__':
    protValue = userConfig['端口']
    port = protValue if len(protValue) > 0 else "39900"
    app.run(host='0.0.0.0', port=port, debug=False)
