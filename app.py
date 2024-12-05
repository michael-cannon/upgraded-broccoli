# app.py
from flask import Flask, request, render_template
import openai
import re
import os
import logging
from dotenv import load_dotenv
from config import MAKE_BETTER_PROMPT, CRITIQUE_PROMPT, FINAL_CRITIQUE_PROMPT

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key here
openai.api_key = os.getenv('OPENAI_API_KEY')

ASSISTANT_ID = os.getenv('ASSISTANT_ID')

# Validate environment variables
if not openai.api_key:
    raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
if not ASSISTANT_ID:
    raise ValueError("Assistant ID is not set. Please set the ASSISTANT_ID environment variable.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_assistant():
    client = openai.OpenAI()
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
    return assistant

def create_thread(client):
    thread = client.beta.threads.create()
    return thread

def add_message(client, thread_id, content, role="user"):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )
    return message

def run_assistant(client, thread_id, assistant_id):
    response = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    return response

def process_section(section, assistant_id, thread_id, markdown_content):
    client = openai.OpenAI()
    add_message(client, thread_id, MAKE_BETTER_PROMPT.format(section, markdown_content))
    improved_section = run_assistant(client, thread_id, assistant_id)

    section_content = ""
    
    if improved_section.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )

        first_response_content = messages.data[0].content[0].text.value

        add_message(client, thread_id, CRITIQUE_PROMPT.format(first_response_content))
        section_content = run_assistant(client, thread_id, assistant_id)
        
        if improved_section.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=thread_id
            )

            section_content = messages.data[0].content[0].text.value

        else:
            section_content = "Error processing Critique. Please try again."

    else:
        section_content = "Error processing Improve. Please try again."

    return section_content

def process_final_content(content, assistant_id, thread_id):
    client = openai.OpenAI()
    add_message(client, thread_id, FINAL_CRITIQUE_PROMPT.format(content))
    final = run_assistant(client, thread_id, assistant_id)

    final_content = ""
    
    if final.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )

        final_content = messages.data[0].content[0].text.value
    else:
        final_content = "Error processing final Critique. Please try again."

    return final_content

def convert_alternate_headers(markdown_content):
    lines = markdown_content.split('\n')
    converted_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and (lines[i + 1].startswith('=====') or lines[i + 1].startswith('-----')):
            if lines[i + 1].startswith('====='):
                converted_lines.append(f"# {line}")
                i += 2  # Skip the next line
            elif lines[i + 1].startswith('-----'):
                converted_lines.append(f"## {line}")
                i += 2  # Skip the next line
            else:
                converted_lines.append(line)
                i += 1
        else:
            converted_lines.append(line)
            i += 1

    return '\n'.join(converted_lines)

def split_sections(markdown_content):
    lines = markdown_content.splitlines()
    result = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        elif line.startswith('#'):
            # It's a header
            header = line
            result.append(header)
            i += 1
            # Collect content lines
            content_lines = []
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                elif line.startswith('#'):
                    # Next header found
                    break
                else:
                    content_lines.append(line)
                    i += 1
            content = '\n'.join(content_lines)
            result.append(content)
        else:
            i += 1

    return result

def process_sections(sections, markdown_content, thread_id):
    assistant = create_assistant()
    section_content = ""
    
    i = 0
    while i < len(sections):
        header = sections[i]

        if i + 1 < len(sections):
            content = sections[i + 1]
            section_content += process_section(header + "\n" + content, assistant.id, thread_id, markdown_content)
            i += 2
        else:
            section_content += header
            i += 1

        section_content += "\n"

    logger.info(f"Section content: {section_content}")
    section_content = process_final_content(section_content, assistant.id, thread_id)

    return section_content

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        markdown_content = request.form['markdown_content']
        markdown_content = convert_alternate_headers(markdown_content)
        sections = split_sections(markdown_content)
        
        client = openai.OpenAI()
        thread = create_thread(client)
        final_content = process_sections(sections, markdown_content, thread.id)

        return render_template('index.html', final_content=final_content)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
