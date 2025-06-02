import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


# 설정
PDF_PATH = "data/2024_KB_부동산_보고서_최종.pdf"

# 환경 변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# PDF 처리 함수
def process_pdf():
    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(documents)

# 벡터 저장소 초기화
@st.cache_resource
def initialize_vectorstore():
    chunks = process_pdf()
    embeddings = OpenAIEmbeddings(api_key=api_key)
    return Chroma.from_documents(chunks, embeddings)