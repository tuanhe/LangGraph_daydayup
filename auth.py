import hmac
import base64
import json
import requests
import time
import json
from hashlib import sha256

call_count = 0

auth_base = "https://aimpapi.midea.com/t-aigc/aimp-aigc-auth/getAccessToken"

def create_signature(secret_key, value_to_digest):
    # 创建 HMAC-SHA256 摘要
    digest = hmac.new(secret_key.encode('utf-8'), value_to_digest.encode('utf-8'), sha256).digest()
    # 将摘要编码为 Base64 字符串
    return base64.b64encode(digest).decode('utf-8')


def create_signature(secret_key, value_to_digest):
    # 创建 HMAC-SHA256 摘要
    digest = hmac.new(secret_key.encode('utf-8'), value_to_digest.encode('utf-8'), sha256).digest()
    # 将摘要编码为 Base64 字符串
    return base64.b64encode(digest).decode('utf-8')

def access_token(publicKey, secretKey, url_base= auth_base ):
    # 去算法管理平台获取sit和prod的获取token的地址

    if len(url_base) > 0:
        url = url_base
    timestamp = str(int(time.time() * 1000))  # 获取毫秒时间戳
    # 创建参数字典
    paramMap = {
        "publicKey": publicKey,
        "timestamp": timestamp,
        "sign": create_signature(secretKey, publicKey + timestamp)
    }

    # 打印参数字典
    print("----" + json.dumps(paramMap))

    # 发送 POST 请求
    headers = {"Content-Type": "application/json"}
    response = {}
    try:
        response = requests.post(url, headers=headers, json=paramMap, proxies={"http": None, "https": None})
        print(response.text)
    except Exception as e:
        print(e)
    return response.text


def generate_token():
     publicKey = "1b761bcf578e4b4b9c8f8f588c55a2d0"  # 替换为团队自己的publicKey
     secretKey = "e3eac93bd450416ab0316df6cf30d610"  # 替换为团队自己的secretKey
     token_text = access_token(publicKey, secretKey)
     token_json = json.loads(token_text)
     return token_json["data"]["token"]

def get_headers():
    headers = {
        "Content-Type": "application/json",
        "Aimp-App-Id":"1892819270127927297",
        "Aimp-Biz-Id": "aimp-qwen2-5-72b-ascend",
        "Aimp-Api-Token": generate_token()
    }

    return headers 