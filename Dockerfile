# 使用多阶段构建
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 复制项目文件
COPY *.py .
COPY *.service .
COPY *.md .
COPY app ./app
COPY logs ./logs

# 最终阶段
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# 设置环境变量
ENV PATH="/root/.local/bin:${PATH}"
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 8001

# 定义启动命令
CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]