# Generated by Django 4.2 on 2025-04-26 04:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("trips", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PackingList",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("generated", models.BooleanField(default=False)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                (
                    "trip",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="packing_list",
                        to="trips.trip",
                    ),
                ),
            ],
            options={
                "ordering": ["-last_updated"],
            },
        ),
        migrations.CreateModel(
            name="PackingItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("CLOTHING", "Clothing"),
                            ("TOILETRIES", "Toiletries"),
                            ("ELECTRONICS", "Electronics"),
                            ("DOCUMENTS", "Documents"),
                            ("MISC", "Miscellaneous"),
                        ],
                        max_length=20,
                    ),
                ),
                ("quantity", models.PositiveSmallIntegerField(default=1)),
                ("is_essential", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                ("for_day", models.DateField(blank=True, null=True)),
                ("custom_added", models.BooleanField(default=False)),
                ("completed", models.BooleanField(default=False)),
                (
                    "packing_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="packing.packinglist",
                    ),
                ),
            ],
            options={
                "ordering": ["category", "name"],
            },
        ),
    ]
