module "hem_lambda" {
  source              = "terraform-aws-modules/lambda/aws"
  version             = "~> 7.0"
  source_path         = "hello_world/"
  function_name       = "HelloWorldFunction"
  handler             = "app.lambda_handler"
  runtime             = "python3.9"
  create_sam_metadata = true
}
