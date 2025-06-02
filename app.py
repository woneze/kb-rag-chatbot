import os
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory
from langchain.memory import ChatMessageHistory
from langchain_openai import ChatOpenAI


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

# 체인 초기화
@st.cache_resource
def initialize_chain():
    vectorstore = initialize_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    template = """당신은 KB 부동산 보고서 전문가입니다. 다음 정보를 바탕으로 사용자의 질문에 답변해주세요.
    컨텍스트: {context}
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", template),
        ("placeholder", "{chat_history}"),
        ("human", "{question}")
    ])

    model = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, api_key=api_key)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    base_chain = (
        RunnablePassthrough.assign(
            context=lambda x: format_docs(retriever.invoke(x["question"]))
        )
        | prompt
        | model
        | StrOutputParser()
    )

    return RunnableWithMessageHistory(
        base_chain,
        lambda session_id: ChatMessageHistory(),
        input_messages_key="question",
        history_messages_key="chat_history",
    )

# 세션 상태 관리용 헬퍼 함수
def get_chain():
    if "chat_chain" not in st.session_state:
        st.session_state.chat_chain = initialize_chain()
    return st.session_state.chat_chain

# Streamlit UI 구현
def main():
    st.set_page_config(page_title="KB 부동산 보고서 챗봇", page_icon="")
    st.title("KB 부동산 보고서 AI 어드바이저")
    st.caption("2024 KB 부동산 보고서 기반 질의응답 시스템")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_chain" not in st.session_state:
        st.session_state.chat_chain = initialize_chain()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("부동산 관련 질문을 입력하세요"):

        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        chain = get_chain()

        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                response = chain.invoke(
                    {"question": prompt},
                    {"configurable": {"session_id": "streamlit_session"}}
                )
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()