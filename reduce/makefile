include etc/environment.sh

reduce: reduce.package reduce.deploy
reduce.package:
	aws s3 cp iac/asl.json s3://${P_ASLBUCKET}/${P_ASLKEY}
	sam package -t ${REDUCE_TEMPLATE} --output-template-file ${REDUCE_OUTPUT} --s3-bucket ${S3BUCKET}
reduce.deploy:
	sam deploy -t ${REDUCE_OUTPUT} --stack-name ${REDUCE_STACK} --parameter-overrides ${REDUCE_PARAMS} --capabilities CAPABILITY_NAMED_IAM
reduce.local.invoke:
	sam local invoke -t ${REDUCE_TEMPLATE} --parameter-overrides ${REDUCE_PARAMS} --env-vars etc/envvars.json -e etc/event.json FnGate | jq
reduce.local.api:
	sam local start-api -t ${REDUCE_TEMPLATE} --parameter-overrides ${REDUCE_PARAMS} --env-vars etc/envvars.json
reduce.invoke:
	aws --profile ${PROFILE} lambda invoke --function-name ${OUT_FN} --invocation-type RequestResponse --payload file://etc/event.json --cli-binary-format raw-in-base64-out --log-type Tail tmp/fn.json | jq "." > tmp/response.json
	cat tmp/response.json | jq -r ".LogResult" | base64 --decode
	cat tmp/fn.json | jq