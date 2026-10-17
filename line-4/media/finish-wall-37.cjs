// Assemble a small generated pigment mark on untouched inherited rock.
const fs=require('node:fs'),zlib=require('node:zlib'),crypto=require('node:crypto');
const {decode,encode,thumbnail}=require('../../line-1/media/finish-wall.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const sig=Buffer.from('89504e470d0a1a0a','hex');

function rgba(bytes){
  if(!bytes.subarray(0,8).equals(sig))throw Error('PNG required');
  let w,h,parts=[];
  for(let p=8;p<bytes.length;){
    const n=bytes.readUInt32BE(p),t=bytes.toString('ascii',p+4,p+8),v=bytes.subarray(p+8,p+8+n);
    if(t==='IHDR'){
      w=v.readUInt32BE(0);h=v.readUInt32BE(4);
      if(w>2048||h>2048||w<1||h<1||v[8]!==8||v[9]!==6||v[12]!==0)throw Error('8-bit RGBA noninterlaced PNG required');
    }
    if(t==='IDAT')parts.push(v);
    p+=n+12;if(t==='IEND')break;
  }
  const stride=w*4,raw=zlib.inflateSync(Buffer.concat(parts),{maxOutputLength:(stride+1)*h});
  if(raw.length!==(stride+1)*h)throw Error('bad PNG raster');
  const pixels=Buffer.alloc(stride*h);
  for(let y=0;y<h;y++){
    const filter=raw[y*(stride+1)];if(filter>4)throw Error('bad PNG filter');
    for(let x=0;x<stride;x++){
      const i=y*stride+x,a=x>=4?pixels[i-4]:0,b=y?pixels[i-stride]:0,c=y&&x>=4?pixels[i-stride-4]:0;
      const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);
      const pred=[0,a,b,Math.floor((a+b)/2),pa<=pb&&pa<=pc?a:pb<=pc?b:c][filter];
      pixels[i]=(raw[y*(stride+1)+x+1]+pred)&255;
    }
  }
  return {width:w,height:h,pixels};
}

const oldBytes=fs.readFileSync('artifacts/line-4/wall-v17.png');
const record36=JSON.parse(fs.readFileSync('dist/line-4/36.json'));
if(record36.image!=='https://api.imd.fun/artifacts/'+sha(oldBytes))throw Error('ancestor hash mismatch');
const old=decode(oldBytes),glyph=rgba(fs.readFileSync('artifacts/line-4/wall-v18.png'));
const out={...old,pixels:Buffer.from(old.pixels)};
const box=[170,925,250,160];let changed=0;
for(let y=0;y<box[3];y++)for(let x=0;x<box[2];x++){
  let alpha=0,r=0,g=0,b=0;
  for(let sy=0;sy<4;sy++)for(let sx=0;sx<4;sx++){
    const gx=Math.min(glyph.width-1,Math.floor((x+(sx+.5)/4)*glyph.width/box[2]));
    const gy=Math.min(glyph.height-1,Math.floor((y+(sy+.5)/4)*glyph.height/box[3]));
    const i=(gy*glyph.width+gx)*4,a=glyph.pixels[i+3]/255;
    const rr=glyph.pixels[i],gg=glyph.pixels[i+1],bb=glyph.pixels[i+2];
    // Remove the generator's translucent glow; transfer opaque pigment only.
    if(a<.93)continue;
    const red=rr>75&&rr>gg*1.35&&gg>bb*1.12;
    const ochre=rr>140&&rr>gg*1.10&&gg>bb*1.45;
    const charcoal=rr<100&&gg<95&&bb<90;
    if(!(red||ochre||charcoal))continue;
    const color=ochre?[185,127,43]:red?[150,62,31]:[46,36,26];
    alpha+=a;r+=a*color[0];g+=a*color[1];b+=a*color[2];
  }
  alpha/=16;if(alpha<.06)continue;
  const j=((box[1]+y)*old.width+box[0]+x)*3,src=[r/(alpha*16),g/(alpha*16),b/(alpha*16)];
  const stone=(old.pixels[j]+old.pixels[j+1]+old.pixels[j+2])/765;
  const opacity=alpha*(.68+.20*stone);
  for(let k=0;k<3;k++)out.pixels[j+k]=Math.round(old.pixels[j+k]*(1-opacity)+src[k]*opacity);
  if(!out.pixels.subarray(j,j+3).equals(old.pixels.subarray(j,j+3)))changed++;
}
let outside=0;
for(let y=0;y<old.height;y++)for(let x=0;x<old.width;x++){
 if(x>=box[0]&&x<box[0]+box[2]&&y>=box[1]&&y<box[1]+box[3])continue;
 const j=(y*old.width+x)*3;
 if(!old.pixels.subarray(j,j+3).equals(out.pixels.subarray(j,j+3)))outside++;
}
if(outside||changed<200||changed>box[2]*box[3])throw Error('unexpected pigment area or changed ancestor');
const png=encode(out),jpg=thumbnail(out);
if(!decode(png).pixels.equals(out.pixels)||jpg.length>100000)throw Error('output codec check failed');
fs.writeFileSync('artifacts/line-4/wall-v18.png',png);
fs.unlinkSync('artifacts/line-4/wall.png');
fs.linkSync('artifacts/line-4/wall-v18.png','artifacts/line-4/wall.png');
fs.writeFileSync('artifacts/line-4/37.jpg',jpg);
fs.linkSync('artifacts/line-4/37.jpg','dist/line-4/37.jpg');
const record={name:'The Values in the Basket',image:'https://api.imd.fun/artifacts/'+sha(png),attributes:[
  {trait_type:'Cave',value:'Lava'},
  {trait_type:'Wall',value:'Line 4'},
  {trait_type:'Number',value:37},
  {trait_type:'Left behind',value:'MapCheck'},
  {trait_type:'Meaning',value:'Three different stones sit in an ochre basket, each value checked within its container.'},
  {trait_type:'One thing',value:'Detect breaking OpenAPI changes'}]};
fs.writeFileSync('dist/line-4/37.json',JSON.stringify(record,null,2)+'\n');
const review={ancestor_sha256:sha(oldBytes),sha256:sha(png),dimensions:[old.width,old.height],
  format:'RGB PNG',wall:'artifacts/line-4/wall-v18.png',canonical_wall:'artifacts/line-4/wall.png',
  preview:'dist/line-4/37.jpg',preview_format:'JPEG',preview_dimensions:[512,512],
  preview_bytes:jpg.length,addition_bounds:[...box],changed_pixels:changed,
  pixels_changed_outside_addition:outside,png_roundtrip_passed:true,
  method:'Built-in image generation of pigment; opaque motif recolored to earth pigments and blended onto exact prior wall. Generated glow discarded.',
  visual_review:'Pending visual inspection.',unmet_visual_requirements:[]};
fs.writeFileSync('line-4/review-37.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify({sha256:sha(png),png_bytes:png.length,jpeg_bytes:jpg.length,
  dimensions:review.dimensions,changed_pixels:changed,outside_pixels_changed:outside},null,2));
