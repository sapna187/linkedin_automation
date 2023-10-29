import json
from urllib.request import Request, urlopen

import openai
import requests

import config


class LinkedinAutomate:
    def __init__(self, access_token, openai_api_key):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        self.openai_api_key = openai_api_key

    def common_api_call_part(self, feed_type="feed"):
        payload_dict = {
            "author": f"urn:li:person:{self.user_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": self.description
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": self.description
                            },
                            "originalUrl": self.image,
                            "title": {
                                "text": self.title
                            },
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC" if feed_type == "feed" else "CONTAINER"
            }
        }
        return json.dumps(payload_dict)
    

    # get user id -------------------->>>>>>>>>>>>>>>
    def get_user_id(self):
        url = "https://api.linkedin.com/v2/userinfo"
        response = requests.request("GET", url, headers=self.headers)

        if response.status_code == 200:
            jsonData = json.loads(response.text)
            user_id = jsonData.get("sub")
            if user_id:
                return user_id
            else:
                print("User ID not found in the response:", jsonData)
        else:
            print("Failed to fetch user data. Status Code:", response.status_code)
            print("Response Content:", response.text)
        return None

    # generate image -------------------->>>>>>>>>>>>>>>
    def generate_image(self, description):
        response1 = openai.Image.create(
            prompt=f"Generate an image related to {description}",
            n=1,