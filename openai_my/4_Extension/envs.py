from dotenv import load_dotenv
import os

def swtich_to_azure_env() -> None:
    load_dotenv()
    os.environ["OPENAI_API_TYPE"] = "azure"
    os.environ["OPENAI_API_VERSION"] = "2023-05-15"
    os.environ["AZURE_OPENAI_ENDPOINT"] = "https://pvg-azure-openai-uk-south.openai.azure.com"
    print('Swtiched to azure!')