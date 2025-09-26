# client.py
import base64
import io
import json
import pickle
import re

import imagehash
import requests

import converse
import screen_utils
import setup_utils


def filter_messages(messages):
    # count = 0
    # for message in messages:
    #     if not 'content' in message:
    #         continue
    #
    #     has_image = len([item for item in message['content'] if 'image' in item]) != 0
    #     is_screenshot = message["role"] == "user" and has_image
    #     if is_screenshot:
    #         count += 1

    # if count > 20:
    for message in messages[:-20]:
        if not 'content' in message:
            continue

        message['content'] = [item for item in message['content'] if 'image' not in item]

def mcp_converse(messages, tools_module, url, specify_module=None):
    description = ""
    desc_serial = 1

    while True:
        serialized_data = base64.b64encode(pickle.dumps(messages)).decode('utf-8')
        files = {
            "serialized_data": ("filename.txt", io.StringIO(serialized_data), 'text/plain')
        }

        if not specify_module:
            server_response = requests.post(url,files=files)
        else:
            server_response = requests.post(url, files=files, data={"module": specify_module})

        converse.token_usage_input += server_response.json()["claude_response"]['usage']['inputTokens']
        converse.token_usage_output += server_response.json()["claude_response"]['usage']['outputTokens']
        response = server_response.json()["claude_response"]


        if len(messages) > 20:
            filter_messages(messages)
            print("Filtered messages to keep the last 20 screenshots.")

        print(f"Server responded: {json.dumps(response["output"]["message"], indent=4)}")
        messages.append(response["output"]["message"])


        if response["stopReason"] == "tool_use":
            for content in response["output"]["message"]["content"]:
                if "toolUse" in content:
                    tool_use = content["toolUse"]
                    tool_name = tool_use["name"]
                    tool_input = tool_use["input"]
                    tool_use_id = tool_use["toolUseId"]
                    print(f"Executing tool: {tool_name}")
                    function = getattr(tools_module, tool_name, None)
                    tool_result = function(**tool_input)
                    print(f"Tool response: {tool_result}")
                    tool_result_json = tool_result
                    tool_result_message = {
                        "role": "user",
                        "content": [
                            {
                                "toolResult": {
                                    "toolUseId": tool_use_id,
                                    "content": [{"text": tool_result_json['message']}],
                                    "status": tool_result_json['status']
                                }
                            }
                        ]
                    }
                    messages.append(tool_result_message)
                    if tool_name == "get_screenshot" and tool_result_json['status'] == "success":
                        messages.append(get_screenshot_and_message("Here is the updated screen after the last action:"))
                    if 'description' in tool_result_json:
                        description += f"[{desc_serial}]: {tool_result_json['description']}\n"
                        desc_serial += 1
        else:
            break

    return description, messages

def get_screenshot_and_message(user_text):
    print("Taking screenshot...")
    # Take a screenshot
    screenshot = screen_utils.screenshot_primary_monitor()
    # Convert screenshot to bytes
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    image_bytes = img_byte_arr.getvalue()
    print("Sending data to server...")
    message ={
            "role": "user",
            "content": [
                {
                    "text": user_text,
                },
                {
                    "image": {
                        "format": "png",
                        "source": {
                            "bytes": image_bytes,
                        }
                    }
                }
            ]
        }

    return message

def operate_computer(user_text):
    messages = [get_screenshot_and_message(user_text)]
    url = "http://localhost:8000/ping"

    mcp_converse(messages, screen_utils, url)
    return messages

def setup(text, module=None):
    content = [{"text": text}]
    messages = [{
        "role": "user",
        "content": content
    }]
    url = "http://localhost:8000/setup"

    description = mcp_converse(messages, setup_utils, url, module)
    return description

def converse_json(messages, text):
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "text": text
                }
            ]
        })
    url = "http://localhost:8000/converse"

    system = [
        {
            "text": "You are an JSON extraction assistant. Extract a json object or array of json objects from the text as requested by the user. Reply only the extracted result and nothing else."
        }
    ]
    message = converse.converse(url, messages, system)
    messages.append(message)
    # print(message)
    # print("")
    json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    text_content = "\n".join([item['text'] for item in message['content']])
    matches = re.findall(json_pattern, text_content)
    assert len(matches) == 1
    extracted_json = json.loads(matches[0])
    return extracted_json