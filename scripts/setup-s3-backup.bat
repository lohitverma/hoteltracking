@echo off
echo Setting up S3 backup bucket...

REM Create the bucket
aws s3 mb s3://%BACKUP_S3_BUCKET% --region %AWS_DEFAULT_REGION%

REM Enable versioning
aws s3api put-bucket-versioning --bucket %BACKUP_S3_BUCKET% --versioning-configuration Status=Enabled

REM Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration --bucket %BACKUP_S3_BUCKET% --lifecycle-configuration file://../s3-lifecycle-policy.json

REM Enable encryption
aws s3api put-bucket-encryption --bucket %BACKUP_S3_BUCKET% --server-side-encryption-configuration "{\"Rules\": [{\"ApplyServerSideEncryptionByDefault\": {\"SSEAlgorithm\": \"AES256\"}}]}"

echo S3 backup bucket setup completed successfully!
