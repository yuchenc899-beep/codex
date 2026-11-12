import http from "node:http";
import { handleRequest } from "./gateway.mjs";
const server = http.createServer(async (req, res) => {
  try {
    if (req.headers.host !== "127.0.0.1:8787") {
      res.writeHead(403);
      return res.end();
    }
    const chunks = [];
    let size = 0;
    for await (const part of req) {
      size += part.length;
      if (size > 32768) {
        res.writeHead(413);
        return res.end();
      }
      chunks.push(part);
    }
    const response = await handleRequest(
      new Request("http://127.0.0.1:8787" + req.url, {
        method: req.method,
        body: ["GET", "HEAD"].includes(req.method)
          ? undefined
          : Buffer.concat(chunks),
        headers: { "Content-Type": "application/json" },
      }),
    );
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch {
    res.writeHead(500);
    res.end("gateway error");
  }
});
server.listen(8787, "127.0.0.1", () =>
  console.log("Yuchen local gateway http://127.0.0.1:8787"),
);
