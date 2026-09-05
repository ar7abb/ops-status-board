from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_TEMPLATE = ROOT / "ansible/roles/backup/templates/ops-status-board-backup.sh.j2"
BACKUP_TASKS = ROOT / "ansible/roles/backup/tasks/main.yml"
CLOUD_PLAYBOOK = ROOT / "ansible/playbooks/cloud.yml"


def test_backup_script_uploads_dump_and_checksum_with_kms() -> None:
    script = BACKUP_TEMPLATE.read_text()

    assert script.count("aws s3 cp") == 2
    assert '"${backup_file}"' in script
    assert '"${checksum_file}"' in script
    assert "--sse aws:kms" in script
    assert '--sse-kms-key-id "${kms_key_id}"' in script
    assert '--region "${aws_region}"' in script


def test_backup_role_rejects_missing_remote_configuration() -> None:
    tasks = BACKUP_TASKS.read_text()

    for variable in (
        "ops_backup_s3_bucket",
        "ops_backup_s3_prefix",
        "ops_backup_aws_region",
        "ops_backup_kms_key_id",
    ):
        assert f"{variable} | length > 0" in tasks


def test_cloud_playbook_reads_bucket_from_controller_environment() -> None:
    playbook = CLOUD_PLAYBOOK.read_text()

    assert "lookup('env', 'OPS_BACKUP_S3_BUCKET')" in playbook
    assert "ops_backup_aws_region: eu-north-1" in playbook
    assert "ops_backup_kms_key_id: alias/ops-status-board-lab-backups" in playbook
