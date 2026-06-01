from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0019_patientaithread_conversation_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientaithread',
            name='openai_vector_store_id',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
