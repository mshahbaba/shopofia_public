#!/bin/bash

echo "Beginning Entrypoint script execution."


python main.py


echo "vm finished executing."


# Add this service account to the root of your source repo dir. It's a SA with the Log writter and Custom VM delete Role.
gcloud auth activate-service-account --key-file=[.json]


# Change this to your project
gcloud config set project "project-name"


gcloud logging write batch-execution "Hello world from $(hostname)."

gcloud logging write batch-workload "[$(hostname)]Exit status from python"

echo "Entrypoint script execution finished."

# Delete the VM
gcp_zone=$(curl -H Metadata-Flavor:Google http://metadata.google.internal/computeMetadata/v1/instance/zone -s | cut -d/ -f4)
echo ${gcp_zone}
gcloud compute instances delete "instance-1" --zone "us-central1-a" --quiet

