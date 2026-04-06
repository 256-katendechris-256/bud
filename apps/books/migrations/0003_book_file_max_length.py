from django.core.validators import FileExtensionValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_book_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='books/pdfs/',
                max_length=500,
                validators=[FileExtensionValidator(['pdf'])],
            ),
        ),
    ]
