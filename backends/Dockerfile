# Python 3.11-slim을 기반 이미지로 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 파일을 컨테이너에 복사
COPY requirements.txt .

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 코드를 컨테이너에 복사
COPY . .

# 8000번 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python3", "main.py"]
