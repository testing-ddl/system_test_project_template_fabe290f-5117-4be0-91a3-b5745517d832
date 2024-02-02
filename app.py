import requests
import streamlit as st


import ctranslate2
import nvidia
import os
import time
import torch
import transformers

from random import randint
from streamlit.web.server import websocket_headers
from streamlit_chat import message
from transformers import AutoTokenizer


def generate(prompt: str = None, pct_new_tokens: float = 0.2):
    if prompt is None:
        return {'text_from_llm': "Please provide a prompt", 'tokens_per_sec': -1}
    # Tokenize the prompt
    tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(prompt))
    input_length = len(tokens)
    new_tokens = round(pct_new_tokens*input_length)
    tokens_per_sec = 0
    start_time = time.time()
    results = generator.generate_batch([tokens], sampling_topk=10, max_length=new_tokens, include_prompt_in_result=False)
    end_time = time.time()
    output_text = tokenizer.decode(results[0].sequences_ids[0])
    tokens_per_sec = round(new_tokens / (end_time - start_time),3)
    return {'text_from_llm': output_text, 'tokens_per_sec': tokens_per_sec}
    
    
cuda_install_dir = '/'.join(nvidia.__file__.split('/')[:-1]) + '/cuda_runtime/lib/'
os.environ['LD_LIBRARY_PATH'] =  cuda_install_dir


# Load the ctranslate model, please change this to where you have saved the ctranslate2 model
model_path = '/mnt/data/SM-LLM-Inference/'
hf_model_name = 'tiiuae/falcon-7b'
model_device = 'cuda' if torch.cuda.is_available() else 'cpu'

# load the ctranslate model
generator = ctranslate2.Generator(model_path, device=model_device)
# load the tokenizer
tokenizer = transformers.AutoTokenizer.from_pretrained(hf_model_name)

prompt_template = f"Summarize the chat dialogue:\n{{dialogue}}\n---\nSummary:\n"


# Initialise session state variables
if 'generated' not in st.session_state:
    st.session_state['generated'] = []
if 'past' not in st.session_state:
    st.session_state['past'] = []
if 'messages' not in st.session_state:
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]
if 'tokens_sec' not in st.session_state:
    st.session_state['tokens_sec'] = []


st.set_page_config(initial_sidebar_state='collapsed')
clear_button = st.sidebar.button("Clear Conversation", key="clear")
                


if clear_button:
    st.session_state['generated'] = []
    st.session_state['past'] = []
    st.session_state['tokens_sec'] = []
    st.session_state['messages'] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]


# container for chat history
response_container = st.container()
# container for text box
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You:", key='input', height=150)
        submit_button = st.form_submit_button(label='Send')
        tokens_sec = 0
    if submit_button and user_input :
        with st.spinner("Generating response"):
            prompt = prompt_template.format(dialogue=user_input)
            llm_response = generate(prompt)
            answer = llm_response['text_from_llm']
            tokens_sec = llm_response['tokens_per_sec']
            
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(answer)
        st.session_state['tokens_sec'].append(tokens_sec)
        
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + '_user')
                message(st.session_state["generated"][i], key=str(i))
                st.write(f"Tokens generated per sec: {st.session_state['tokens_sec'][i]}")
