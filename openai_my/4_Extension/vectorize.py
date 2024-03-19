import os
import pandas
import tiktoken
import envs
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader;

def read_pdf_sample_doc(pdfpath='./IRM_Help.pdf'):
    pdfLoader = PyPDFLoader(pdfpath)
    return pdfLoader.load_and_split()

def normalize_txt_array_and_to_df(txtArray):
    medium_content = []
    gpt35_encoding = tiktoken.get_encoding("cl100k_base")
    for docItem in txtArray:
        n_txt = normalize_text(docItem.page_content)
        medium_content.append(
            {
                "raw_doc": docItem,
                "content": n_txt,
                # TODO: How to handle the cases that input tokens exceed embedding api limitation?
                "token_num": len(gpt35_encoding.encode(n_txt))
            }
        )
    return pandas.DataFrame(medium_content)

def normalize_text(s, sep_token = " \n ") -> str:
    # s = re.sub(r'\s+',  ' ', s).strip()
    # s = re.sub(r". ,","",s)
    # # remove all instances of multiple spaces
    # s = s.replace("..",".")
    # s = s.replace(". .",".")
    # # s = s.replace("\n", "")
    # s = s.strip()
    
    return s

def init_vector_db(pdfPath,db_file_path = "data/irm_help_faiss"):
    if os.path.exists(db_file_path):
        return FAISS.load_local(db_file_path, AzureOpenAIEmbeddings(),allow_dangerous_deserialization=True)
    
    pdf_pages = read_pdf_sample_doc(pdfPath)
    textArray = normalize_txt_array_and_to_df(pdf_pages)["content"]
    envs.swtich_to_azure_env()
    embeddings = AzureOpenAIEmbeddings()
    faiss_ins = FAISS.from_texts(textArray,embeddings)
    faiss_ins.save_local(db_file_path)
    return faiss_ins