# Generated by Django 3.2.12 on 2022-12-09 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_alter_kicks_retailpricekrw'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kicks',
            name='releaseDate',
            field=models.CharField(blank=True, default='2022-12-12', max_length=100, null=True),
        ),
    ]
