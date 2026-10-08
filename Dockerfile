# 파이썬 최적화 경량화 베이스 이미지 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 파이썬 출력 버퍼링 해제 (로그가 실시간으로 호스팅 콘솔에 찍히도록!)
ENV PYTHONUNBUFFERED=1

# 시간대 한국(Asia/Seoul)으로 설정 (로그 시간 맞춤용)
ENV TZ=Asia/Seoul
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 필수 파이썬 라이브러리(pyrad) 설치
RUN pip install --no-cache-dir pyrad

# 파이썬 RADIUS 서버 코드 복사
COPY radius_server.py .

# UDP 1812 포트 외부 노출 명시
EXPOSE 1812/udp

# 서버 실행 명령!
CMD ["python3", "radius_server.py"]
