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
    elif generator == "gemini":
        import google.generativeai as genai
        import base64
        from PIL import Image
        import io
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        model = "imagen-3.0"
        response = genai.generate_images(
            model=model,
            prompt=prompt
        )
        image_data = response.generated_images[0].data
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        image.save(output_path)
    elif generator == "craiyon":
        import base64
        response = requests.post("https://api.craiyon.com/generate", json={"prompt": prompt})
        data = response.json()
        image_data = data["images"][0]
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
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
    else:
        raise ValueError("Invalid GENERATOR. Use 'openai', 'gemini', 'craiyon', or 'grok'")

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