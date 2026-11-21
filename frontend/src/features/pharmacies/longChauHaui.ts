/** Addresses and the shared customer hotline are published by FPT Long Châu.
 * Store coordinates are intentionally omitted because the official pages do
 * not publish coordinates and nearby geocoders returned imprecise matches.
 */
export type VerifiedPharmacy = {
  id: string;
  name: string;
  address: string;
  phone?: string;
  phoneKind?: "chain_hotline";
  sourceUrl: string;
};

export const LONG_CHAU_HAUI: VerifiedPharmacy[] = [
  {
    id: "long-chau-7-van-tri",
    name: "Long Châu 7 Phố Văn Trì",
    address: "7 Phố Văn Trì, P. Tây Tựu, Hà Nội",
    sourceUrl: "https://nhathuoclongchau.com.vn/he-thong-cua-hang/7-pho-van-tri-p-minh-khai-q-bac-tu-liem-tp-ha-noi",
  },
  {
    id: "long-chau-160-tay-tuu",
    name: "Long Châu 160 Tây Tựu",
    address: "160 Tây Tựu, P. Tây Tựu, Hà Nội",
    sourceUrl: "https://nhathuoclongchau.com.vn/he-thong-cua-hang/lc-hni-160-tay-tuu",
  },
  {
    id: "long-chau-64-phu-dien",
    name: "Long Châu 64 Phú Diễn",
    address: "64 Phú Diễn, P. Phú Diễn, Hà Nội",
    sourceUrl: "https://nhathuoclongchau.com.vn/he-thong-cua-hang/64-phu-dien-p-phu-dien-q-bac-tu-liem-tp-ha-noi",
  },
  {
    id: "long-chau-363-hoang-cong-chat",
    name: "Long Châu 363 Hoàng Công Chất",
    address: "363 Hoàng Công Chất, P. Phú Diễn, Hà Nội",
    sourceUrl: "https://nhathuoclongchau.com.vn/he-thong-cua-hang/ha-noi/phuong-phu-dien",
  },
  {
    id: "long-chau-24-chua-but-moc",
    name: "Long Châu 24 Chùa Bụt Mọc",
    address: "24 Đường Chùa Bụt Mọc, P. Phú Diễn, Hà Nội",
    sourceUrl: "https://nhathuoclongchau.com.vn/he-thong-cua-hang/ha-noi/phuong-phu-dien",
  },
  {
    id: "long-chau-248-nguyen-van-giap",
    name: "Long Châu 248 Nguyễn Văn Giáp",
    address: "248 Nguyễn Văn Giáp, P. Từ Liêm, Hà Nội",
    sourceUrl: "https://nhathuoclongchau.com.vn/he-thong-cua-hang/248-nguyen-van-giap-p-cau-dien-q-nam-tu-liem-tp-ha-noi",
  },
];

export const LONG_CHAU_HOTLINE = "1800 6928";

export function verifiedDirectionsUrl(address: string, origin?: { latitude: number; longitude: number }): string {
  const params = new URLSearchParams({
    api: "1",
    destination: `Nhà thuốc FPT Long Châu, ${address}`,
  });
  if (origin) params.set("origin", `${origin.latitude},${origin.longitude}`);
  return `https://www.google.com/maps/dir/?${params}`;
}
