# curate-bids

FROM python:2.7
MAINTAINER Flywheel <support@flywheel.io>

# Install JQ to parse config file
RUN apt-get update && apt-get -y install jq

# Install jsonschema and dateutil
RUN pip install jsonschema==2.6.0 python-dateutil==2.6.1

# Install python SDK
RUN pip install https://github.com/flywheel-io/sdk/releases/download/0.3.0/flywheel-0.3.0-py2-none-linux_x86_64.whl

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run ${FLYWHEEL}/run
COPY manifest.json ${FLYWHEEL}/manifest.json

# Copy code into place
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/curate_bids.py ${FLYWHEEL}/curate_bids.py

ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/__init__.py ${FLYWHEEL}/supporting_files/__init__.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/bidsify_flywheel.py ${FLYWHEEL}/supporting_files/bidsify_flywheel.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/classifications.py ${FLYWHEEL}/supporting_files/classifications.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/project_tree.py ${FLYWHEEL}/supporting_files/project_tree.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/resolver.py ${FLYWHEEL}/supporting_files/resolver.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/templates.py ${FLYWHEEL}/supporting_files/templates.py
ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/supporting_files/utils.py ${FLYWHEEL}/supporting_files/utils.py

ADD https://raw.githubusercontent.com/flywheel-io/bids-client/master/templates/bids-v1.json ${FLYWHEEL}/templates/bids-v1.json 

RUN chmod +x ${FLYWHEEL}/curate_bids.py
RUN chmod +x ${FLYWHEEL}/supporting_files/__init__.py
RUN chmod +x ${FLYWHEEL}/supporting_files/bidsify_flywheel.py
RUN chmod +x ${FLYWHEEL}/supporting_files/classifications.py
RUN chmod +x ${FLYWHEEL}/supporting_files/project_tree.py
RUN chmod +x ${FLYWHEEL}/supporting_files/resolver.py
RUN chmod +x ${FLYWHEEL}/supporting_files/templates.py
RUN chmod +x ${FLYWHEEL}/supporting_files/utils.py

# Set the entrypoint
ENTRYPOINT ["/flywheel/v0/run"]
