# Load environment variables
$env:AWS_ACCESS_KEY_ID = (Get-Content ../.env.production | Select-String "AWS_ACCESS_KEY_ID=(.*)").Matches.Groups[1].Value
$env:AWS_SECRET_ACCESS_KEY = (Get-Content ../.env.production | Select-String "AWS_SECRET_ACCESS_KEY=(.*)").Matches.Groups[1].Value
$env:AWS_DEFAULT_REGION = (Get-Content ../.env.production | Select-String "AWS_DEFAULT_REGION=(.*)").Matches.Groups[1].Value
$BUCKET_NAME = (Get-Content ../.env.production | Select-String "BACKUP_S3_BUCKET=(.*)").Matches.Groups[1].Value

# Create S3 bucket if it doesn't exist
Write-Host "Creating S3 bucket if it doesn't exist..."
aws s3 mb "s3://$BUCKET_NAME" --region $env:AWS_DEFAULT_REGION

# Enable versioning
Write-Host "Enabling versioning..."
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled

# Set lifecycle policy
Write-Host "Setting lifecycle policy..."
aws s3api put-bucket-lifecycle-configuration --bucket $BUCKET_NAME --lifecycle-configuration file://../s3-lifecycle-policy.json

# Enable encryption
Write-Host "Enabling encryption..."
aws s3api put-bucket-encryption --bucket $BUCKET_NAME --server-side-encryption-configuration '{
    "Rules": [
        {
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }
    ]
}'

Write-Host "S3 backup bucket setup completed successfully!"
