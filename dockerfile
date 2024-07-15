# 使用Python 3.9作为基础镜像
FROM python:3.9

# 设置工作目录
WORKDIR /SBOM

# 将当前目录下全部文件复制到容器中
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露Flask应用的端口
EXPOSE 5000

# 设置入口点,启动Flask应用
CMD ["python", "SBOM.py"]

# docker命令如下
# docker build -t docker push my-python-service:latest .
# docker push SBOM:latest