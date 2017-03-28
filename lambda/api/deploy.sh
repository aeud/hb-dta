DEV_PATH=$HOME/Sites/hb/dota/lambda/api
S3_KEY=bot

LAMBDA_NAME=botAPIMess
LAMBDA_NAME_2=botAPIProcess

ZIP_PATH=/tmp/lambda.zip
rm $ZIP_PATH
cd $DEV_PATH/venv/lib/python2.7/site-packages
zip -r9 $ZIP_PATH *
cd $DEV_PATH
zip -g $ZIP_PATH lambda.py

aws s3 cp $ZIP_PATH s3://lx-dwh/$S3_KEY.zip
aws lambda update-function-code --function-name $LAMBDA_NAME --s3-bucket lx-dwh --s3-key $S3_KEY.zip
aws lambda update-function-code --function-name $LAMBDA_NAME_2 --s3-bucket lx-dwh --s3-key $S3_KEY.zip

