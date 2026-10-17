// Transfer generated pigment only, preserving all ancestor pixels outside the mark.
const fs=require('node:fs'), crypto=require('node:crypto');
const media=require('./png_codec.cjs');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const source='artifacts/line-3/wall-v17.png', target='artifacts/line-3/wall-v18.png';
const oldBytes=fs.readFileSync(source), proposal=fs.readFileSync(target);
if(hash(oldBytes)!=='8ad259fb983e2b84eb9982af01c82dc15aa6b544d02e5d933055118e8d057062') throw Error('Wrong ancestor');
const old=media.decode(oldBytes), paint=media.decode(proposal);
const out={...old,pixels:Buffer.from(old.pixels)};
const box=[174,937,148,62], crop=[30,395,1190,500];
let changed=0;
for(let dy=0;dy<box[3];dy++) for(let dx=0;dx<box[2];dx++) {
  // Average source pigment coverage; white backdrop contributes no paint.
  let alpha=0, sums=[0,0,0], count=0;
  const x0=Math.floor(crop[0]+dx*crop[2]/box[2]), x1=Math.floor(crop[0]+(dx+1)*crop[2]/box[2]);
  const y0=Math.floor(crop[1]+dy*crop[3]/box[3]), y1=Math.floor(crop[1]+(dy+1)*crop[3]/box[3]);
  for(let y=y0;y<y1;y++) for(let x=x0;x<x1;x++) {
    const i=(y*paint.width+x)*3, [r,g,b]=paint.pixels.subarray(i,i+3);
    count++;
    if(r>225&&g>225&&b>225) continue;
    const coverage=Math.max(0,Math.min(1,(240-Math.min(r,g,b))/210));
    const color=r<115&&g<105?[38,28,20]:r>g*1.4?[154,58,27]:[181,124,35];
    alpha+=coverage;
    for(let c=0;c<3;c++) sums[c]+=color[c]*coverage;
  }
  if(alpha===0) continue;
  const a=.78*alpha/count, i=((box[1]+dy)*old.width+box[0]+dx)*3;
  for(let c=0;c<3;c++) out.pixels[i+c]=Math.round(old.pixels[i+c]*(1-a)+sums[c]/alpha*a);
  if(!out.pixels.subarray(i,i+3).equals(old.pixels.subarray(i,i+3))) changed++;
}
let outside=0;
for(let y=0;y<old.height;y++) for(let x=0;x<old.width;x++) {
  if(x>=box[0]&&x<box[0]+box[2]&&y>=box[1]&&y<box[1]+box[3]) continue;
  const i=(y*old.width+x)*3;
  if(!old.pixels.subarray(i,i+3).equals(out.pixels.subarray(i,i+3))) outside++;
}
if(outside||changed<500||changed>7000) throw Error('preservation failure');
const png=media.encode(out), jpg=media.thumbnail(out);
if(jpg.length>100000||!media.decode(png).pixels.equals(out.pixels)) throw Error('format/size failure');
fs.writeFileSync(target,png);
// Remove the inherited alias before writing, so the ancestor cannot be overwritten.
fs.rmSync('artifacts/line-3/wall.png',{force:true});
fs.symlinkSync('wall-v18.png','artifacts/line-3/wall.png');
fs.writeFileSync('dist/line-3/35.jpg',jpg,{flag:'wx'});
const result={source,source_sha256:hash(oldBytes),generated_sha256:hash(proposal),output:target,
  output_sha256:hash(png),patch_xywh:box,changed_pixels:changed,changed_pixels_outside_patch:outside,
  png_dimensions:[old.width,old.height],png_format:'RGB PNG',png_bytes:png.length,
  jpeg_dimensions:[512,512],jpeg_format:'JPEG',jpeg_bytes:jpg.length,
  method:'White backdrop removed; generated pigment area-averaged onto original rock in bare lower-left patch.'};
fs.writeFileSync('line-3/asset-build/preservation-35.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(result,null,2));
