import os
import json
from envs import swtich_to_azure_env
from vectorize import init_vector_db
from auth import doAuth
import streamlit as st
from langchain.chains import RetrievalQA
from langchain_openai import AzureChatOpenAI
from openai import AzureOpenAI
import searchengine

@st.cache_resource
def load_vector_db():
   pdfPath = './IRM_Help.pdf'
   local_db_path = "data/irm_help_faiss"
   return init_vector_db(pdfPath,local_db_path)

def extensible_qa_client_manually_handle_response(user_query):
   source_docs,ai_result= get_info_from_local_pdf_document(user_question=user_query)
   if source_docs:
      return ai_result
   
   system_prompt = "You are a helpful assistant."
   user_prompt = f"""Here is the question:[{user_query}]. Transfer the question to search-engine friendly, and search in help portal. Could you combine the search results and give me a paragraph in natural language, please keep the url?"""
   messages = [
                  {"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}
               ]
   client = AzureOpenAI(
      azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
      api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
      api_version="2023-05-15"
   )
   tools = [    
      {"type": "function", 
         "function": {
            "name": "get_info_from_help_portal", 
            "description": "Search help info from help portal",
            "parameters": {
                "type":"object",
                "properties": {
                    "user_question": {
                        "type": "string", 
                        "description": "The search keywords for help portal"
                    }
                }
            }
        }
    }
   ]
   response = client.chat.completions.create(
      model="gpt-35-turbo", 
      messages=messages,
      tools=tools, 
      tool_choice = 'auto'
   )
   response_message = response.choices[0].message

   if response.choices[0].finish_reason == "tool_calls":
      print("GPT asked us to call a function.")
      messages.append(response_message)
      call_once = False
      for tool_call in response.choices[0].message.tool_calls: 
         function_name = tool_call.function.name
         function_response = {}
         if not call_once:
            params = json.loads(tool_call.function.arguments)
            function_response = get_info_from_help_portal(
                  **params
            )
         call_once = True

         messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": function_name, "content": json.dumps(function_response)})
         
         
      second_response = client.chat.completions.create(
         model="gpt-35-turbo", 
         messages = messages,
      )
      
      return second_response.choices[0].message.content

def get_info_from_help_portal(user_question: str):
   """Get the answers from help portal.

   Args:
        user_question: The question from user
   """
   return searchengine.search(user_question)
   
def get_info_from_local_pdf_document(user_question: str):
   """Get the answers from local pdf document .

   Args:
        user_question: The question from user
   """
   
   qa_chain = create_qa_chain_with_vectordb()
   ans = qa_chain.invoke({"query": user_question})
   if ans["source_documents"]:
      return ans["source_documents"],ans["result"]
   return None,None

@st.cache_resource
def create_qa_chain_with_vectordb():
    vec_db = load_vector_db()
    llm = AzureChatOpenAI(model_name="gpt-35-turbo", temperature=0.5)
    qa_chain = RetrievalQA.from_chain_type(llm,
                retriever=vec_db.as_retriever(search_type="similarity_score_threshold",
                search_kwargs={"score_threshold": 0.7}))
    qa_chain.combine_documents_chain.verbose = True
    qa_chain.return_source_documents = True
    return qa_chain

def invokeAI(message, history):
   print(f"[message]{message}")
   print(f"[history]{history}")
   
   return extensible_qa_client_manually_handle_response(message)

def chat(doChat):
    st.title("Hi,")
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
   if os.getenv("IRM_AUTH_ENABLED")=="True" and ("authentication_status" not in st.session_state or st.session_state["authentication_status"] is not True):
      doAuth()
   else:
      chat(invokeAI)