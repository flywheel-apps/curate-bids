# curate-bids

FROM python:2.7
MAINTAINER Flywheel <support@flywheel.io>

# Install JQ to parse config file
RUN apt-get update && apt-get -y install jq

# Install jsonschema
RUN pip install jsonschema==2.6.0

# Install python SDK
RUN pip install https://github.com/flywheel-io/sdk/releases/download/0.2.0/flywheel-0.2.0-py2-none-linux_x86_64.whl

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

# Copy code into place
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/curate_bids.py?token=AWK3zPF-uXts9N-9SH9hYBXgQVKcQpE3ks5aPSPgwA%3D%3D ${FLYWHEEL}/curate_bids.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/bidsify_flywheel.py?token=AWK3zNW2vO49Umrxq8YgLsH6lUlU794eks5aPSjgwA%3D%3D ${FLYWHEEL}/supporting_files/bidsify_flywheel.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/utils.py?token=AWK3zM-WkIsWINlhAn2u7N1fdOMqltsJks5aPSkBwA%3D%3D ${FLYWHEEL}/supporting_files/utils.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/__init__.py?token=AWK3zKrpvdr5jHH65Vo6cKxQmSR77yoPks5aPTCvwA%3D%3D ${FLYWHEEL}/supporting_files/__init__.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/classifications.py?token=AWK3zEbMM0Y8QhLza2tgVU_3_PoZMppiks5aPTD_wA%3D%3D ${FLYWHEEL}/supporting_files/classifications.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/templates.py?token=AWK3zCCHOpwwpUGST9EJUdJ8ZCmuP45iks5aPTFPwA%3D%3D ${FLYWHEEL}/supporting_files/templates.py


RUN chmod +x ${FLYWHEEL}/curate_bids.py
RUN chmod +x ${FLYWHEEL}/supporting_files/bidsify_flywheel.py
RUN chmod +x ${FLYWHEEL}/supporting_files/utils.py
RUN chmod +x ${FLYWHEEL}/supporting_files/classifications.py
RUN chmod +x ${FLYWHEEL}/supporting_files/templates.py
RUN chmod +x ${FLYWHEEL}/supporting_files/__init__.py

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/run"]