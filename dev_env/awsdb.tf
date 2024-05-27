terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.22.0"
    }
  }
}

# Summon some API
data "aws_secretsmanager_secret_version" "creds" {
  secret_id = "db-credsv2"
}

# Instantiating locals
locals {
  db_creds = jsondecode(
    data.aws_secretsmanager_secret_version.creds.secret_string
  )
}

# Now creating our resources
provider "postgresql" {
  host            = aws_db_instance.postgrespgadmin.address // Corrected the resource reference
  port            = var.port
  database        = var.database
  username        = local.db_creds.username
  password        = local.db_creds.password
  sslmode         = "require"
  connect_timeout = 15
}

# Create a security group to allow traffic to our db instance
resource "aws_security_group" "postgresdb" {
  name = "postgresdb"

  ingress {
    from_port   = var.port
    to_port     = var.port
    protocol    = "tcp"
    description = "PostgreSQL"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port        = var.port
    to_port          = var.port
    protocol         = "tcp"
    description      = "PostgreSQL"
    ipv6_cidr_blocks = ["::/0"]
  }
}

# Create an AWS DB instance
resource "aws_db_instance" "postgrespgadmin" {
  allocated_storage      = 10
  db_name                = var.database
  engine                 = "postgres"
  engine_version         = "12"
  instance_class         = "db.t3.micro"
  username               = local.db_creds.username
  password               = local.db_creds.password
  publicly_accessible    = true
  parameter_group_name   = "default.postgres12"
  vpc_security_group_ids = [aws_security_group.postgresdb.id]
  skip_final_snapshot    = true
}

# Create a role
resource "postgresql_role" "user_name" {
  name                = local.db_creds.username
  login               = true
  password            = local.db_creds.password
  encrypted_password  = true
  create_database     = true
  create_role         = true
  skip_reassign_owned = true
}
