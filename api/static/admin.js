async function post(url, data){
  const token = localStorage.getItem('admin_token') || '';
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type':'application/json', 'X-Admin-Token': token },
    body: data ? JSON.stringify(data) : null
  });
  if(!res.ok){ alert('Request failed: ' + res.status); return null; }
  return await res.json();
}
async function handle(el){
  const url = el.getAttribute("data-url");
  const json = await post(url);
  if(json){ location.reload(); }
}
