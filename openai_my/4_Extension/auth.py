import streamlit_authenticator as stauth
import streamlit as st
import json
import os

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
    authenticator.login(fields={'Username':'SAP Email', 'Password':'SAP i-Number'})

    if st.session_state["authentication_status"] is False:
       st.error('Email/i-Number is incorrect')
    elif st.session_state["authentication_status"] is None:
       st.warning('Please enter your Email and i-Number')