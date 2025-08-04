import requests
import json
import os
import time
from datetime import datetime
import urllib3
import sys

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log_message(message):
    """打印日志消息到控制台"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_usernames_from_api():
    """从API获取用户名数据"""
    try:
        log_message("正在从API获取用户名数据...")
        response = requests.get("http://81.70.150.62:3000/api/usernames", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("success"):
            usernames = data.get("data", [])
            log_message(f"成功获取到 {len(usernames)} 个用户名")
            return usernames
        else:
            log_message("API返回失败状态")
            return []
    except requests.exceptions.RequestException as e:
        log_message(f"API请求失败: {str(e)}")
        return []
    except Exception as e:
        log_message(f"获取用户名数据时出错: {str(e)}")
        return []

def load_client_username_file(file_path):
    """加载client_username.json文件"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        else:
            return []
    except Exception as e:
        log_message(f"加载client_username文件失败: {str(e)}")
        return []

def save_client_username_file(file_path, data):
    """保存数据到client_username.json文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log_message(f"已保存 {len(data)} 个用户名到 {file_path}")
        return True
    except Exception as e:
        log_message(f"保存client_username文件失败: {str(e)}")
        return False

def update_client_username_data(api_usernames, file_path):
    """更新client_username数据"""
    existing_data = load_client_username_file(file_path)
    
    max_number = 0
    if existing_data:
        max_number = max([item.get("number", 0) for item in existing_data])
    
    log_message(f"当前文件中最大编号: {max_number}")
    
    new_data = []
    for user in api_usernames:
        if user.get("number", 0) > max_number:
            new_data.append({
                "number": user.get("number"),
                "username": user.get("username")
            })
    
    if new_data:
        new_data.sort(key=lambda x: x.get("number", 0))
        if save_client_username_file(file_path, new_data):
            log_message(f"发现 {len(new_data)} 个新用户名，已覆盖保存")
            return new_data
    else:
        log_message("没有新的用户名数据需要添加")
    
    return []

def send_claim_request(username, cookie):
    """发送涨分请求"""
    try:
        url = "https://addplus.org/api/trpc/users.claimPoints?batch=1"
        
        headers = {
            "Host": "addplus.org",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Windows\"",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
            "trpc-accept": "application/jsonl",
            "content-type": "application/json",
            "x-trpc-source": "nextjs-react",
            "sec-ch-ua-mobile": "?0",
            "Accept": "*/*",
            "Origin": "https://addplus.org",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": f"https://addplus.org/boost/{username}",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie": cookie
        }
        
        payload = {
            "0": {
                "json": {
                    "username": username
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30, verify=False)
        
        if response.status_code == 200:
            log_message(f"✅ {username} - 涨分成功")
            return True
        else:
            log_message(f"❌ {username} - 涨分失败 (状态码: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        log_message(f"❌ {username} - 网络请求失败: {str(e)}")
        return False
    except Exception as e:
        log_message(f"❌ {username} - 发送请求时出错: {str(e)}")
        return False

def main(cookie):
    """命令行版本主函数"""
    log_message("🎉 命令行工具已启动")
    log_message("🚀 开始涨分...")
    
    client_username_file = "client_username.json"

    # 1. 从API获取用户名数据
    api_usernames = get_usernames_from_api()
    if not api_usernames:
        log_message("❌ 无法获取用户名数据，停止处理")
        return
    
    # 2. 更新client_username文件
    client_data = update_client_username_data(api_usernames, client_username_file)
    if not client_data:
        log_message("❌ 没有可处理的用户名数据")
        return
    
    # 3. 依次发送涨分请求
    log_message(f"开始处理 {len(client_data)} 个涨分链接...")
    
    success_count = 0
    for i, user_data in enumerate(client_data):
        username = user_data.get("username")
        number = user_data.get("number")
        
        if username:
            log_message(f"正在处理 #{number} - {username}... ({i+1}/{len(client_data)})")
            
            if send_claim_request(username, cookie):
                success_count += 1
            
            # 添加延迟避免请求过快
            if i < len(client_data) - 1:
                time.sleep(2)
    
    log_message(f"🎉 涨分完成！成功: {success_count}/{len(client_data)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 addplus_cli.py \"<你的完整Cookie字符串>\"")
        print("例如: python3 addplus_cli.py \"token=...; next-auth.session-token=...\"")
        sys.exit(1)
    
    cookie_str = sys.argv[1]
    main(cookie_str)
