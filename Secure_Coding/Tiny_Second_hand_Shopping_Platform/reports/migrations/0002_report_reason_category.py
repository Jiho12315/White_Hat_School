from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reports", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="report",
            name="reason_category",
            field=models.CharField(
                choices=[
                    ("FRAUD", "사기 또는 허위 판매"),
                    ("PROHIBITED", "판매 금지 품목"),
                    ("COUNTERFEIT", "위조품 또는 모조품"),
                    ("INAPPROPRIATE", "부적절한 상품 정보"),
                    ("SPAM", "도배 또는 광고"),
                    ("OTHER", "기타"),
                ],
                default="OTHER",
                max_length=20,
            ),
        ),
    ]
