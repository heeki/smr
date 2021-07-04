include etc/environment.sh

ingest: ingest.package ingest.deploy
ingest.package:
	sam package -t ${INGEST_TEMPLATE} --output-template-file ${INGEST_OUTPUT} --s3-bucket ${S3BUCKET}
ingest.deploy:
	sam deploy -t ${INGEST_OUTPUT} --stack-name ${INGEST_STACK} --parameter-overrides ${INGEST_PARAMS} --capabilities CAPABILITY_NAMED_IAM
ingest.local.invoke:
	sam local invoke -t ${INGEST_TEMPLATE} --parameter-overrides ${INGEST_PARAMS} --env-vars etc/envvars.json -e etc/event.json Fn | jq
ingest.local.api:
	sam local start-api -t ${INGEST_TEMPLATE} --parameter-overrides ${INGEST_PARAMS} --env-vars etc/envvars.json
ingest.invoke:
	aws --profile ${PROFILE} lambda invoke --function-name ${OUT_FN} --invocation-type RequestResponse --payload file://etc/event.json --cli-binary-format raw-in-base64-out --log-type Tail tmp/fn.json | jq "." > tmp/response.json
	cat tmp/response.json | jq -r ".LogResult" | base64 --decode
	cat tmp/fn.json | jq