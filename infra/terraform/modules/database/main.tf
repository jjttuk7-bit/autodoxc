variable "name_prefix"        { type = string }
variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "instance_class"     { type = string }
variable "allocated_storage"  { type = number }

resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

# RDS Postgres + pgvector (extension은 첫 connection 시 CREATE EXTENSION 실행)
resource "aws_db_instance" "this" {
  identifier              = "${var.name_prefix}-pg"
  engine                  = "postgres"
  engine_version          = "16.4"
  instance_class          = var.instance_class
  allocated_storage       = var.allocated_storage
  storage_encrypted       = true
  db_subnet_group_name    = aws_db_subnet_group.this.name
  vpc_security_group_ids  = [aws_security_group.db.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  backup_retention_period = 7

  # 비밀번호는 Secrets Manager에서 데이터 소스로 가져오는 게 표준
  username = "autodoxc"
  password = "TBD-from-secrets-manager"

  tags = { Name = "${var.name_prefix}-pg" }
}

resource "aws_security_group" "db" {
  name        = "${var.name_prefix}-db-sg"
  vpc_id      = var.vpc_id
  description = "Postgres access from compute layer"

  # ingress는 compute 모듈의 task SG에서 허용 (별도 wire-up 필요)
}

output "endpoint" { value = aws_db_instance.this.endpoint }
output "db_sg_id" { value = aws_security_group.db.id }
