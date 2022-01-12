# Generated by Django 2.2.8 on 2021-12-07 08:05

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('models', '5605_searchexporthistory_downloadfile'),
    ]

    operations = [
        migrations.CreateModel(
            name='LatestResourceEdit',
            fields=[
                ('editlogid', models.UUIDField(default=uuid.uuid1, primary_key=True, serialize=False)),
                ('resourceinstanceid', models.TextField(blank=True, null=True)),
                ('edittype', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'latest_resource_edit',
                'managed': True,
            },
        ),
    ]
