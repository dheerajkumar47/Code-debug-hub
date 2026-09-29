FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bidsmith ./bidsmith
COPY profile ./profile
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "bidsmith", "serve", "--port", "8000"]
