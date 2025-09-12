const products = [
	{ id: 1, name: "Modern Jeans", price: 100, img: "img1.jpg" },
	{ id: 2, name: "Steel Bottle", price: 200, img: "img2.jpg" },
	{ id: 3, name: "Trendy Sneakers", price: 300, img: "img3.jpg" }
];
const productList = document.getElementById("product-list");
const cartModal = document.getElementById("cartModal");
const cartItems = document.getElementById("cartItems");
const cartCount = document.getElementById("cart-count");
const cartTotal = document.getElementById("cartTotal");
const checkoutForm = document.getElementById("checkoutForm");
const successMessage = document.getElementById("successMessage");


let cart = {};


function renderProducts() {
products.forEach(p => {
const el = document.createElement("div");
el.className = "product";
el.innerHTML = `
<img src="${p.img}" alt="${p.name}">
<h3>${p.name}</h3>
<p>₹${p.price}</p>
<button onclick="addToCart(${p.id})">Add to Cart</button>
`;
productList.appendChild(el);
});
}


function addToCart(id) {
if (!cart[id]) cart[id] = 0;
cart[id]++;
updateCart();
}


function updateCart() {
cartItems.innerHTML = "";
let total = 0;
let count = 0;
for (const id in cart) {
const product = products.find(p => p.id == id);
const qty = cart[id];
total += product.price * qty;
count += qty;
const item = document.createElement("div");
item.className = "cart-item";
item.innerHTML = `
<span>${product.name} x ${qty}</span>
<span>₹${product.price * qty}</span>
`;
cartItems.appendChild(item);
}
cartTotal.textContent = total;
cartCount.textContent = count;
}


function toggleCart() {
cartModal.classList.toggle("open");
checkoutForm.style.display = "none";
successMessage.style.display = "none";
}


function showCheckout() {
checkoutForm.style.display = "block";
}


function submitOrder(e) {
e.preventDefault();
cart = {};
updateCart();
checkoutForm.style.display = "none";
successMessage.style.display = "block";
}


document.querySelector(".cart-btn").addEventListener("click", toggleCart);


renderProducts();