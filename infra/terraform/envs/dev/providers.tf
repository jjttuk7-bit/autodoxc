terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  # backend "s3" — 부트스트랩 후 활성화
  # backend "s3" {
  #   bucket         = "autodoxc-tfstate"
  #   key            = "envs/dev/terraform.tfstate"
  #   region         = "ap-northeast-2"
  #   dynamodb_table = "autodoxc-tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = "autodoxc"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}
