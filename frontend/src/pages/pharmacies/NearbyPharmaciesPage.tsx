import React, { useState } from "react";
import { ExternalLink, MapPin, Navigation, Phone, RefreshCw } from "lucide-react";
import { Coordinates, directionsUrl, findAddress, findNearbyPharmacies, nearbySearchUrl, Pharmacy } from "../../features/pharmacies/search";

export const NearbyPharmaciesPage: React.FC = () => {
  const [origin, setOrigin] = useState<Coordinates | null>(null);
  const [items, setItems] = useState<Pharmacy[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [address, setAddress] = useState("");

  const searchAt = async (position: Coordinates) => {
    setOrigin(position);
    setItems([]);
    try {
      setItems(await findNearbyPharmacies(position));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Không tải được danh sách nhà thuốc.");
    } finally {
      setLoading(false);
    }
  };

  const searchAddress = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!address.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await searchAt(await findAddress(address));
    } catch (cause) {
      setLoading(false);
      setError(cause instanceof Error ? cause.message : "Không tìm được địa chỉ.");
    }
  };

  const locate = () => {
    if (!navigator.geolocation) {
      setError("Thiết bị không hỗ trợ lấy vị trí. Bạn có thể mở tìm kiếm trên bản đồ.");
      return;
    }
    setLoading(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      const position = { latitude: coords.latitude, longitude: coords.longitude };
      void searchAt(position);
    }, (cause) => {
      setLoading(false);
      setError(cause.code === 1
        ? "Bạn chưa cho phép truy cập vị trí. Hãy cấp quyền vị trí trong trình duyệt hoặc mở tìm kiếm trên bản đồ."
        : "Không xác định được vị trí. Hãy kiểm tra định vị của thiết bị rồi thử lại.");
    }, { enableHighAccuracy: false, timeout: 15_000, maximumAge: 60_000 });
  };

  return (
    <section style={{ maxWidth: 920, display: "grid", gap: 18 }}>
      <div>
        <h1 style={{ fontSize: "1.55rem" }}>Nhà thuốc gần bạn</h1>
        <p style={{ color: "var(--pm-text-secondary)" }}>
          Tìm nhà thuốc trong bán kính 5 km, xem địa chỉ, số điện thoại và đường đi.
        </p>
      </div>
      <form className="card" onSubmit={searchAddress} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <input className="input" style={{ flex: "1 1 250px" }} type="search" aria-label="Địa chỉ hoặc khu vực cần tìm" placeholder="Nhập địa chỉ hoặc khu vực, ví dụ: Quận 1, TP.HCM" value={address} onChange={(event) => setAddress(event.target.value)} />
        <button className="btn btn-secondary" type="submit" disabled={loading || !address.trim()}>Tìm theo địa chỉ</button>
      </form>
      <div className="card" style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <button type="button" className="btn btn-primary" onClick={locate} disabled={loading}>
          {loading ? <RefreshCw size={18} /> : <MapPin size={18} />}
          {loading ? "Đang tìm nhà thuốc..." : origin ? "Cập nhật vị trí" : "Tìm gần vị trí của tôi"}
        </button>
        <a className="btn btn-outline" href={nearbySearchUrl(origin ?? undefined)} target="_blank" rel="noopener noreferrer">
          <ExternalLink size={18} /> Tìm trên Google Maps
        </a>
        <span style={{ color: "var(--pm-text-secondary)", fontSize: ".85rem" }}>
          Chỉ truy cập vị trí khi bạn bấm tìm. Vị trí được gửi đến OpenStreetMap để tìm kết quả.
        </span>
      </div>
      {error && <div className="alert-banner alert-warning" role="alert">{error}</div>}
      {origin && !loading && !error && items.length === 0 &&
        <div className="card">Chưa tìm thấy nhà thuốc trong bán kính 5 km. Hãy thử tìm trên Google Maps.</div>}
      {items.length > 0 && <p style={{ color: "var(--pm-text-secondary)" }}>
        {items.length} nhà thuốc gần nhất · khoảng cách đường chim bay
      </p>}
      <div className="pharmacy-list">
        {items.map((pharmacy) => (
          <article className="card pharmacy-card" key={pharmacy.id}>
            <div>
              <h2 style={{ fontSize: "1.08rem" }}>{pharmacy.name}</h2>
              <p style={{ color: "var(--pm-primary)", fontWeight: 600 }}>
                {pharmacy.distanceKm < 1 ? `${Math.round(pharmacy.distanceKm * 1000)} m` : `${pharmacy.distanceKm.toFixed(1)} km`}
              </p>
              <p><MapPin size={16} aria-hidden="true" /> {pharmacy.address || "Chưa có địa chỉ chi tiết trong dữ liệu bản đồ"}</p>
              <p><Phone size={16} aria-hidden="true" /> {pharmacy.phone || "Chưa có số điện thoại trong dữ liệu bản đồ"}</p>
            </div>
            <div className="pharmacy-actions">
              {pharmacy.phone && <a className="btn btn-outline" href={`tel:${pharmacy.phone.replace(/[^\d+]/g, "")}`}>
                <Phone size={16} /> Gọi điện
              </a>}
              {origin && <a className="btn btn-primary" href={directionsUrl(origin, pharmacy)} target="_blank" rel="noopener noreferrer">
                <Navigation size={16} /> Chỉ đường
              </a>}
            </div>
          </article>
        ))}
      </div>
      <small style={{ color: "var(--pm-text-secondary)" }}>
        Dữ liệu địa điểm © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>.
        Thông tin địa chỉ, số điện thoại có thể chưa đầy đủ; hãy xác nhận trước khi đến.
      </small>
    </section>
  );
};
