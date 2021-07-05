include etc/environment.sh

shared: shared.package shared.deploy
shared.package:
	sam package -t ${SHARED_TEMPLATE} --output-template-file ${SHARED_OUTPUT} --s3-bucket ${S3BUCKET}
shared.deploy:
	sam deploy -t ${SHARED_OUTPUT} --stack-name ${SHARED_STACK} --parameter-overrides ${SHARED_PARAMS} --capabilities CAPABILITY_NAMED_IAM
