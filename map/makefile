include etc/environment.sh

map: map.package map.deploy
map.package:
	sam package -t ${MAP_TEMPLATE} --output-template-file ${MAP_OUTPUT} --s3-bucket ${S3BUCKET}
map.deploy:
	sam deploy -t ${MAP_OUTPUT} --stack-name ${MAP_STACK} --parameter-overrides ${MAP_PARAMS} --capabilities CAPABILITY_NAMED_IAM
map.local.invoke:
	sam local invoke -t ${MAP_TEMPLATE} --parameter-overrides ${MAP_PARAMS} --env-vars etc/envvars.json -e etc/event.json Fn | jq
map.local.api:
	sam local start-api -t ${MAP_TEMPLATE} --parameter-overrides ${MAP_PARAMS} --env-vars etc/envvars.json
map.invoke:
	aws --profile ${PROFILE} lambda invoke --function-name ${OUT_FN} --invocation-type RequestResponse --payload file://etc/event.json --cli-binary-format raw-in-base64-out --log-type Tail tmp/fn.json | jq "." > tmp/response.json
	cat tmp/response.json | jq -r ".LogResult" | base64 --decode
	cat tmp/fn.json | jq