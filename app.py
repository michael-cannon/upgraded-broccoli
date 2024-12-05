# app.py
from flask import Flask, request, render_template
import openai
import re
import os
import logging
from dotenv import load_dotenv
from config import MAKE_BETTER_PROMPT, CRITIQUE_PROMPT

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
    logger.info(f"Assistant created with ID: {ASSISTANT_ID}")
    return assistant

def create_thread(client):
    thread = client.beta.threads.create()
    logger.info(f"Thread created with ID: {thread.id}")
    return thread

def add_message(client, thread_id, content):
    logger.info(f"Content: {content}")
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )
    logger.info(f"Message added to thread {thread_id}")
    return message

def run_assistant(client, thread_id, assistant_id):
    response = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    logger.info(f"Assistant run completed for thread {thread_id}")
    return response

def process_section(section, assistant_id):
    client = openai.OpenAI()
    thread = create_thread(client)
    add_message(client, thread.id, MAKE_BETTER_PROMPT.format(section))
    improved_section = run_assistant(client, thread.id, assistant_id)

    final_section = ""
    
    if improved_section.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )

        first_response_content = messages.data[0].content[0].text.value
        logger.info(f"First response: {first_response_content}")
        logger.info("Improved section received")

        thread = create_thread(client)
        add_message(client, thread.id, CRITIQUE_PROMPT.format(first_response_content))
        final_section = run_assistant(client, thread.id, assistant_id)
        
        if improved_section.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )

            final_section = messages.data[0].content[0].text.value
            logger.info("Final section received after critique")

        else:
            final_section = "Error processing Critique. Please try again."
            logger.error("Error processing Critique")

    else:
        final_section = "Error processing Improve. Please try again."
        logger.error("Error processing Improve")

    return final_section

def convert_alternate_headers(markdown_content):
    lines = markdown_content.split('\n')
    converted_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and (lines[i + 1].startswith('=') or lines[i + 1].startswith('-')):
            if lines[i + 1].startswith('=') and len(lines[i + 1]) >= 3:
                converted_lines.append(f"# {line}")
                i += 2  # Skip the next line
            elif lines[i + 1].startswith('-') and len(lines[i + 1]) >= 3:
                converted_lines.append(f"## {line}")
                i += 2  # Skip the next line
            else:
                converted_lines.append(line)
                i += 1
        else:
            converted_lines.append(line)
            i += 1

    return '\n'.join(converted_lines)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        markdown_content = request.form['markdown_content']
        markdown_content = convert_alternate_headers(markdown_content)
        sections = re.split(r'(\n#+ .+\n)', markdown_content)
        
        logging.info(f"Sections: {sections}")
        
        assistant = create_assistant()
        final_content = ""
        
        for i in range(0, len(sections), 2):
            header = sections[i]
            content = sections[i + 1] if i + 1 < len(sections) else ""
            if content:  # Check if content is not blank
                final_content += header + "\n" + process_section(content, assistant.id) + "\n"
            else:
                final_content += header + "\n"

        logger.info("Final content generated")
        return render_template('index.html', final_content=final_content)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)