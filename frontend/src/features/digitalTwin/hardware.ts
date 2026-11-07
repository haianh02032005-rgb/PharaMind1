export type PhysicalBoxState = { status: "OPEN" | "CLOSED"; led_state: "ON" | "OFF" };
export type HardwareState = {
  connected: boolean;
  boxes: Record<string, PhysicalBoxState> | null;
};
export type HardwareCommand =
  | { action: "UNLOCK_BOX"; box_id: number }
  | { action: "SET_LED"; box_id: number; state: "ON" | "OFF" };

declare global {
  interface Window {
    pharmamindHardware?: {
      getState: () => Promise<HardwareState>;
      subscribe: (callback: (state: HardwareState) => void) => () => void;
      sendCommand: (command: HardwareCommand) => Promise<{ sent: boolean }>;
    };
  }
}

export const isPiHardwareApp = () =>
  typeof window !== "undefined" && Boolean(window.pharmamindHardware);

export async function sendHardwareCommand(command: HardwareCommand): Promise<void> {
  const bridge = window.pharmamindHardware;
  if (!bridge) throw new Error("Ứng dụng Raspberry Pi không khả dụng");
  await bridge.sendCommand(command);
}
