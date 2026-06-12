locals {
  name_prefix = "${var.project}-${var.environment}"
}

module "network" {
  source = "../../modules/network"

  name_prefix = local.name_prefix
  vpc_cidr    = var.vpc_cidr
  azs         = ["${var.region}a", "${var.region}c"]
}

module "database" {
  source = "../../modules/database"

  name_prefix        = local.name_prefix
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  instance_class     = "db.t4g.small"
  allocated_storage  = 20
}

module "compute" {
  source = "../../modules/compute"

  name_prefix        = local.name_prefix
  vpc_id             = module.network.vpc_id
  public_subnet_ids  = module.network.public_subnet_ids
  private_subnet_ids = module.network.private_subnet_ids
}

module "storage" {
  source = "../../modules/storage"

  name_prefix = local.name_prefix
}
