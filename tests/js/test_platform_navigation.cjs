const test=require('node:test'),assert=require('node:assert/strict');
const {pilot}=require('./tme-dom.cjs');
const {flush}=require('./ui-dom.cjs');
for(const [index,mode] of [[1,'specialized'],[2,'dynamic']])test(`teacher navigation opens ${mode} in the existing router`,async()=>{
 const ui=await pilot({startHome:true});
 let prevented=false;await ui.platformLinks[index].handlers.click({button:0,preventDefault(){prevented=true;}});await flush();
 assert(prevented);assert.equal(ui.window.history.url,`/tme?view=new&mode=${mode}`);
 assert(!ui.calls.some(c=>c.options?.method==='POST'));
});
for(const [status,message] of [[404,/Demonstração local/],[401,/Sessão ausente ou expirada/],[403,/perfil não tem acesso/],[500,/Não foi possível consultar a sessão/]])test(`session HTTP ${status} is explicit and does not imply authenticated access`,async()=>{
 const ui=await pilot({startHome:true,mockFetch:async url=>url==='/auth/me'?{ok:false,status,json:async()=>({})}:undefined});
 assert.match(ui.shell['platform-session-status'].textContent,message);
 assert.equal(ui.shell['platform-session-status'].hidden,status===404);
 assert.match(ui.shell['home-session'].textContent,message);
 assert(!ui.calls.some(c=>c.options?.method==='POST'));
});

test('platform brand is static while the three modules retain the menu home link',()=>{
 const fs=require('node:fs'),path=require('node:path');
 const root=path.resolve(__dirname,'../../app/confia_lean_auditor/static');
 const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
 const platform=html.match(/<header\b[^>]*id="platform-header"[\s\S]*?<\/header>/)[0];
 const brand=platform.match(/<div\b[^>]*class="home-brand"[^>]*>/);
 assert(brand,'The approved brand is a non-interactive div');
 assert.doesNotMatch(brand[0],/\b(?:href|tabindex|role|onclick)\s*=/);
 assert.doesNotMatch(platform,/<a\b[^>]*class="home-brand"/);
 const shell=fs.readFileSync(path.join(root,'shell.js'),'utf8');
 for(const role of ['student','teacher','management'])assert(shell.includes(role));
 assert.match(html,/Início da plataforma/);
});
