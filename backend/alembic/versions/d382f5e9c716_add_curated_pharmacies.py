"""Store verified pharmacies near HaUI campus 1.

Revision ID: d382f5e9c716
Revises: 9b4f8c12a011
"""

from alembic import op
import sqlalchemy as sa

revision = "d382f5e9c716"
down_revision = "9b4f8c12a011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    table = op.create_table(
        "curated_pharmacies",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("area", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(300), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("phone_kind", sa.String(30), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
    )
    op.create_index("ix_curated_pharmacies_area", "curated_pharmacies", ["area"])
    base = "https://nhathuoclongchau.com.vn/he-thong-cua-hang/"
    ward = base + "ha-noi/phuong-phu-dien"
    stores = [
        ("long-chau-7-van-tri", "Long Châu 7 Phố Văn Trì", "7 Phố Văn Trì, P. Tây Tựu, Hà Nội", base + "7-pho-van-tri-p-minh-khai-q-bac-tu-liem-tp-ha-noi"),
        ("long-chau-160-tay-tuu", "Long Châu 160 Tây Tựu", "160 Tây Tựu, P. Tây Tựu, Hà Nội", base + "lc-hni-160-tay-tuu"),
        ("long-chau-64-phu-dien", "Long Châu 64 Phú Diễn", "64 Phú Diễn, P. Phú Diễn, Hà Nội", base + "64-phu-dien-p-phu-dien-q-bac-tu-liem-tp-ha-noi"),
        ("long-chau-363-hoang-cong-chat", "Long Châu 363 Hoàng Công Chất", "363 Hoàng Công Chất, P. Phú Diễn, Hà Nội", ward),
        ("long-chau-24-chua-but-moc", "Long Châu 24 Chùa Bụt Mọc", "24 Đường Chùa Bụt Mọc, P. Phú Diễn, Hà Nội", ward),
        ("long-chau-248-nguyen-van-giap", "Long Châu 248 Nguyễn Văn Giáp", "248 Nguyễn Văn Giáp, P. Từ Liêm, Hà Nội", base + "248-nguyen-van-giap-p-cau-dien-q-nam-tu-liem-tp-ha-noi"),
    ]
    op.bulk_insert(table, [
        {
            "id": store_id,
            "area": "haui-campus-1",
            "name": name,
            "address": address,
            "phone": "1800 6928",
            "phone_kind": "chain_hotline",
            "source_url": source_url,
        }
        for store_id, name, address, source_url in stores
    ])


def downgrade() -> None:
    op.drop_index("ix_curated_pharmacies_area", table_name="curated_pharmacies")
    op.drop_table("curated_pharmacies")
