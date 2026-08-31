# Terraform network, IAM, and SSM design

This document explains the AWS foundation defined during M09-T03. The configuration is declarative and has not been planned or applied. It creates no EC2 instance by itself.

## Mental model

Think of this foundation as preparing a secured property before placing a building on it:

- the VPC is the property's private network boundary;
- the subnet is one smaller address range inside that boundary;
- the route table and internet gateway provide a path to public internet destinations;
- the security group is the instance-level network allow-list;
- the instance profile carries the EC2 instance's IAM role;
- the SSM managed policy permits the agent on the future instance to communicate with AWS Systems Manager.

The future EC2 instance is the building. It is intentionally absent from this task.

## Network path

The VPC uses `10.20.0.0/16`. Its public subnet uses `10.20.1.0/24` in one Stockholm Availability Zone. These are private IP address ranges; the word *public* describes routing, not the numbers themselves.

The subnet is associated with a route table whose default IPv4 route (`0.0.0.0/0`) points to an internet gateway. Automatic public IPv4 assignment is disabled. A later compute task must make an explicit, cost-reviewed decision before assigning a public address to an EC2 instance.

The instance security group has:

- no inbound rules, including no SSH rule on port 22;
- one outbound TCP rule for HTTPS on port 443.

Outbound HTTPS lets the SSM Agent initiate connections to AWS Systems Manager and later reach approved HTTPS package or image sources. Public SSM endpoints do not have one stable destination CIDR for a security-group rule, so the rule currently permits TCP/443 to `0.0.0.0/0`. This cost-conscious lab exception is documented in code and expires for reassessment on 2027-02-28. Private VPC endpoints or managed destination controls can be reconsidered later.

## IAM and Session Manager path

The trust policy allows the EC2 service to assume the instance role. The role has the AWS-managed `AmazonSSMManagedInstanceCore` policy, which grants the machine-side permissions needed by the SSM Agent. An instance profile contains that role and is the object a future EC2 instance will receive.

The connection flow is:

```text
Future EC2 instance
  -> instance profile
  -> IAM role with AmazonSSMManagedInstanceCore
  -> SSM Agent initiates outbound HTTPS on TCP/443
  -> regional AWS Systems Manager endpoints
```

No inbound SSH connection is required because the agent initiates the connection from the instance. The human operator still needs separate IAM permission to request a Session Manager session; the instance role does not grant that permission to a person.

## Current boundary and recovery

M09-T03 defines only the network and machine identity foundation. It does not define an `aws_instance`, EBS workload volume, public IPv4 assignment, application deployment, or human Session Manager policy. No workload plan or apply belongs to this task.

Because Terraform will manage these resources later, permanent changes should go through reviewed configuration rather than undocumented console edits. Before any future apply, review the saved plan, cost implications, remote-state locking, and the exact AWS identity and Region. Recovery is then based on correcting the configuration and applying a reviewed replacement plan rather than relying on manual reconstruction.
