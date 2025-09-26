import base64
import io
import json
import os
import pickle

import imagehash
import requests
import screen_utils
from PIL import Image
from screen_utils import screenshot_primary_monitor


def generate_report(texts, image_dir, offset=0, limit=20):
    # read files from image_dir, convert to base64 and send to server
    assert offset >= 0
    content = [{"text": texts[0]}]
    final_response = ""

    files = os.listdir(image_dir)
    files.sort()
    # files = files[offset:]

    # First remove duplicates
    unique_files = []
    previous_hash = None
    hash_threshold = 0.5  # Adjustable similarity threshold

    for image_file in files:
        image_path = os.path.join(image_dir, image_file)

        with Image.open(image_path) as img:
            # Generate perceptual hash
            img_hash = imagehash.phash(img)

            # Skip if visually similar to previous image
            if previous_hash is not None and abs(img_hash - previous_hash) <= hash_threshold:
                continue

            # Found a visually different image
            previous_hash = img_hash
            unique_files.append(image_file)

    unique_files = unique_files[offset:]
    unique_files = unique_files[limit*-1:]


    for image_file in unique_files:
    # for image_file in files:


        format = image_file.split(".")[-1]
        if format == "jpg":
            format = "jpeg"
        image_path = os.path.join(image_dir, image_file)
        with Image.open(image_path) as img:
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

    message = [{
        "role": "user",
        "content": content
    }]

    for i in range(len(texts)):
        serialized_data = base64.b64encode(pickle.dumps(message)).decode('utf-8')
        files = {
            "serialized_data": ("filename.txt", io.StringIO(serialized_data), 'text/plain')
        }
        server_response = requests.post(
            'http://localhost:8000/reason',
            files=files,
        )

        converse.token_usage_input += server_response.json()["claude_response"]['usage']['inputTokens']
        converse.token_usage_output += server_response.json()["claude_response"]['usage']['outputTokens']
        response = server_response.json()["claude_response"]
        message.append(response["output"]["message"])

        print(json.dumps(response["output"]["message"], indent=4))
        print("\n\n")
        print("-" * 50)
        final_response = response["output"]["message"]['content'][1]['text']
        print(final_response)
        print("-" * 50)
        print("\n\n")

        if i < len(texts) - 1:
            message.append({
                "role": "user",
                "content": [
                    {
                        "text": texts[i + 1]
                    }
                ]
            })
    # print("----------------Final report concludes----------------")
    return final_response