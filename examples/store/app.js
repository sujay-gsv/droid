const products = [
  {id:1,name:'Studio Wireless Headphones',category:'Tech',price:2499,icon:'🎧',color:'#e7e7df',badge:'BESTSELLER'},
  {id:2,name:'The Everyday Tote',category:'Outdoor',price:699,icon:'👜',color:'#e6ddcb',badge:'STAFF PICK'},
  {id:3,name:'Slow Morning Coffee Set',category:'Home',price:899,icon:'☕',color:'#ece1d3',badge:'NEW ARRIVAL'},
  {id:4,name:'Pocket Bluetooth Speaker',category:'Tech',price:1299,icon:'📻',color:'#dce5df',badge:'GREAT FIND'},
  {id:5,name:'Trail Ready Sneakers',category:'Outdoor',price:1999,icon:'👟',color:'#e4e4d9',badge:'EVERYDAY FAVOURITE'},
  {id:6,name:'Little Desk Companion',category:'Home',price:399,icon:'🪴',color:'#e0e8d9',badge:'A LITTLE JOY'},
  {id:7,name:'Weekend Adventure Pack',category:'Outdoor',price:1499,icon:'🎒',color:'#e9dfd5',badge:'READY TO GO'},
  {id:8,name:'Focus Mechanical Keyboard',category:'Tech',price:3299,icon:'⌨️',color:'#dce1e8',badge:'WORK BETTER'}
];
let category='All', query='', cart={};
try { const saved=JSON.parse(localStorage.getItem('driod-demo-cart')||'{}'); for(const p of products){ const q=Number(saved[p.id]); if(Number.isInteger(q)&&q>0&&q<1000) cart[p.id]=q; } } catch (_) {}
const money=n=>'₹'+n.toLocaleString('en-IN');
function renderProducts(){
  const selected=products.filter(p=>(category==='All'||p.category===category)&&p.name.toLowerCase().includes(query.toLowerCase()));
  document.querySelector('#product-grid').innerHTML=selected.map(p=>`<article class="product"><div class="product-art" style="--color:${p.color}"><span class="badge">${p.badge}</span><span role="img" aria-label="${p.name}">${p.icon}</span></div><div class="product-info"><span class="category">${p.category}</span><h3>${p.name}</h3><span class="rating" aria-label="Demo rating: 4.8 out of 5">★★★★★ · 4.8</span><div class="price-row"><b>${money(p.price)}</b><button data-add="${p.id}" aria-label="Add ${p.name} to bag">Add to bag +</button></div></div></article>`).join('');
  document.querySelector('#result-count').textContent=selected.length+' finds';
  document.querySelector('#empty').hidden=selected.length>0;
}
function renderCart(){
  let total=0,count=0;
  const items=products.filter(p=>cart[p.id]);
  document.querySelector('#cart-items').innerHTML=items.length?items.map(p=>{total+=p.price*cart[p.id];count+=cart[p.id];return `<div class="cart-row"><span>${p.icon} ${p.name}<br><b>${money(p.price)} × ${cart[p.id]}</b></span><button data-remove="${p.id}" aria-label="Remove one ${p.name}">−</button><button data-add="${p.id}" aria-label="Add one ${p.name}">+</button></div>`}).join(''):'<p>Your bag is empty. Time to find a favourite.</p>';
  document.querySelector('#cart-count').textContent=count;
  document.querySelector('#cart-total').textContent=money(total);
  try {localStorage.setItem('driod-demo-cart',JSON.stringify(cart));}catch(_){}
}
let toastTimer;
document.addEventListener('click',e=>{
  const add=e.target.closest('[data-add]'),remove=e.target.closest('[data-remove]');
  if(add){const id=add.dataset.add;cart[id]=(cart[id]||0)+1;renderCart();const t=document.querySelector('#toast');t.textContent='Added to your bag';t.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('visible'),1700);}
  if(remove){const id=remove.dataset.remove;if(--cart[id]<=0)delete cart[id];renderCart();}
});
document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=button.dataset.category;document.querySelectorAll('[data-category]').forEach(b=>b.classList.toggle('active',b===button));renderProducts();}));
document.querySelector('#search-form').addEventListener('submit',e=>{e.preventDefault();query=document.querySelector('#search').value.trim();renderProducts();});
document.querySelector('#search').addEventListener('input',e=>{query=e.target.value.trim();renderProducts();});
const dialog=document.querySelector('#cart');
document.querySelector('#cart-open').addEventListener('click',()=>{renderCart();dialog.showModal();});
document.querySelector('#cart-close').addEventListener('click',()=>dialog.close());
document.querySelector('#checkout').addEventListener('click',()=>{document.querySelector('#checkout-note').textContent=Object.keys(cart).length?'Demo only — no order was placed and no payment was collected.':'Add a product to your bag first.';});
renderProducts();renderCart();
