FROM centos:7
RUN cd /tmp && \
  yum install -y https://repo.ius.io/ius-release-el7.rpm \
    https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
  yum update -y
RUN yum install -y gcc python36u python36u-devel postgresql-devel openssl-devel
RUN groupadd -r shire && useradd -m --no-log-init -r -g shire shire
USER shire
RUN chown -R shire:shire /home/shire && pip3.6 install --user --upgrade pip poetry
WORKDIR /var/www/shire/current
ENV PATH="/home/shire/.cache/pypoetry/virtualenvs/bin:/home/shire/.local/bin:$PATH"
ADD pyproject.toml /var/www/shire/current/pyproject.toml
ADD poetry.lock /var/www/shire/current/poetry.lock
RUN poetry install
ENTRYPOINT ["poetry", "run"]
