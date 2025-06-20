from core import get_model
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    api_key="not-needed",  # LMStudio ne nécessite pas de clé API réelle
    model_name="dolphin3.0-llama3.1-8b",  # ou le nom de votre modèle
    temperature=0.5
)
