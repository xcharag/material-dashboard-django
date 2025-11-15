from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0013_patientaithread_patientaimessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultationattachment',
            name='openai_file_id',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
    ]
