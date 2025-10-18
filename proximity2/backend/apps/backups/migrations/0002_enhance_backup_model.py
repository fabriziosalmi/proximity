# Generated manually for backup model enhancements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backups', '0001_initial'),  # Adjust based on your last migration
    ]

    operations = [
        migrations.RenameField(
            model_name='backup',
            old_name='filename',
            new_name='file_name',
        ),
        migrations.RenameField(
            model_name='backup',
            old_name='size_bytes',
            new_name='size',
        ),
        migrations.AlterField(
            model_name='backup',
            name='file_name',
            field=models.CharField(help_text='Backup filename on Proxmox storage', max_length=500),
        ),
        migrations.AlterField(
            model_name='backup',
            name='size',
            field=models.BigIntegerField(blank=True, help_text='Backup size in bytes', null=True),
        ),
        migrations.AlterField(
            model_name='backup',
            name='storage_name',
            field=models.CharField(default='local', help_text='Proxmox storage name where backup is stored', max_length=100),
        ),
        migrations.AlterField(
            model_name='backup',
            name='backup_type',
            field=models.CharField(
                choices=[('snapshot', 'Snapshot'), ('suspend', 'Suspend'), ('stop', 'Stop')],
                default='snapshot',
                help_text='Backup mode used',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='backup',
            name='compression',
            field=models.CharField(
                choices=[('zstd', 'Zstandard'), ('gzip', 'Gzip'), ('lzo', 'LZO')],
                default='zstd',
                help_text='Compression algorithm',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='backup',
            name='status',
            field=models.CharField(
                choices=[
                    ('creating', 'Creating'),
                    ('completed', 'Completed'),
                    ('failed', 'Failed'),
                    ('restoring', 'Restoring'),
                    ('deleting', 'Deleting')
                ],
                db_index=True,
                default='creating',
                help_text='Current backup status',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='backup',
            name='error_message',
            field=models.TextField(blank=True, help_text='Error message if backup failed', null=True),
        ),
        migrations.AddField(
            model_name='backup',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, help_text='Last status update'),
        ),
        migrations.AlterField(
            model_name='backup',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, help_text='When backup was initiated'),
        ),
        migrations.AlterField(
            model_name='backup',
            name='completed_at',
            field=models.DateTimeField(blank=True, help_text='When backup completed successfully', null=True),
        ),
        migrations.AddIndex(
            model_name='backup',
            index=models.Index(fields=['application', 'status'], name='backups_app_status_idx'),
        ),
        migrations.AddIndex(
            model_name='backup',
            index=models.Index(fields=['status', 'created_at'], name='backups_status_created_idx'),
        ),
    ]
