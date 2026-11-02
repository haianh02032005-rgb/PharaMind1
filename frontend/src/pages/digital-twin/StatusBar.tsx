import React from "react";
import { Wifi, WifiOff, RefreshCw, Cpu, Clock } from "lucide-react";
import { DigitalTwinCabinetHeader } from "../../features/digitalTwin/types";

interface StatusBarProps {
  cabinet: DigitalTwinCabinetHeader | null;
  wsConnected: boolean;
  onToggleOnline: () => void;
  onSyncState: () => void;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  cabinet,
  wsConnected,
  onToggleOnline,
  onSyncState,
}) => {
  if (!cabinet) return null;

  const isOnline = cabinet.status === "ONLINE";
  const formattedLastSeen = cabinet.last_seen_at
    ? new Date(cabinet.last_seen_at).toLocaleTimeString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "Chưa ghi nhận";

  return (
    <div
      className="card"
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 14,
        padding: "14px 20px",
        marginBottom: 18,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <span
          className={`badge ${isOnline ? "badge-success" : "badge-neutral"}`}
          style={{ fontSize: "0.85rem", padding: "6px 12px" }}
        >
          {isOnline ? <Wifi size={15} /> : <WifiOff size={15} />}
          {isOnline ? "Tủ đang ONLINE" : "Tủ đang OFFLINE"}
        </span>

        <span className="badge badge-primary">
          <Cpu size={14} />
          Chế độ: {cabinet.hardware_mode}
        </span>

        <span
          className={`badge ${wsConnected ? "badge-success" : "badge-warning"}`}
        >
          ● Realtime WS: {wsConnected ? "Đã kết nối" : "Polling dự phòng"}
        </span>

        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: "0.85rem",
            color: "var(--pm-text-secondary)",
          }}
        >
          <Clock size={14} />
          Cập nhật: {formattedLastSeen}
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <button
          type="button"
          className={`btn btn-sm ${isOnline ? "btn-outline" : "btn-primary"}`}
          onClick={onToggleOnline}
        >
          {isOnline ? "Giả lập Mất kết nối (Offline)" : "Bật kết nối Tủ (Online)"}
        </button>

        <button
          type="button"
          className="btn btn-sm btn-secondary"
          onClick={onSyncState}
        >
          <RefreshCw size={14} />
          Đồng bộ trạng thái
        </button>
      </div>
    </div>
  );
};

