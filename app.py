import os
import streamlit as st
from dotenv import load_dotenv

# 설정
PDF_PATH = "data/2024_KB_부동산_보고서_최종.pdf"

# 환경 변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
