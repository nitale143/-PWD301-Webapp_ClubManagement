const {chromium}=require('playwright');
const assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({channel:'msedge',headless:true});
 try{
  const p=await b.newPage({viewport:{width:1440,height:950}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>sessionStorage.setItem('fia-preview-session-v1',JSON.stringify({role:'board',name:'Nguyễn Minh An',code:'DEMO-BDH'})));
  await p.goto('http://127.0.0.1:5082/#landing');
  assert.equal(await p.locator('.fia-footer-column').count(),3);
  await p.locator('.fia-footer-column a[href="#rl-activities"]').click();
  assert.equal(new URL(p.url()).hash,'#landing');
  await p.locator('.fia-footer-up').click();await p.waitForFunction(()=>scrollY<10);
  await p.locator('[data-footer-info=privacy]').click();
  assert.equal(await p.locator('#preview-dialog').getAttribute('open'),'');
  assert.match(await p.locator('#preview-dialog').innerText(),/không gọi API AI/);
  await p.keyboard.press('Escape');
  await p.locator('.fia-footer-column a[href="#ai"]').click();assert.equal(new URL(p.url()).hash,'#ai');
  await p.evaluate(()=>location.hash='landing');await p.waitForSelector('.fia-footer');
  await p.setViewportSize({width:390,height:844});
  await p.locator('.fia-footer-socials button').first().click();assert.match(await p.locator('#preview-dialog').innerText(),/chưa được cung cấp/);await p.keyboard.press('Escape');
  assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  await p.locator('.fia-footer').screenshot({path:__dirname+'/screenshots/footer-fia-mobile.png'});
  await p.setViewportSize({width:1440,height:950});await p.locator('.fia-footer').screenshot({path:__dirname+'/screenshots/footer-fia.png'});
  assert.deepEqual(errors,[]);console.log(JSON.stringify({footer:'passed',links:'passed',backToTop:'passed',dialogs:'passed',mobile:'passed',errors}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
