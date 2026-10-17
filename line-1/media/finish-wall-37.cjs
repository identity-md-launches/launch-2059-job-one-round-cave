// Add only the generated basket on bare upper-left rock; protect all other pixels.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {decode, encode, thumbnail} = require('./finish-wall.cjs');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const oldBytes = fs.readFileSync('artifacts/line-1/wall-v17.png');
const old = decode(oldBytes), edit = decode(fs.readFileSync('artifacts/line-1/wall-v18.png'));
if(old.width !== edit.width || old.height !== edit.height) throw Error('size changed');
const output = {...old, pixels: Buffer.from(old.pixels)};
const clamp = v => Math.max(0, Math.min(1,v));
function mask(x,y) {
  const body = clamp((1-Math.hypot((x-201)/51,(y-258)/34))*8);
  const ring = Math.abs(Math.hypot((x-200)/31,(y-239)/38)-1);
  const handle = y <= 242 ? clamp((0.22-ring)*10) : 0;
  return Math.max(body,handle);
}
let changed=0, protectedPixels=0, outsideChanged=0;
for(let y=0;y<old.height;y++) for(let x=0;x<old.width;x++) {
  const a=mask(x,y), at=(y*old.width+x)*3;
  if(!a) protectedPixels++;
  let differs=false;
  for(let c=0;c<3;c++) {
    output.pixels[at+c]=Math.round(old.pixels[at+c]*(1-a)+edit.pixels[at+c]*a);
    differs ||= output.pixels[at+c] !== old.pixels[at+c];
  }
  if(differs) changed++;
  if(!a && differs) outsideChanged++;
}
if(outsideChanged || changed<1000) throw Error('mask failed');
const png=encode(output), jpg=thumbnail(output);
if(!decode(png).pixels.equals(output.pixels)) throw Error('PNG roundtrip failed');
if(jpg.length>100000) throw Error('JPEG too large');
fs.writeFileSync('artifacts/line-1/wall-v18.png',png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/37.jpg',jpg);
const report={previous_sha256:hash(oldBytes),sha256:hash(png),format:'PNG',width:old.width,height:old.height,
 png_bytes:png.length,preview_format:'JPEG',preview_width:512,preview_height:512,preview_bytes:jpg.length,
 changed_pixels:changed,protected_pixels:protectedPixels,outside_mask_changed_pixels:outsideChanged,
 mask:'feathered basket body ellipse and upper handle ring; bare upper-left rock only',png_roundtrip_passed:true};
fs.writeFileSync('line-1/media-check-37.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
