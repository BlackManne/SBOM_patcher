# 使用基础镜像
FROM ubuntu:18.04

# 设置环境变量
ENV MONGO_VERSION 4.4
ENV ES_VERSION 8.12.1
ENV PYTHON_VERSION 3.9.13

# 创建工作目录
RUN mkdir /SBOM

VOLUME /SBOM

# 安装依赖、Python、MongoDB和Elasticsearch
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# 安装特定版本的Python
RUN wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz \
    && tar xzf Python-$PYTHON_VERSION.tgz \
    && cd Python-$PYTHON_VERSION \
    && ./configure --enable-optimizations && make && make altinstall \
    && cd .. \
    && rm Python-$PYTHON_VERSION.tgz

# 安装MongoDB
RUN apt-get install -y mongodb-org

# 安装Elasticsearch
RUN wget https://artifacts.elastic.co/downloads/elasticsearch/$ES_VERSION/elasticsearch-$ES_VERSION-linux-x86_64.tar.gz \
    && tar -xzf elasticsearch-$ES_VERSION-linux-x86_64.tar.gz \
    && mv elasticsearch-$ES_VERSION /usr/local/elasticsearch \
    && rm elasticsearch-$ES_VERSION-linux-x86_64.tar.gz

WORKDIR /SBOM

# 安装Python依赖
COPY requirements.txt /SBOM/requirements.txt

RUN pip3 install -r requirements.txt

# 复制Python项目到容器中
COPY . /SBOM

# 添加启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

# 暴露端口
EXPOSE 27017 9200 5000 #SBOM运行在5000端口

# 设置容器启动时执行的命令
CMD ["./start.sh"]