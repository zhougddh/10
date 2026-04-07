# -*- coding:utf-8 -*-
"""
上传自定义音色到302.AI
"""
import requests
import json
import os

def upload_voice(api_key, audio_file):
    """上传音色到302.AI"""
    # 尝试不同的接口路径
    urls = [
        "https://api.302.ai/fish-audio/v1/voices",
        "https://api.302.ai/fish-audio/v1/model",
        "https://api.302.ai/fish-audio/v1/voices/create"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    for url in urls:
        print(f"尝试上传到: {url}")
        try:
            with open(audio_file, "rb") as f:
                files = {
                    "file": (os.path.basename(audio_file), f, "audio/mp3")
                }
                data = {
                    "name": "自定义音色"
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                print(f"上传响应状态码: {response.status_code}")
                print(f"上传响应内容: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("上传成功！")
                    print(f"参考音色ID: {result.get('reference_id')}")
                    return result.get('reference_id')
                else:
                    print(f"上传失败: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"上传异常: {e}")
    
    return None

if __name__ == "__main__":
    api_key = "sk-B4V1pwfJF1OzG8PLGEuvo6hvBNonBrb8oWRtHVIUxsRYdPVD"
    audio_file = "custom_voice.mp3"
    
    if audio_file and os.path.exists(audio_file):
        print(f"上传文件: {audio_file}")
        print(f"文件大小: {os.path.getsize(audio_file)} bytes")
        reference_id = upload_voice(api_key, audio_file)
        if reference_id:
            print(f"\n请将以下ID配置到应用中:")
            print(f"参考音色ID: {reference_id}")
    else:
        print("文件不存在！")
