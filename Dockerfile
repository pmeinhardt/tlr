FROM python:2.7.10

RUN apt-get update

# Build dependencies

RUN apt-get install -y \
  bison \
  flex \
  gtk-doc-tools \
  libtool \
  swig

RUN rm -rf /var/lib/apt/lists/*

# Download and compile sources

RUN set -x \
  && curl -sSL "http://purl.org/net/dajobe/gnupg.asc" -o dajobe.gpg \
  && gpg --import dajobe.gpg \
  && rm dajobe.gpg

RUN set -x \
  && mkdir -p /usr/src/raptor \
  && curl -sS "http://download.librdf.org/source/raptor2-2.0.15.tar.gz" -o raptor.tar.gz \
  && curl -sS "http://download.librdf.org/source/raptor2-2.0.15.tar.gz.asc" -o raptor.tar.gz.asc \
  && gpg --verify raptor.tar.gz.asc \
  && tar -xz -C /usr/src/raptor --strip-components=1 -f raptor.tar.gz \
  && rm raptor.tar.gz* \
  && cd /usr/src/raptor \
  && ./autogen.sh \
  && make \
  && make install \
  && rm -rf /usr/src/raptor

RUN set -x \
  && mkdir -p /usr/src/rasqal \
  && curl -sS "http://download.librdf.org/source/rasqal-0.9.33.tar.gz" -o rasqal.tar.gz \
  && curl -sS "http://download.librdf.org/source/rasqal-0.9.33.tar.gz.asc" -o rasqal.tar.gz.asc \
  && gpg --verify rasqal.tar.gz.asc \
  && tar -xz -C /usr/src/rasqal --strip-components=1 -f rasqal.tar.gz \
  && cd /usr/src/rasqal \
  && ./autogen.sh \
  && make \
  && make install \
  && rm -rf /usr/src/rasqal

RUN set -x \
  && mkdir -p /usr/src/redland \
  && curl -sS "http://download.librdf.org/source/redland-1.0.17.tar.gz" -o redland.tar.gz \
  && curl -sS "http://download.librdf.org/source/redland-1.0.17.tar.gz.asc" -o redland.tar.gz.asc \
  && gpg --verify redland.tar.gz.asc \
  && tar -xz -C /usr/src/redland --strip-components=1 -f redland.tar.gz \
  && cd /usr/src/redland \
  && ./autogen.sh \
  && make \
  && make install \
  && rm -rf /usr/src/redland

RUN set -x \
  && mkdir -p /usr/src/redland-bindings \
  && curl -sS "http://download.librdf.org/source/redland-bindings-1.0.17.1.tar.gz" -o redland-bindings.tar.gz \
  && curl -sS "http://download.librdf.org/source/redland-bindings-1.0.17.1.tar.gz.asc" -o redland-bindings.tar.gz.asc \
  && gpg --verify redland-bindings.tar.gz.asc \
  && tar -xz -C /usr/src/redland-bindings --strip-components=1 -f redland-bindings.tar.gz \
  && cd /usr/src/redland-bindings \
  && ./autogen.sh --with-python \
  && make \
  && make install \
  && rm -rf /usr/src/redland-bindings

# Clean-up

RUN apt-get remove -y \
  bison \
  flex \
  gtk-doc-tools \
  libtool \
  swig

ENV LD_LIBRARY_PATH /usr/local/lib:$LD_LIBRARY_PATH

# Application setup

RUN useradd -ms /bin/bash tailr

RUN mkdir /home/tailr/app

WORKDIR /home/tailr/app

ADD requirements.txt /home/tailr/app/requirements.txt

RUN pip install -r requirements.txt

ADD . /home/tailr/app

RUN chown -R tailr:tailr /home/tailr/app

USER tailr

EXPOSE 5000

CMD python app.py
