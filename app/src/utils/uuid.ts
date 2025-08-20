// Simple RFC4122 v4 UUID generator using Crypto API
export function uuidv4(): string {
  const rnds = new Uint8Array(16);
  if (typeof globalThis.crypto?.getRandomValues === 'function') {
    globalThis.crypto.getRandomValues(rnds);
  } else {
    for (let i = 0; i < 16; i += 1) rnds[i] = Math.floor(Math.random() * 256);
  }
  // Per RFC4122 v4
  rnds[6] = (rnds[6] & 0x0f) | 0x40;
  rnds[8] = (rnds[8] & 0x3f) | 0x80;
  const hex: string[] = [];
  for (let i = 0; i < 256; i++) hex.push((i + 0x100).toString(16).substring(1));
  return (
    hex[rnds[0]] +
    hex[rnds[1]] +
    hex[rnds[2]] +
    hex[rnds[3]] +
    '-' +
    hex[rnds[4]] +
    hex[rnds[5]] +
    '-' +
    hex[rnds[6]] +
    hex[rnds[7]] +
    '-' +
    hex[rnds[8]] +
    hex[rnds[9]] +
    '-' +
    hex[rnds[10]] +
    hex[rnds[11]] +
    hex[rnds[12]] +
    hex[rnds[13]] +
    hex[rnds[14]] +
    hex[rnds[15]]
  );
}


