# -*- coding:utf-8 -*-
import requests
import json
import os

class NovaAI:
    def __init__(self, config_file='novai_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.api_key = self.config.get('api_key', '')
        self.base_url = self.config.get('base_url', 'https://api.novai.su')
        self.voices_endpoint = self.config.get('voices_endpoint', '/voices')
        self.tts_endpoint = self.config.get('tts_endpoint', '/tts')
        self.upload_endpoint = self.config.get('upload_endpoint', '/upload')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def set_api_key(self, api_key):
        self.api_key = api_key
        self.config['api_key'] = api_key
        self.headers['Authorization'] = f'Bearer {api_key}'
        return self.save_config()
    
    def get_voices(self):
        """获取音色列表"""
        try:
            url = f"{self.base_url}{self.voices_endpoint}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取音色列表失败: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            print(f"获取音色列表异常: {e}")
            return {}
    
    def upload_voice(self, audio_file, voice_name):
        """上传音色"""
        try:
            url = f"{self.base_url}{self.upload_endpoint}"
            files = {'file': open(audio_file, 'rb')}
            data = {'name': voice_name}
            # 上传文件时不需要Content-Type为json
            upload_headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.post(url, headers=upload_headers, files=files, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"上传音色失败: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            print(f"上传音色异常: {e}")
            return {}
    
    def text_to_speech(self, text, voice_id, output_file='output.mp3'):
        """文本转语音"""
        try:
            url = f"{self.base_url}{self.tts_endpoint}"
            data = {
                'text': text,
                'voice': voice_id
            }
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"语音已生成: {output_file}")
                return True
            else:
                print(f"生成语音失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"生成语音异常: {e}")
            return False

if __name__ == '__main__':
    # 测试代码
    nova = NovaAI()
    
    # 设置API密钥
    api_key = input("请输入NovaAI API密钥: ")
    nova.set_api_key(api_key)
    
    # 测试获取音色列表
    print("\n获取音色列表:")
    voices = nova.get_voices()
    print(json.dumps(voices, ensure_ascii=False, indent=2))
    
    # 测试上传音色
    audio_file = input("\n请输入要上传的音频文件路径: ")
    voice_name = input("请输入音色名称: ")
    if audio_file and os.path.exists(audio_file):
        result = nova.upload_voice(audio_file, voice_name)
        print("上传结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 测试文本转语音
    if voices and 'voices' in voices:
        voice_ids = [voice['id'] for voice in voices['voices']]
        if voice_ids:
            print("\n可用的音色ID:", voice_ids)
            selected_voice = input("请选择音色ID: ")
            text = input("请输入要转换的文本: ")
            nova.text_to_speech(text, selected_voice)
