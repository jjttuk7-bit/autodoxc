output "vpc_id" {
  value = module.network.vpc_id
}

output "alb_dns_name" {
  value = module.compute.alb_dns_name
}

output "db_endpoint" {
  value     = module.database.endpoint
  sensitive = true
}

output "attachments_bucket" {
  value = module.storage.attachments_bucket
}
