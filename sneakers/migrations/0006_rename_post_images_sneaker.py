# Generated by Django 3.2.12 on 2022-09-18 13:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sneakers', '0005_auto_20220918_2204'),
    ]

    operations = [
        migrations.RenameField(
            model_name='images',
            old_name='post',
            new_name='sneaker',
        ),
    ]
