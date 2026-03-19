FROM python:3.11-slim

# 添加国内 Debian 镜像源
RUN sed -i 's|http://deb.debian.org|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|http://deb.debian.org|https://mirrors.ustc.edu.cn|g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 添加 pip 国内镜像源（关键！）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data/raw /app/data/processed /app/data/reports

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
