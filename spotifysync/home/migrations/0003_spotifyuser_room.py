# Generated by Django 4.0 on 2021-12-18 07:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('room', '0003_initial'),
        ('home', '0002_rename_auth_token_spotifyuser_access_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='spotifyuser',
            name='room',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='room.room'),
        ),
    ]
