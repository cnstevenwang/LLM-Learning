#!/bin/bash

## export azure api key,replace with the real one
# export AZURE_OPENAI_API_KEY="sample" # replace

## export streamlit-auth required env vars
export IRM_CHAT_CRE_NAMES='["abc","def"]'
## sample only
export IRM_CHAT_CRE_USERNAMES='["abc@sample.com","@sample.com"]'
export IRM_CHAT_CRE_PASSWORDS='["xxxxxx","xxxxxx"]'
export IRM_AUTH_ENABLED=False

streamlit run main.py