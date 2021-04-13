# curate-bids

# FROM flywheel/curate-bids:GEAR-743-add-template-selection-feature
# FROM flywheel/bids-client:release-candidate
# FROM flywheel/bids-client:release-candidate.5734fdb5
# FROM flywheel/bids-client:GEAR-426-enhanced-logging
FROM flywheel/bids-client:release-candidate
MAINTAINER Flywheel <support@flywheel.io>

# Install JQ to parse config file
RUN apk add --no-cache jq

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
RUN mkdir -p ${FLYWHEEL}
COPY run.py ${FLYWHEEL}/run.py
COPY manifest.json ${FLYWHEEL}/manifest.json

# Set the command for local runs
CMD python3 /flywheel/v0/run.py
