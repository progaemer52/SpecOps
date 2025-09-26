import base64
import io
import pickle

import requests
from PIL import Image

########################################
# This file contains our own implementation of LLM call APIs
########################################

token_usage_input = 0
token_usage_output = 0

def simple_converse(text, messages=None, reasoning=None, files=None, system=None):
    if messages is None:
        messages = []

    content = [{"text": text}]

    if files:
        for file_path in files:
            format = file_path.split('.')[-1]  # Extract file extension as format
            if format in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                if format == 'jpg':
                    format = 'jpeg'
                with Image.open(file_path) as img:
                    # Convert image to bytes
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format=format)
                    img_byte_arr.seek(0)
                    image_bytes = img_byte_arr.getvalue()
                    content.append({
                        "image": {
                            "format": format,
                            "source": {
                                "bytes": image_bytes,
                            }
                        }
                    })
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    file_name = file_path.split('/')[-1]  # Extract filename from path
                    format = file_name.split('.')[-1]

                    if format == "sh":
                        format = "txt"
                        file_content = f"# Shell script: {file_content}"
                    if format == "py":
                        format = "txt"
                    content.append({
                        "document": {
                            "format": format,  # Extract extension as format
                            "name": file_name.split('.')[0],
                            "source": {
                                "bytes": file_content.encode('utf-8')
                            }
                        }
                    })

    messages.append({
        "role": "user",
        "content": content
    })
    url = "http://localhost:8000/converse"

    return converse(url, messages, reasoning=reasoning, system=system)


def converse(url, messages, system=None, reasoning=None):
    params = {"messages": messages}
    if system:
        params["system"] = system
    if reasoning:
        params["reasoning"] = reasoning

    serialized_data = base64.b64encode(pickle.dumps(params)).decode('utf-8')
    files = {
        "serialized_data": ("filename.txt", io.StringIO(serialized_data), 'text/plain')
    }
    server_response = requests.post(url,
                                    files=files,
                                    )

    global token_usage_input, token_usage_output
    token_usage_input += server_response.json()["claude_response"]['usage']['inputTokens']
    token_usage_output += server_response.json()["claude_response"]['usage']['outputTokens']
    return server_response.json()["claude_response"]["output"]["message"]


def simple_chat(reasoning=None):
    messages = []
    while True:
        text = input("Enter your text: ")
        message = simple_converse(text, messages, reasoning=reasoning)
        idx = 1 if reasoning else 0
        print(message['content'][idx]['text'])
        messages.append(message)


if __name__ == "__main__":
    message = simple_converse("What is the capital of France?")
    # message = simple_converse("What is in the files?", files=["assets/test_img.png", "assets/test.txt"])
    print(message)