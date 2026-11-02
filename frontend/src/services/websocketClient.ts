import { getAccessToken, WS_BASE_URL } from "./apiClient";

export interface CabinetRealtimeMessage {
  event_type:
    | "CABINET_ONLINE"
    | "CABINET_OFFLINE"
    | "COMPARTMENT_OPEN"
    | "COMPARTMENT_CLOSE"
    | "CABINET_STATE_SYNC"
    | string;
  family_id: number;
  cabinet_id: number;
  occurred_at: string;
  payload: {
    position?: number;
    object_id?: string;
    is_open?: boolean;
    status?: string;
    compartments?: Record<string, boolean>;
    [key: string]: unknown;
  };
}

export class CabinetWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyClosed = false;

  constructor(
    private readonly familyId: number,
    private readonly cabinetId: number,
    private readonly onEvent: (msg: CabinetRealtimeMessage) => void,
    private readonly onConnectionChange?: (connected: boolean) => void
  ) {}

  connect(): void {
    this.manuallyClosed = false;
    const token = getAccessToken();
    if (!token || typeof WebSocket === "undefined") {
      this.onConnectionChange?.(false);
      return;
    }

    const url = `${WS_BASE_URL}/ws/families/${this.familyId}/cabinets/${this.cabinetId}?token=${encodeURIComponent(
      token
    )}`;

    try {
      this.ws = new WebSocket(url);
      this.ws.onopen = () => {
        this.onConnectionChange?.(true);
      };
      this.ws.onmessage = (evt) => {
        try {
          const parsed = JSON.parse(evt.data) as CabinetRealtimeMessage;
          if (parsed && parsed.event_type) {
            this.onEvent(parsed);
          }
        } catch {
          // ignore invalid json
        }
      };
      this.ws.onclose = () => {
        this.onConnectionChange?.(false);
        if (!this.manuallyClosed) {
          this.reconnectTimer = setTimeout(() => this.connect(), 3500);
        }
      };
      this.ws.onerror = () => {
        this.onConnectionChange?.(false);
      };
    } catch {
      this.onConnectionChange?.(false);
    }
  }

  disconnect(): void {
    this.manuallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        // ignore
      }
      this.ws = null;
    }
  }
}

