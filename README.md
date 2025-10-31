# Streamlit 대시보드 로컬 실행 가이드

이 프로젝트는 인터넷 신문사 성과 분석 대시보드의 Streamlit 템플릿입니다.

## 1. 사전 준비

-   Python 3.8 이상이 설치되어 있어야 합니다.
-   `app.py`, `data.csv`, `requirements.txt` 파일이 모두 같은 폴더에 있어야 합니다.

## 2. 설치

터미널(명령 프롬프트)을 열고, 이 파일들이 있는 폴더로 이동합니다.

**a. (권장) 가상환경 생성 및 활성화**

```bash
# 가상환경 생성
python -m venv venv

# Windows에서 활성화
.\venv\Scripts\activate

# macOS/Linux에서 활성화
source venv/bin/activate