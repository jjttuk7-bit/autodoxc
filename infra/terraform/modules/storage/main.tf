variable "name_prefix" { type = string }

# 사용자 첨부 양식 + DA1 공식 양식 원본 저장
resource "aws_s3_bucket" "attachments" {
  bucket = "${var.name_prefix}-attachments"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket                  = aws_s3_bucket.attachments.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 프론트엔드 SPA 정적 호스팅
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.name_prefix}-frontend"
}

# TODO: CloudFront distribution (frontend) + OAC, ACM cert, WAF

output "attachments_bucket" { value = aws_s3_bucket.attachments.id }
output "frontend_bucket"    { value = aws_s3_bucket.frontend.id }
