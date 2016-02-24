require 'aws-sdk' #version 2
require 'digest'

Aws.config.update({
  region: 'us-west-2',
  credentials: Aws::Credentials.new('akid', 'secret')
})
s3 = Aws::S3::Resource.new(region: 'us-east-1')     
BUCKET = s3.bucket('bucketname')

ROOT_DIR = '_site'

IGNORE_FILES = ['Gemfile','Gemfile.lock','s3_upload.rb','s3_upload_config.rb']