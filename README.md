# My notes

## Debugging
Debug config based on: 
- https://medium.com/@Consegna/aws-sam-local-debugging-lambda-and-api-gateway-with-breakpoints-demo-d5fea4172376
- https://github.com/microsoft/debugpy

## Deployment TODO

I think we should use [serverless.tf modules for the lambda
deployment](https://github.com/terraform-aws-modules/terraform-aws-lambda?tab=readme-ov-file#-deployment-package---create-or-use-existing).
By default these build and deploy the lambda packages during the terraform apply step. This won't work with the
terraform monorepo approach. Instead I should:
- Use the link above section to create a lambda function without a `create_package` step, instead targeting an existing
  S3 package in the MGT account.
  - Will need cross account permissions similar to Baringa.

## Development TODO

When I tried running a different demo JSON the CSV results converter failed. Need to test all the cases for this.