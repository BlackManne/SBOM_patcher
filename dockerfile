# 使用基础镜像
FROM python:3.9.13

# 安装需要的系统工具
RUN apt-get update && apt-get install -y netcat

WORKDIR /SBOM

# 安装Python依赖
COPY requirements.txt /SBOM/requirements.txt

RUN pip install -r requirements.txt

# 复制Python项目到容器中
COPY . /SBOM

# 添加启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 暴露端口
EXPOSE 5000

# 设置容器启动时执行的命令
CMD ["bash", "start.sh"]