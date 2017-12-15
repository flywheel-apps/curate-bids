# curate-bids
Flywheel Gear that curates files within a Flywheel project according to BIDS Spec


### Build the Image
To build the image:
```
git clone https://github.com/flywheel-apps/curate-bids
cd curate-bids
docker build -t flywheel/curate-bids .
```

### Run the Image Locally
The BIDS curation gear can be run locally with the following command. 
```
docker run -it --rm \
    -v /path/to/config:/flywheel/v0/config.json \
    flywheel/curate-bids

```

The `-v` flag in the above command mounts a local config file to the correct path within the Docker container.

Below is the template of the local config file (JSON file)
```
{
    "config" : {
        "project_label" : "<ENTER PROJECT LABEL TO CURATE>"
    },
    "inputs" : {
        "api_key" : {
            "base" : "api-key",
            "key" : "<PLACE YOUR API KEY HERE>"
        }
    }
}
```
