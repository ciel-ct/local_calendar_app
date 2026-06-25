FROM python:3.11-alpine

WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 鍵ファイルやソースコードをコピー
COPY credentials.json .
COPY main.py .

# FastAPIを起動（ポート8000で待ち受けます）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]