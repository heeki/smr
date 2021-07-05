include etc/environment.sh

flow: flow.package flow.deploy
flow.package:
	aws s3 cp iac/asl.json s3://${P_ASLBUCKET}/${P_ASLKEY}
	sam package -t ${FLOW_TEMPLATE} --output-template-file ${FLOW_OUTPUT} --s3-bucket ${S3BUCKET}
flow.deploy:
	sam deploy -t ${FLOW_OUTPUT} --stack-name ${FLOW_STACK} --parameter-overrides ${FLOW_PARAMS} --capabilities CAPABILITY_NAMED_IAM
flow.local.invoke:
	sam local invoke -t ${FLOW_TEMPLATE} --parameter-overrides ${FLOW_PARAMS} --env-vars etc/envvars.json -e etc/event.json Fn | jq
flow.local.api:
	sam local start-api -t ${FLOW_TEMPLATE} --parameter-overrides ${FLOW_PARAMS} --env-vars etc/envvars.json
flow.invoke:
	aws --profile ${PROFILE} stepfunctions start-execution --state-machine-arn ${OUT_SFN} --input file://etc/event.json | jq