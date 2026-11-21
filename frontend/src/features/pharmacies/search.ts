export type Coordinates = { latitude: number; longitude: number };

export type Pharmacy = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  distanceKm: number;
  address: string | null;
  phone: string | null;
};

type OsmElement = {
  type: string;
  id: number;
  lat?: number;
  lon?: number;
  center?: { lat: number; lon: number };
  tags?: Record<string, string>;
};

type PhotonFeature = {
  properties?: Record<string, string | number>;
  geometry?: { coordinates?: number[] };
};

const ENDPOINTS = [
  "https://overpass.private.coffee/api/interpreter",
  "https://overpass-api.de/api/interpreter",
];
const RADIUS_METERS = 5000;
const cache = new Map<string, { time: number; items: Pharmacy[] }>();

function distanceKm(a: Coordinates, b: Coordinates): number {
  const rad = Math.PI / 180;
  const deltaLat = (b.latitude - a.latitude) * rad;
  const deltaLon = (b.longitude - a.longitude) * rad;
  const arc = Math.sin(deltaLat / 2) ** 2 +
    Math.cos(a.latitude * rad) * Math.cos(b.latitude * rad) * Math.sin(deltaLon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.min(1, Math.sqrt(arc)));
}

function addressFromTags(tags: Record<string, string>): string | null {
  const street = [tags["addr:housenumber"], tags["addr:street"]].filter(Boolean).join(" ");
  const address = [street, tags["addr:suburb"], tags["addr:district"], tags["addr:city"] || tags["addr:province"]]
    .filter(Boolean).join(", ");
  return address || tags["addr:full"] || null;
}

async function findPhotonPharmacies(origin: Coordinates): Promise<Pharmacy[]> {
  const params = new URLSearchParams({ q: "pharmacy", lat: String(origin.latitude), lon: String(origin.longitude), limit: "50" });
  const response = await fetch(`https://photon.komoot.io/api/?${params}`, { signal: AbortSignal.timeout(15_000) });
  if (!response.ok) throw new Error("Dịch vụ bản đồ đang bận.");
  const data = await response.json() as { features?: PhotonFeature[] };
  return (data.features ?? []).flatMap((feature) => {
    const point = feature.geometry?.coordinates;
    const properties = feature.properties ?? {};
    if (!point || point.length < 2 || properties.osm_value !== "pharmacy") return [];
    const [longitude, latitude] = point;
    const distance = distanceKm(origin, { latitude, longitude });
    if (!Number.isFinite(distance) || distance > RADIUS_METERS / 1000) return [];
    const address = [properties.housenumber, properties.street, properties.district, properties.city]
      .filter(Boolean).join(", ");
    return [{
      id: `photon-${properties.osm_type}-${properties.osm_id}`,
      name: String(properties.name || "Nhà thuốc"),
      latitude, longitude, distanceKm: distance,
      address: address || null,
      phone: typeof properties.phone === "string" ? properties.phone : null,
    }];
  }).sort((a, b) => a.distanceKm - b.distanceKm).slice(0, 30);
}

export async function findNearbyPharmacies(origin: Coordinates): Promise<Pharmacy[]> {
  if (!Number.isFinite(origin.latitude) || !Number.isFinite(origin.longitude) ||
      Math.abs(origin.latitude) > 90 || Math.abs(origin.longitude) > 180) {
    throw new Error("Vị trí hiện tại không hợp lệ.");
  }
  const key = `${origin.latitude.toFixed(2)},${origin.longitude.toFixed(2)}`;
  const cached = cache.get(key);
  if (cached && Date.now() - cached.time < 10 * 60_000) return cached.items;

  const query = `[out:json][timeout:20];(nwr(around:${RADIUS_METERS},${origin.latitude},${origin.longitude})["amenity"="pharmacy"];);out center tags;`;
  let data: { elements?: OsmElement[] } | null = null;
  for (const endpoint of ENDPOINTS) {
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
        body: new URLSearchParams({ data: query }),
        signal: AbortSignal.timeout(12_000),
      });
      if (response.ok) {
        data = await response.json() as { elements?: OsmElement[] };
        break;
      }
      if (response.status === 429) break;
    } catch {
      // Try the other public instance if this one is unavailable.
    }
  }
  if (!data) {
    const fallback = await findPhotonPharmacies(origin);
    cache.set(key, { time: Date.now(), items: fallback });
    return fallback;
  }
  if (!Array.isArray(data.elements)) throw new Error("Dữ liệu nhà thuốc chưa sẵn sàng.");
  const items = data.elements.flatMap((element) => {
    const latitude = element.lat ?? element.center?.lat;
    const longitude = element.lon ?? element.center?.lon;
    if (latitude === undefined || longitude === undefined || !Number.isFinite(latitude) || !Number.isFinite(longitude)) return [];
    const tags = element.tags ?? {};
    return [{
      id: `${element.type}-${element.id}`,
      name: tags.name || tags.operator || "Nhà thuốc",
      latitude,
      longitude,
      distanceKm: distanceKm(origin, { latitude, longitude }),
      address: addressFromTags(tags),
      phone: tags["contact:phone"] || tags.phone || null,
    }];
  }).filter((item) => item.distanceKm <= RADIUS_METERS / 1000)
    .sort((a, b) => a.distanceKm - b.distanceKm)
    .slice(0, 30);
  cache.set(key, { time: Date.now(), items });
  return items;
}

export function directionsUrl(origin: Coordinates, pharmacy: Pharmacy): string {
  const params = new URLSearchParams({
    api: "1",
    origin: `${origin.latitude},${origin.longitude}`,
    destination: `${pharmacy.latitude},${pharmacy.longitude}`,
  });
  return `https://www.google.com/maps/dir/?${params}`;
}

export function nearbySearchUrl(origin?: Coordinates): string {
  const query = origin
    ? `nhà thuốc gần ${origin.latitude},${origin.longitude}`
    : "nhà thuốc gần tôi";
  return `https://www.google.com/maps/search/?${new URLSearchParams({ api: "1", query })}`;
}

export async function findAddress(query: string): Promise<Coordinates> {
  const response = await fetch(`https://photon.komoot.io/api/?${new URLSearchParams({ q: query.trim(), limit: "1" })}`, {
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) throw new Error("Không thể tìm địa chỉ. Hãy thử tên đường hoặc khu vực khác.");
  const data = await response.json() as { features?: Array<{ geometry?: { coordinates?: number[] } }> };
  const coordinates = data.features?.[0]?.geometry?.coordinates;
  if (!coordinates || coordinates.length < 2 || !Number.isFinite(coordinates[0]) || !Number.isFinite(coordinates[1])) {
    throw new Error("Không tìm thấy địa chỉ này. Hãy nhập địa chỉ cụ thể hơn.");
  }
  return { latitude: coordinates[1], longitude: coordinates[0] };
}
