DEV_PATH=$HOME/Sites/hb/dta
# S3_KEY=bot
S3_BUCKET=tnl-lambdas

echo $AWS_ACCESS_KEY_ID

# LAMBDA_NAME_2=hbDtaBot

ZIP_PATH=/tmp/lambda.zip

source credentials

LAMBDA_NAME=hbDtaWS
FILE_NAME=hb_dta_ws.py
rm $ZIP_PATH
zip -g $ZIP_PATH $FILE_NAME
aws s3 cp $ZIP_PATH s3://$S3_BUCKET/$LAMBDA_NAME.zip
aws lambda update-function-code --function-name $LAMBDA_NAME --s3-bucket $S3_BUCKET --s3-key $LAMBDA_NAME.zip

LAMBDA_NAME=hbDtaBot
FILE_NAME=hb_dta_bot.py
rm $ZIP_PATH
cd $DEV_PATH/venv/lib/python2.7/site-packages
zip -r9 $ZIP_PATH *
cd $DEV_PATH
zip -g $ZIP_PATH $FILE_NAME
aws s3 cp $ZIP_PATH s3://$S3_BUCKET/$LAMBDA_NAME.zip
aws lambda update-function-code --function-name $LAMBDA_NAME --s3-bucket $S3_BUCKET --s3-key $LAMBDA_NAME.zip


# cd $DEV_PATH/venv/lib/python2.7/site-packages
# zip -r9 $ZIP_PATH *
# cd $DEV_PATH
# zip -g $ZIP_PATH lambda.py

# aws s3 cp $ZIP_PATH s3://lx-dwh/$S3_KEY.zip
# aws lambda update-function-code --function-name $LAMBDA_NAME --s3-bucket $S3_BUCKET --s3-key $S3_KEY.zip
# aws lambda update-function-code --function-name $LAMBDA_NAME_2 --s3-bucket $S3_BUCKET --s3-key $S3_KEY.zip

