import { DurableObject } from "cloudflare:workers";

interface Env {
  PHARMAMIND_CONTAINER: DurableObjectNamespace<PharmaMindContainer>;
  DATABASE_URL: string;
  JWT_SECRET: string;
}

const PORT = 8000;
const STARTUP_TIMEOUT_MS = 30_000;

export class PharmaMindContainer extends DurableObject<Env> {
  private starting: Promise<void> | undefined;

  async fetch(request: Request): Promise<Response> {
    this.starting ??= this.startContainer().finally(() => {
      this.starting = undefined;
    });
    await this.starting;

    const url = new URL(request.url);
    url.protocol = "http:";
    url.host = "container";
    const forwarded = new Request(url, request);
    forwarded.headers.delete("host");
    return this.ctx.container!.getTcpPort(PORT).fetch(forwarded);
  }

  private async startContainer(): Promise<void> {
    const container = this.ctx.container!;
    if (!container.running) {
      if (!this.env.DATABASE_URL || !this.env.JWT_SECRET) {
        throw new Error("Set the DATABASE_URL and JWT_SECRET Worker secrets before deployment.");
      }
      container.start({
        image: container.images.base,
        env: {
          DATABASE_URL: this.env.DATABASE_URL,
          JWT_SECRET: this.env.JWT_SECRET,
          DEBUG: "false",
          CORS_ORIGINS: "[]",
          DEFAULT_TIMEZONE: "Asia/Ho_Chi_Minh",
          PORT: String(PORT),
        },
      });
    }

    const deadline = Date.now() + STARTUP_TIMEOUT_MS;
    let lastError: unknown;
    while (Date.now() < deadline) {
      try {
        const response = await container.getTcpPort(PORT).fetch("http://container/health", {
          signal: AbortSignal.timeout(1_000),
        });
        await response.body?.cancel();
        if (response.ok) return;
        lastError = new Error(`Container health check returned ${response.status}`);
      } catch (error) {
        lastError = error;
      }
      await scheduler.wait(500);
    }

    throw new Error("PharmaMind container did not become healthy within 30 seconds.", {
      cause: lastError,
    });
  }
}

export default {
  fetch(request: Request, env: Env): Promise<Response> {
    return env.PHARMAMIND_CONTAINER.getByName("pharmamind-production").fetch(request);
  },
} satisfies ExportedHandler<Env>;
