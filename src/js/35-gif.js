/*
  decodeGif(bytes): reads a GIF (87a or 89a) into fully composited RGBA frames.
  Handles global and local color tables, transparency, interlacing, and the
  disposal methods that animation tools use. Pure function: no DOM needed.
  Returns { width, height, frames: [{ rgba: Uint8ClampedArray, delay: ms }] }.
*/
function decodeGif(bytes) {
  let pos = 0;
  const u8 = () => bytes[pos++];
  const u16 = () => { const v = bytes[pos] | (bytes[pos + 1] << 8); pos += 2; return v; };
  const sig = String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5]);
  if (sig !== 'GIF87a' && sig !== 'GIF89a') throw new Error('Not a GIF file');
  pos = 6;
  const W = u16(), H = u16();
  const packed = u8(); u8(); u8();                 // background index and aspect ratio are not needed
  let gct = null;
  if (packed & 0x80) { const n = 2 << (packed & 7); gct = bytes.subarray(pos, pos + n * 3); pos += n * 3; }

  const frames = [];
  let canvas = new Uint8ClampedArray(W * H * 4); // starts fully transparent
  let gce = { delay: 0, trans: -1, disposal: 0 };

  while (pos < bytes.length) {
    const block = u8();
    if (block === 0x3B) break;                     // trailer
    if (block === 0x21) {                          // extension
      const label = u8();
      if (label === 0xF9) {                        // graphic control extension
        const size = u8(), start = pos;
        const p = u8(), delay = u16(), ti = u8();
        pos = start + size;
        gce = { disposal: (p >> 2) & 7, trans: (p & 1) ? ti : -1, delay: delay * 10 };
        while (pos < bytes.length) { const n = u8(); if (!n) break; pos += n; }
      } else {
        while (pos < bytes.length) { const n = u8(); if (!n) break; pos += n; }
      }
      continue;
    }
    if (block !== 0x2C) break;                     // anything else: stop reading

    const fx = u16(), fy = u16(), fw = u16(), fh = u16(), ip = u8();
    let ct = gct;
    if (ip & 0x80) { const n = 2 << (ip & 7); ct = bytes.subarray(pos, pos + n * 3); pos += n * 3; }
    const interlaced = !!(ip & 0x40);
    const minCode = u8();
    const parts = []; let total = 0;
    while (pos < bytes.length) { const n = u8(); if (!n) break; parts.push(bytes.subarray(pos, pos + n)); total += n; pos += n; }
    const data = new Uint8Array(total);
    for (let i = 0, o = 0; i < parts.length; o += parts[i].length, i++) data.set(parts[i], o);
    const idx = lzwDecode(minCode, data, fw * fh);

    const before = gce.disposal === 3 ? canvas.slice() : null;
    const rows = interlaced ? interlaceOrder(fh) : null;
    if (ct) {
      for (let r = 0; r < fh; r++) {
        const y = fy + (rows ? rows[r] : r);
        if (y >= H) continue;
        for (let x = 0; x < fw; x++) {
          const X = fx + x;
          if (X >= W) continue;
          const c = idx[r * fw + x];
          if (c === gce.trans || c * 3 + 2 >= ct.length) continue;
          const d = (y * W + X) * 4;
          canvas[d] = ct[c * 3]; canvas[d + 1] = ct[c * 3 + 1]; canvas[d + 2] = ct[c * 3 + 2]; canvas[d + 3] = 255;
        }
      }
    }
    frames.push({ rgba: canvas.slice(), delay: gce.delay });

    if (gce.disposal === 2) {                      // restore the frame's area to transparent
      for (let y = fy; y < Math.min(H, fy + fh); y++) canvas.fill(0, (y * W + fx) * 4, (y * W + Math.min(W, fx + fw)) * 4);
    } else if (gce.disposal === 3 && before) {     // restore to how it was before this frame
      canvas = before;
    }
    gce = { delay: 0, trans: -1, disposal: 0 };
  }
  return { width: W, height: H, frames };
}

function interlaceOrder(h) {
  const order = [];
  for (const [start, step] of [[0, 8], [4, 8], [2, 4], [1, 2]]) for (let r = start; r < h; r += step) order.push(r);
  return order;
}

/* Variable-width LZW, as GIF uses it. Returns color indices for one frame. */
function lzwDecode(minCode, data, count) {
  const out = new Uint8Array(count);
  const clear = 1 << minCode, eoi = clear + 1;
  const prefix = new Int32Array(4096), suffix = new Uint8Array(4096), stack = new Uint8Array(4097);
  for (let i = 0; i < clear; i++) { prefix[i] = -1; suffix[i] = i; }
  let size = minCode + 1, mask = (1 << size) - 1, next = eoi + 1, old = -1, first = 0;
  let bits = 0, datum = 0, di = 0, op = 0;
  while (op < count) {
    while (bits < size) {
      if (di >= data.length) return out;
      datum |= data[di++] << bits; bits += 8;
    }
    let code = datum & mask;
    datum >>>= size; bits -= size;
    if (code === clear) { size = minCode + 1; mask = (1 << size) - 1; next = eoi + 1; old = -1; continue; }
    if (code === eoi) break;
    if (old === -1) {
      if (code >= clear) return out;               // corrupt stream
      out[op++] = suffix[code]; old = code; first = code;
      continue;
    }
    const incoming = code;
    let sp = 0;
    if (code >= next) { stack[sp++] = first; code = old; }
    while (code > eoi) { stack[sp++] = suffix[code]; code = prefix[code]; if (sp >= 4096) return out; }
    first = suffix[code];
    stack[sp++] = first;
    while (sp > 0 && op < count) out[op++] = stack[--sp];
    if (next < 4096) {
      prefix[next] = old; suffix[next] = first; next++;
      if (next > mask && size < 12) { size++; mask = (1 << size) - 1; }
    }
    old = incoming;
  }
  return out;
}

if (typeof module !== 'undefined') module.exports = { decodeGif };
