FROM centos:7
RUN yum update -y && yum install -y gcc https://repo.ius.io/ius-release-el7.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN yum install -y python36u python36u-devel postgresql-devel openssl-devel
RUN pip3.6 install --upgrade poetry
WORKDIR /app
ADD pyproject.toml /app/pyproject.toml
ADD poetry.lock /app/poetry.lock
RUN poetry install
