import os
import pandas
import tiktoken
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader;
from langchain.chains import RetrievalQA
from langchain_openai import AzureChatOpenAI

def swtich_to_azure_env() -> None:
    load_dotenv()
    os.environ["OPENAI_API_TYPE"] = "azure"
    os.environ["OPENAI_API_VERSION"] = "2023-05-15"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://pvg-azure-openai-uk-south.openai.azure.com"
    print('Swtiched to azure!')

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

def init_vector_db(textArray,path = "data/irm_help_faiss"):
    swtich_to_azure_env()
    embeddings = AzureOpenAIEmbeddings()
    faiss_ins = FAISS.from_texts(textArray,embeddings)
    faiss_ins.save_local(path)
    return faiss_ins

def init_qa_client(pdfPath):
    pdf_pages = read_pdf_sample_doc(pdfPath)
    normalized_df = normalize_txt_array_and_to_df(pdf_pages)
    local_path = "data/irm_help_faiss"
    if not os.path.exists(local_path):
        init_vector_db(normalized_df["content"],local_path)

    swtich_to_azure_env()
    vec_db = FAISS.load_local(local_path, AzureOpenAIEmbeddings(),allow_dangerous_deserialization=True)
    llm = AzureChatOpenAI(model_name="gpt-35-turbo", temperature=0.5)
    qa_chain = RetrievalQA.from_chain_type(llm,
                retriever=vec_db.as_retriever(search_type="similarity_score_threshold",
                search_kwargs={"score_threshold": 0.7}))
    qa_chain.combine_documents_chain.verbose = True
    qa_chain.return_source_documents = True
    return qa_chain