from vectorize import swtich_to_azure_env
from vectorize import init_qa_client
import streamlit as st
import streamlit_authenticator as stauth
import json
import os

@st.cache_resource
def init():
   return init_qa_client('./IRM_Help.pdf')

def invokeAI(message, history):
    print(f"[message]{message}")
    print(f"[history]{history}")
    enable_chat = True

    qa = init()

    ans = qa.invoke({"query": message})
    if ans["source_documents"] or enable_chat:
        return ans["result"]
    else:
        return "I don't know."

def resolveUserCredentials():
   names = json.loads(os.getenv("IRM_CHAT_CRE_NAMES"))
   usernames = json.loads(os.getenv("IRM_CHAT_CRE_USERNAMES"))
   passwords = json.loads(os.getenv("IRM_CHAT_CRE_PASSWORDS"))
   return names,usernames,passwords

def doAuth():
    names,usernames,passwords=resolveUserCredentials()
    hashed_passwords = stauth.Hasher(passwords).generate()

    credentials = {'usernames': {}}
    for i in range(0, len(names)):  
       credentials['usernames'][usernames[i]] = {'name': names[i], 'password': hashed_passwords[i]}  
    authenticator = stauth.Authenticate(credentials, 'some_cookie_name', 'some_signature_key', cookie_expiry_days=0)
    authenticator.login(fields={'Username':'SAP Email', 'Password':'SAP i-Number',})

    if st.session_state["authentication_status"] is False:
       st.error('Email/i-Number is incorrect')
    elif st.session_state["authentication_status"] is None:
       st.warning('Please enter your Email and i-Number')

def chat(doChat):
    st.title("Hi, {}".format(st.session_state["name"]))
    swtich_to_azure_env()

    prompt = st.chat_input("Enter your questions here")

    if "user_prompt_history" not in st.session_state:
       st.session_state["user_prompt_history"]=[]
    if "chat_answers_history" not in st.session_state:
       st.session_state["chat_answers_history"]=[]
    if "chat_history" not in st.session_state:
       st.session_state["chat_history"]=[]

    if prompt:
       with st.spinner("Generating......"):
          output = doChat(prompt, st.session_state["chat_history"])
          st.session_state["chat_answers_history"].append(output)
          st.session_state["user_prompt_history"].append(prompt)
          st.session_state["chat_history"].append((prompt,output))

      # Displaying the chat history

    if st.session_state["chat_answers_history"]:
       for i, j in zip(st.session_state["chat_answers_history"],st.session_state["user_prompt_history"]):
          message1 = st.chat_message("user")
          message1.write(j)
          message2 = st.chat_message("assistant")
          message2.write(i)

if __name__ == "__main__":
   if "authentication_status" not in st.session_state or st.session_state["authentication_status"] is not True:
      doAuth()
   else:
      chat(invokeAI)