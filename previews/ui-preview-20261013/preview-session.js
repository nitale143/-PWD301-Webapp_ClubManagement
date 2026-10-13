/* UI-only demo session. NOT real authentication or a security boundary. */
(() => {
  const key = 'fia-preview-session-v1';
  const destinations = new Set(['dashboard','members','events','event-detail','tasks','funds','ai','approvals','roles','profile','checkin']);
  let session = null;
  let next = null;
  try {
    const value = JSON.parse(sessionStorage.getItem(key) || 'null');
    if (value && ['member','board'].includes(value.role) && typeof value.code === 'string') {
      session = {role:value.role,code:value.code.slice(0,30),name:String(value.name || 'Thành viên FIA').slice(0,100)};
    }
  } catch (_) { /* Browsers may disable session storage; use memory instead. */ }
  window.PreviewSession = {
    current: () => session ? {...session} : null,
    signIn: ({role='member',code='DEMO',name='Thành viên FIA'} = {}) => {
      session = {role:role === 'board' ? 'board' : 'member',code:String(code).trim().slice(0,30),name:String(name).trim().slice(0,100) || 'Thành viên FIA'};
      try {sessionStorage.setItem(key,JSON.stringify(session));} catch (_) {}
      return {...session};
    },
    signOut: () => {session=null;next=null;try {sessionStorage.removeItem(key);} catch (_) {}},
    request: destination => {next=destinations.has(destination)?destination:'dashboard';},
    takeNext: () => {const destination=next || 'dashboard';next=null;return destination;},
    canVisit: destination => session && (session.role === 'board' || !['members','approvals','roles'].includes(destination)),
  };
})();
