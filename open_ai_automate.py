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
            size="256x256"
        )
        image_url = response1['data'][0]['url']
        print(image_url)
        return image_url

    # get post content text -------------------->>>>>>>>>>>>>>>
    def generate_linkedin_post_content(self, brand_description):
        prompt = f"We are writing a progressive series of posts for LinkedIn. All posts should be of different brands: {brand_description}. Also, add relevant emojis and hashtags to the text."
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.7,
            max_tokens=150,
            top_p=1.0,
            frequency_penalty=0.7,
            presence_penalty=1
        )
        return response.choices[0].text.strip()
    
    # register linkedin image upload -------------------->>>>>>>>>>>>>>>
    def register_image_upload(self, person_urn, image_url):
        register_url = 'https://api.linkedin.com/v2/assets?action=registerUpload'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        post_body = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": f"urn:li:person:{person_urn}",
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }
        response = requests.post(register_url, headers=headers, json=post_body)
        if response.status_code == 200 or 201:
            data = response.json()
            print("Response structure:", data)  # Print the entire response structure
            if 'value' in data:
                upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                asset = data['value']['asset']
            else:
                print("Response does not contain 'value' key:", data)
                return None
        else:
            print("Failed to register image upload")
            print(response)
            return None

        with urlopen(image_url) as image_response:
            image_data = image_response.read()

        with open("image.jpg", "wb") as image_file:
            image_file.write(image_data)

        headers1 = {
            "Authorization": f"Bearer {self.access_token}"
        }
        res = requests.post(upload_url, data=image_data, headers=headers1)
        print(res.status_code)
        return asset


    # create linkedin final post -------------------->>>>>>>>>>>>>>>
    # def create_linkedin_post_with_image(self, urn, post_content, media_artifact):
    def create_linkedin_post(self, urn, post_content): #posting only text for now
        api_url = 'https://api.linkedin.com/v2/ugcPosts'

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Connection': 'Keep-Alive',
            'Content-Type': 'application/json'
        }

        post_body = {
            "author": f"urn:li:person:{urn}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post_content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # post_body = {
        #     'author' : f'urn:li:person:{urn}',
        #     'LifecycleState': 'PUBLISHED',
        #     'specificContent': {
        #         'com.linkedin.ugc.ShareContent': {
        #             'sharedCommentary': {
        #                 'text' : post_content
        #             },
        #             'shareMediaCategory': 'IMAGE',
        #             'media': [
        #                 {
        #                     'status': 'READY',
        #                     'description': {
        #                         'text': 'Center stage!'
        #                     },
        #                     'media': media_artifact,
        #                     'title': {
        #                         'text': 'Sapna\'s LinkedIn Automation Project'
        #                     }
        #                 }
        #             ]
        #         }
        #     },
        #     'visibility': {
        #         'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
        #     }
        # }

        response = requests.post(api_url, headers=headers, json=post_body)
        if response.status_code == 201:
            print('Post successfully created')
        else:
            print(f'Post creation failed with status code: {response.status_code}:{response.text}')

    # MAIN METHOD HERE -------------------->>>>>>>>>>>>>>>
    def main_func(self):
        topic = input("Enter the topic: ")
        brand_description = input("Enter the brand description: ")

        # Set OpenAI API key
        openai.api_key = openai_api_key

        # get user id
        user_id = self.get_user_id()
        print("User ID:", user_id)

        # generate image using openai #############################
        image_url = self.generate_image(brand_description)
        # image_url = "https://oaidalleapiprodscus.blob.core.windows.net/private/org-PDu3lHSG8WHccDNUaguN1Ejw/user-HYi07qzEri0iYILPJJafEnge/img-zj5ul83KHZ5pXTssVvY626YS.png?st=2023-10-28T06%3A17%3A57Z&se=2023-10-28T08%3A17%3A57Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-10-27T22%3A52%3A46Z&ske=2023-10-28T22%3A52%3A46Z&sks=b&skv=2021-08-06&sig=b6lfZdCKfNEmgLpu4SaId7PtX89AOdqwimquxYJshuo%3D"

        # generate text content using openai ###################################
        text_content = self.generate_linkedin_post_content(brand_description)
        # text_content = "At SDE, we provide media professionals with the tools to create and manage dynamic digital experiences. Our services are designed to make it easier for businesses to engage their customers through cutting-edge technology! 💻 #DigitalExperience #MediaTools"

        # print the generated content
        print("Generated Post Content:", text_content)

        # register image upload on linkedin
        # media_artifact = self.register_image_upload(user_id, image_url)

        # Create a LinkedIn post with the generated content
        response = self.create_linkedin_post(user_id, text_content)
        print(response)


# global variables -------------------->>>>>>>>>>>>>>>
access_token = config.ACCESS_TOKEN
openai_api_key = config.OPEN_AI_KEY

# Create an instance of the LinkedinAutomate class and run the main function
LinkedinAutomate(access_token, openai_api_key).main_func()
