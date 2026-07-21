from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from products.models import Product


SAMPLES = {
    Product.Category.DIGITAL: [
        ("아이폰 14 128GB", 620000),
        ("갤럭시 S23 자급제", 540000),
        ("맥북 에어 M1", 780000),
        ("아이패드 9세대", 330000),
        ("닌텐도 스위치 OLED", 270000),
        ("에어팟 프로 2세대", 185000),
        ("LG 울트라기어 모니터", 210000),
        ("다이슨 무선청소기 V10", 240000),
    ],
    Product.Category.FASHION: [
        ("나이키 에어포스 270", 65000),
        ("무신사 스탠다드 코트", 48000),
        ("폴로 랄프로렌 셔츠", 42000),
        ("닥터마틴 8홀 부츠", 89000),
        ("마르헨제이 숄더백", 38000),
        ("뉴에라 볼캡", 18000),
        ("카시오 빈티지 시계", 32000),
        ("실버 체인 목걸이", 25000),
    ],
    Product.Category.LIVING: [
        ("원목 사이드 테이블", 35000),
        ("이케아 스탠드 조명", 22000),
        ("락앤락 냄비 세트", 30000),
        ("발뮤다 토스터", 125000),
        ("무선 물걸레 청소기", 54000),
        ("라탄 수납 바구니 세트", 18000),
        ("메모리폼 좌식 의자", 28000),
        ("도자기 식기 4인 세트", 45000),
    ],
    Product.Category.HOBBY: [
        ("해리포터 전권 세트", 55000),
        ("LP 레코드 10장 묶음", 70000),
        ("뮤지컬 공연 티켓 2매", 120000),
        ("아이돌 공식 응원봉", 32000),
        ("루미큐브 보드게임", 17000),
        ("입문용 통기타", 95000),
        ("건담 프라모델 완성품", 45000),
        ("필름 카메라 미놀타", 110000),
    ],
    Product.Category.SPORTS: [
        ("알톤 하이브리드 자전거", 180000),
        ("코베아 4인용 텐트", 140000),
        ("네이처하이크 캠핑 의자 2개", 42000),
        ("블랙야크 등산 배낭", 38000),
        ("덤벨 20kg 세트", 55000),
        ("요가 매트와 폼롤러", 22000),
        ("캘러웨이 골프 웨지", 78000),
        ("인라인 스케이트", 48000),
    ],
    Product.Category.BEAUTY: [
        ("샤넬 코코 향수 50ml", 85000),
        ("설화수 기초 세트", 72000),
        ("다이슨 에어랩 롱배럴", 390000),
        ("유닉스 전문가용 드라이기", 35000),
        ("LED 피부관리 마스크", 110000),
        ("록시땅 핸드크림 세트", 24000),
        ("조말론 바디워시", 38000),
        ("아베다 헤어케어 세트", 44000),
    ],
    Product.Category.ETC: [
        ("반려견 이동 가방", 32000),
        ("고양이 자동 급식기", 45000),
        ("미개봉 비상식량 세트", 28000),
        ("무료 나눔 종이 쇼핑백", 1),
        ("차량용 공기청정기", 25000),
        ("여행용 캐리어 24인치", 55000),
        ("사무용 계산기", 8000),
        ("수제 캔들 재료 묶음", 18000),
    ],
}

SELLERS_BY_CATEGORY = {
    Product.Category.DIGITAL: ("ethan", "olivia", "mason"),
    Product.Category.FASHION: ("sophia", "liam", "ava"),
    Product.Category.LIVING: ("noah", "emma", "ethan"),
    Product.Category.HOBBY: ("mason", "sophia", "olivia"),
    Product.Category.SPORTS: ("liam", "ava", "noah"),
    Product.Category.BEAUTY: ("emma", "olivia", "sophia"),
    Product.Category.ETC: ("ethan", "noah", "ava"),
}
SAMPLE_BIO_TEMPLATE = "Tiny Market 시연용 판매자 {display_name}입니다."
SAMPLE_BIOS = {
    "ava": "캠핑과 패션 소품을 정리하고 있어요. 상태를 꼼꼼하게 안내합니다.",
    "emma": "생활용품과 뷰티 제품을 주로 판매합니다. 빠른 답변을 약속해요.",
    "ethan": "디지털 기기와 생활 잡화를 좋아하는 판매자입니다.",
    "liam": "스포츠 장비와 데일리 패션을 합리적인 가격에 나눕니다.",
    "mason": "전자기기와 취미 수집품을 안전하게 포장해 보내드려요.",
    "noah": "캠핑·생활용품 위주로 판매하며 직거래도 환영합니다.",
    "olivia": "디지털 기기, 취미용품, 뷰티 제품을 깨끗하게 관리합니다.",
    "sophia": "패션과 취미, 뷰티 아이템을 소개하는 판매자입니다.",
}


class Command(BaseCommand):
    help = "카테고리별 중고 상품 샘플 데이터를 중복 없이 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sample-password",
            help="샘플 판매자 로그인용 비밀번호입니다. 생략하면 로그인할 수 없는 계정으로 만듭니다.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        seller_names = sorted({name for names in SELLERS_BY_CATEGORY.values() for name in names})
        sellers = {}
        for username in seller_names:
            expected_bio = SAMPLE_BIOS[username]
            seller, created = User.objects.get_or_create(
                username=username,
                defaults={"bio": expected_bio},
            )
            legacy_bio = SAMPLE_BIO_TEMPLATE.format(display_name=username.title())
            if not created and seller.bio not in {expected_bio, legacy_bio}:
                raise CommandError(f"기존 사용자 '{username}'와 샘플 계정명이 충돌합니다.")
            if seller.bio != expected_bio:
                seller.bio = expected_bio
                seller.save(update_fields=["bio"])
            if options["sample_password"]:
                seller.set_password(options["sample_password"])
                seller.save(update_fields=["password"])
            elif created:
                seller.set_unusable_password()
                seller.save(update_fields=["password"])
            sellers[username] = seller

        created_count = 0
        reassigned_count = 0
        image_number = 1
        managed_seller_names = seller_names + ["sample_market"]
        for category, items in SAMPLES.items():
            category_label = dict(Product.Category.choices)[category]
            for index, (name, price) in enumerate(items, start=1):
                seller_name = SELLERS_BY_CATEGORY[category][(index - 1) % 3]
                seller = sellers[seller_name]
                product = Product.objects.filter(name=name, seller__username__in=managed_seller_names).first()
                was_created = product is None
                if was_created:
                    product = Product(name=name)
                elif product.seller_id != seller.pk:
                    reassigned_count += 1
                product.seller = seller
                product.category = category
                product.description = f"{category_label} 카테고리의 시연용 중고 상품입니다. 사용감은 있으나 정상 사용 가능하며, 상세 상태는 채팅으로 확인해 주세요."
                product.price = price
                if index in {3, 7, 8}:
                    product.sale_status = Product.SaleStatus.SOLD
                elif index == 6:
                    product.sale_status = Product.SaleStatus.RESERVED
                else:
                    product.sale_status = Product.SaleStatus.ON_SALE
                product.visibility_status = Product.Visibility.PUBLIC
                product.sample_image_path = f"images/products/item-{image_number:03}.png"
                product.save()
                created_count += int(was_created)
                image_number += 1

        self.stdout.write(self.style.SUCCESS(
            f"샘플 상품 준비 완료: 판매자 {len(sellers)}명, 신규 {created_count}개, 재배정 {reassigned_count}개, "
            f"전체 {sum(map(len, SAMPLES.values()))}개"
        ))
