import {
  CabinetRealtimeMessage,
  CabinetWebSocketClient,
} from "../../services/websocketClient";
import { useDigitalTwinStore } from "./store";

export function createDigitalTwinWebSocket(
  familyId: number,
  cabinetId: number
): CabinetWebSocketClient {
  return new CabinetWebSocketClient(
    familyId,
    cabinetId,
    (msg: CabinetRealtimeMessage) => {
      useDigitalTwinStore.getState().applyRealtimeEvent(msg);
    },
    (connected: boolean) => {
      useDigitalTwinStore.getState().setWsConnected(connected);
    }
  );
}

