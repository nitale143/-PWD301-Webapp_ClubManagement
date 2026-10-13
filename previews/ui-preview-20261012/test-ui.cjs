const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const output=path.join(__dirname,'screenshots');fs.mkdirSync(output,{recursive:true});
  const keys=['dashboard','members','events','event-detail','tasks','funds','ai','approvals','roles','profile','login','register','pending','checkin'];
  await page.goto('http://127.0.0.1:5080/#dashboard');
  for(const key of keys){
   await page.evaluate(key=>location.hash=key,key);
   await page.waitForFunction(key=>document.title.endsWith('· FIA UI Preview')&&window.location.hash==='#'+key&&document.getElementById('view').textContent.trim().length>30,key);
   await page.waitForTimeout(80);
   assert.equal(page.url().split('#')[1],key,'missing screen '+key);
   await page.screenshot({path:path.join(output,key+'.png'),fullPage:true});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'desktop overflow '+key);
  }
  await page.setViewportSize({width:390,height:844});
  for(const key of keys){
   await page.evaluate(key=>location.hash=key,key);await page.waitForTimeout(80);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'mobile overflow '+key);
   if(['dashboard','ai','login','members'].includes(key))await page.screenshot({path:path.join(output,key+'-mobile.png'),fullPage:true});
  }
  await page.evaluate(()=>location.hash='dashboard');await page.waitForTimeout(80);
  await page.locator('#menu-toggle').click();assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'true');
  await page.locator('#primary-navigation a[data-nav=members]').click();assert.equal(await page.locator('#menu-toggle').getAttribute('aria-expanded'),'false');
  await page.setViewportSize({width:1440,height:1050});
  await page.locator('#preview-options').click();assert.equal(await page.locator('#preview-dialog').getAttribute('open'),'');
  await page.locator('#screen-search').fill('đăng ký');
  assert.equal(await page.locator('#screen-results button').count(),1);
  await page.locator('#screen-results button').click();assert.equal(page.url().split('#')[1],'register');
  await page.waitForTimeout(80);
  assert.deepEqual(errors,[],'browser errors');
  console.log(JSON.stringify({screens:keys.length,desktop:'passed',mobileOverflow:'passed',menu:'passed',search:'passed',errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
