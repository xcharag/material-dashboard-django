from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0014_consultationattachment_openai_file_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientaithread',
            name='context_consult_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='patientaithread',
            name='context_note_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='patientaithread',
            name='context_attachment_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='patientaithread',
            name='context_last_consultation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='pages.consultation'),
        ),
    ]
