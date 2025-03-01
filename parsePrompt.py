import re
import json

def parse_prompt(user_input):
    # Extract URLs from the input, handling spaces and commas correctly
    url_pattern = r'https?://[^\s,]+'
    urls = re.findall(url_pattern, user_input)
    
    # Remove URLs and any leftover delimiters to extract the actual prompt
    cleaned_prompt = re.sub(url_pattern, '', user_input)
    cleaned_prompt = re.sub(r'^[,\s]+', '', cleaned_prompt).strip()
    
    return {
        "url": urls,
        "prompt": cleaned_prompt
    }
