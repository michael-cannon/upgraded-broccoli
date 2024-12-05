# app.py
from flask import Flask, request, render_template
import openai
import re
import os
from config import MAKE_BETTER_PROMPT, CRITIQUE_PROMPT

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = os.getenv('OPENAI_API_KEY')

ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def create_assistant():
    client = openai.OpenAI()
    assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
    return assistant

def create_thread(client):
    thread = client.beta.threads.create()
    return thread

def add_message(client, thread_id, content):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content
    )
    return message

def run_assistant(client, thread_id, assistant_id):
    response = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
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

        thread = create_thread(client)
        add_message(client, thread.id, CRITIQUE_PROMPT.format(first_response_content))
        final_section = run_assistant(client, thread.id, assistant_id)
        
        if improved_section.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )

            final_section = messages.data[0].content[0].text.value

        else:
            final_section = "Error processing Critique. Please try again."

    else:
        final_section = "Error processing Improve. Please try again."

    return final_section

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        markdown_content = request.form['markdown_content']
        sections = re.split(r'(#+ .+)', markdown_content)
        
        assistant = create_assistant()
        final_content = ""
        for i in range(1, len(sections), 2):
            header = sections[i]
            content = sections[i + 1]
            final_content += header + "\n" + process_section(content, assistant.id) + "\n"

        return render_template('index.html', final_content=final_content)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)