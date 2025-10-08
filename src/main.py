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

def extract_key_events(summary_text):
    """Extract key cricket events from match summary text."""
    import re

    highlights = []

    # Extract player performances (runs, wickets)
    # Pattern for "Player scored X off Y balls" or "Player took W/X"
    performance_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+was|\s+scored|\s+took|\s+hit|\s+struck|\s+remained)?\s+(\d+(?:\.\d+)?(?:\s+off\s+\d+(?:\s+balls?)?)?(?:\s+for\s+\d+(?:\.\d+)?)?|wicket|wickets|boundary|four|six)'
    performances = re.findall(performance_pattern, summary_text, re.IGNORECASE)

    for match in performances:
        player, stat = match
        if 'wicket' in stat.lower():
            highlights.append(f"{player}: {stat}")
        elif 'boundary' in stat.lower() or 'four' in stat.lower() or 'six' in stat.lower():
            highlights.append(f"{player}: {stat}")
        else:
            highlights.append(f"{player}: {stat}")

    # Extract partnerships
    partnership_pattern = r'(\d+)-run (?:stand|partnership) between ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*) and ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    partnerships = re.findall(partnership_pattern, summary_text, re.IGNORECASE)

    for runs, player1, player2 in partnerships:
        highlights.append(f"{player1}-{player2} partnership: {runs} runs")

    # Extract collapses or key moments
    if 'collapse' in summary_text.lower():
        collapse_pattern = r'(\d+)/(\d+).*?(\d+)'
        collapses = re.findall(collapse_pattern, summary_text)
        for wickets, runs, remaining in collapses:
            if int(wickets) >= 5:
                highlights.append(f"Collapse: {wickets} wickets for {remaining} runs")

    # Remove duplicates and limit to top 4 highlights
    unique_highlights = []
    seen = set()
    for highlight in highlights:
        if highlight not in seen:
            unique_highlights.append(highlight)
            seen.add(highlight)

    return unique_highlights[:4]  # Return top 4 highlights

def generate_poster(data, output_path='comic.png'):
    required_fields = ['tournament_name', 'match_round', 'match_date', 'toss_winner', 'final_scores', 'result', 'summary']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    # Extract key events from summary
    key_events = extract_key_events(data['summary'])
    events_text = "\n".join(f"- {event}" for event in key_events) if key_events else "- Exciting cricket action throughout the match"

    prompt = f"""Create a professional cricket match poster for: {data['tournament_name']} {data['match_round']}

MATCH DETAILS:
- Date: {data['match_date']}
- Toss: Won by {data['toss_winner']}
- Final Scores: {data['final_scores']['team1']} | {data['final_scores']['team2']}
- Result: {data['result']}

KEY HIGHLIGHTS:
{events_text}

VISUAL DESIGN REQUIREMENTS:
- Vibrant cricket-themed background with stadium atmosphere and crowd
- Prominent centered scoreboard with large, bold typography for scores
- Highlight boxes for key players and match moments
- Team colors and national flags prominently displayed
- Professional sports poster layout with dynamic cricket imagery
- Bright, energetic color scheme celebrating the match victory
- Include cricket-specific elements like wickets, bats, and balls
- High-quality, detailed illustration style suitable for printing

Make it an informative, visually stunning poster that captures the excitement and drama of this cricket match."""
    generator = os.getenv("GENERATOR", "openai").lower()
    if generator == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
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
    generate_poster(data, args.output)
    print(f"Poster saved to {args.output}")

if __name__ == "__main__":
    main()