# -*- coding:utf-8 -*-
import requests
import json
import os

class API302:
    def __init__(self, config_file='api302_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.api_key = self.config.get('api_key', '')
        self.base_url = self.config.get('base_url', 'https://api.302.ai')
        self.tts_endpoint = self.config.get('tts_endpoint', '/fish-audio/v1/tts')
        self.model = self.config.get('model', 'speech-1.5')
        self.response_format = self.config.get('response_format', 'url')
        self.format = self.config.get('format', 'mp3')
        self.mp3_bitrate = self.config.get('mp3_bitrate', 64)
        self.latency = self.config.get('latency', 'normal')
        self.normalize = self.config.get('normalize', True)
        self.chunk_length = self.config.get('chunk_length', 200)
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
    
    def text_to_speech(self, text, reference_id, output_file='output.mp3'):
        """文本转语音"""
        try:
            url = f"{self.base_url}{self.tts_endpoint}"
            data = {
                'text': text,
                'reference_id': reference_id,
                'model': self.model,
                'response_format': self.response_format,
                'format': self.format,
                'mp3_bitrate': self.mp3_bitrate,
                'latency': self.latency,
                'normalize': self.normalize,
                'chunk_length': self.chunk_length
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                
                if self.response_format == 'url':
                    # 如果返回URL，下载音频文件
                    audio_url = result.get('url')
                    if audio_url:
                        audio_response = requests.get(audio_url)
                        if audio_response.status_code == 200:
                            with open(output_file, 'wb') as f:
                                f.write(audio_response.content)
                            print(f"语音已生成: {output_file}")
                            return True
                        else:
                            print(f"下载音频失败: {audio_response.status_code}")
                            return False
                    else:
                        print("响应中没有音频URL")
                        return False
                else:
                    # 如果返回原始数据，直接保存
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
    api302 = API302()
    
    # 设置API密钥
    api_key = input("请输入302.AI API密钥: ")
    api302.set_api_key(api_key)
    
    # 测试文本转语音
    reference_id = input("请输入参考音色ID: ")
    text = input("请输入要转换的文本: ")
    
    if reference_id and text:
        success = api302.text_to_speech(text, reference_id)
        if success:
            print("语音生成成功！")
        else:
            print("语音生成失败！")
