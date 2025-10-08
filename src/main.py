import json
import argparse
import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def load_input(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    required_fields = ['tournament_name', 'match_round', 'match_date', 'toss_winner', 'final_scores', 'result', 'summary']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    return data

def generate_comic(data, output_path='comic.png'):
    required_fields = ['tournament_name', 'match_round', 'match_date', 'toss_winner', 'final_scores', 'result', 'summary']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    prompt = f"Create a comic strip image for a cricket match. Tournament: {data['tournament_name']}, Round: {data['match_round']}, Date: {data['match_date']}, Toss won by: {data['toss_winner']}, Final scores: {data['final_scores']['team1']} vs {data['final_scores']['team2']}, Result: {data['result']}. Summary: {data['summary']}. Make it a 4-panel comic strip in a fun, illustrative style."
    generator = os.getenv("GENERATOR", "openai").lower()
    if generator == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        print("#########",api_key)
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        client = openai.OpenAI(api_key=api_key)
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        img_response = requests.get(image_url)
        with open(output_path, 'wb') as f:
            f.write(img_response.content)

    elif generator == "grok":
        api_key = os.getenv("GROK_API_KEY")
        if not api_key:
            raise ValueError("GROK_API_KEY environment variable not set")
        client = openai.OpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
        response = client.images.generate(
            model="grok-vision-beta",
            prompt=prompt,
            n=1,
        )
        image_url = response.data[0].url
        img_response = requests.get(image_url)
        with open(output_path, 'wb') as f:
            f.write(img_response.content)

    elif generator == "piapi":
        import time
        api_key = os.getenv("PIAPI_API_KEY")
        if not api_key:
            raise ValueError("PIAPI_API_KEY environment variable not set")

        # Create task
        create_url = "https://api.piapi.ai/api/v1/task"
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "model": "Qubico/flux1-dev",
            "task_type": "txt2img",
            "input": {
                "prompt": prompt,
                "width": 1024,
                "height": 1024
            }
        }

        create_response = requests.post(create_url, headers=headers, json=payload)
        create_data = create_response.json()

        if create_data.get("code") != 200:
            raise ValueError(f"PiAPI task creation failed: {create_data}")

        task_id = create_data["data"]["task_id"]
        print(f"PiAPI task created with ID: {task_id}")

        # Poll for completion
        get_url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        max_attempts = 30  # 5 minutes with 10s intervals
        attempt = 0

        while attempt < max_attempts:
            get_response = requests.get(get_url, headers={"X-API-Key": api_key})
            get_data = get_response.json()

            if get_data.get("code") != 200:
                raise ValueError(f"PiAPI task retrieval failed: {get_data}")

            status = get_data["data"]["status"]
            print(f"Task status: {status}")

            if status == "completed":
                image_url = get_data["data"]["output"]["image_url"]
                img_response = requests.get(image_url)
                with open(output_path, 'wb') as f:
                    f.write(img_response.content)
                print(f"Image saved to {output_path}")
                break
            elif status == "failed":
                error_msg = get_data["data"]["error"]["message"]
                raise ValueError(f"PiAPI task failed: {error_msg}")

            attempt += 1
            time.sleep(10)  # Wait 10 seconds before checking again

        if attempt >= max_attempts:
            raise ValueError("PiAPI task timed out")

    elif generator == "gemini":
        import time
        api_key = os.getenv("PIAPI_API_KEY")
        if not api_key:
            raise ValueError("PIAPI_API_KEY environment variable not set (required for Gemini generator)")

        # Create task
        create_url = "https://api.piapi.ai/api/v1/task"
        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gemini",
            "task_type": "gemini-2.5-flash-image",
            "input": {
                "prompt": prompt,
                "num_images": 1,
                "output_format": "png"
            }
        }

        create_response = requests.post(create_url, headers=headers, json=payload)
        create_data = create_response.json()

        if create_data.get("code") != 200:
            raise ValueError(f"PiAPI Gemini task creation failed: {create_data}")

        task_id = create_data["data"]["task_id"]
        print(f"PiAPI Gemini task created with ID: {task_id}")

        # Poll for completion
        get_url = f"https://api.piapi.ai/api/v1/task/{task_id}"
        max_attempts = 30  # 5 minutes with 10s intervals
        attempt = 0

        while attempt < max_attempts:
            get_response = requests.get(get_url, headers={"X-API-Key": api_key})
            get_data = get_response.json()

            if get_data.get("code") != 200:
                raise ValueError(f"PiAPI Gemini task retrieval failed: {get_data}")

            status = get_data["data"]["status"]
            print(f"Task status: {status}")

            if status == "completed" or status == "success":
                output = get_data["data"].get("output")
                if not output:
                    print(f"Task {status} but output is null. Full response: {get_data}")
                    continue

                # Handle different output formats
                image_url = None
                if "image_url" in output:  # Flux format
                    image_url = output["image_url"]
                elif "image_urls" in output and output["image_urls"]:  # Gemini format
                    image_url = output["image_urls"][0]  # Take first image

                if image_url:
                    print(f"Downloading image from: {image_url}")
                    img_response = requests.get(image_url)
                    img_response.raise_for_status()  # Check for HTTP errors
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    print(f"Image saved to {output_path}")
                    break
                else:
                    print(f"Task {status} but no image URL found in output: {output}")
                    raise ValueError(f"Task completed but no image URL in output: {output}")
            elif status == "failed":
                error_msg = get_data["data"]["error"]["message"]
                raise ValueError(f"PiAPI task failed: {error_msg}")

            attempt += 1
            time.sleep(10)  # Wait 10 seconds before checking again

        if attempt >= max_attempts:
            raise ValueError("PiAPI Gemini task timed out")

    elif generator == "nano-banana":
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        try:
            genai.configure(api_key=api_key)

            # Use Gemini 2.5 Flash Image model (Nano Banana)
            model = genai.GenerativeModel('gemini-2.5-flash-image')

            # Create image generation request
            response = model.generate_content([
                f"Generate a high-quality comic strip image for a cricket match: {prompt}",
                "Make it a 4-panel comic strip in a fun, illustrative style."
            ])

            # Extract and save image from response
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and len(candidate.content.parts) > 0:
                    part = candidate.content.parts[0]

                    # Handle different response formats
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Base64 encoded image
                        import base64
                        image_data = base64.b64decode(part.inline_data.data)
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        print(f"Image saved to {output_path}")
                    elif hasattr(part, 'text'):
                        # Text response (not image)
                        raise ValueError("Gemini returned text instead of image. The model may not support image generation in this context.")
                    else:
                        raise ValueError("Unexpected response format from Gemini API")
                else:
                    raise ValueError("No content in Gemini response")
            else:
                raise ValueError("No candidates in Gemini response")

        except Exception as e:
            if "not found for API version" in str(e):
                raise ValueError("Gemini 2.5 Flash Image model not available. Try using PiAPI: GENERATOR=gemini PIAPI_API_KEY=your_key")
            else:
                raise ValueError(f"Gemini Nano Banana generation failed: {str(e)}")

    else:
        raise ValueError("Invalid GENERATOR. Use 'openai', 'grok', 'piapi', 'gemini', or 'nano-banana'")

def main():
    parser = argparse.ArgumentParser(description="Generate cricket comic strip from match data")
    parser.add_argument('input_file', help='Path to JSON input file')
    parser.add_argument('--output', default='comic.png', help='Output image path')
    args = parser.parse_args()

    data = load_input(args.input_file)
    generate_comic(data, args.output)
    print(f"Comic strip saved to {args.output}")

if __name__ == "__main__":
    main()