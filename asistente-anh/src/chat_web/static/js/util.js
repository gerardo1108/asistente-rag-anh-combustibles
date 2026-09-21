/**
 * `crypto.randomUUID()` solo existe en contextos seguros (HTTPS, o
 * `localhost` como excepción del navegador). Este prototipo se abre también
 * desde otros dispositivos en la LAN vía IP (HTTP plano, contexto no
 * seguro), donde esa función no existe y su llamada tira una excepción.
 * `crypto.getRandomValues()` sí funciona en cualquier contexto, así que se
 * arma el UUID v4 a mano con esa base.
 */
export function generarUUID() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0"));
  return (
    `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-` +
    `${hex.slice(6, 8).join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10, 16).join("")}`
  );
}
