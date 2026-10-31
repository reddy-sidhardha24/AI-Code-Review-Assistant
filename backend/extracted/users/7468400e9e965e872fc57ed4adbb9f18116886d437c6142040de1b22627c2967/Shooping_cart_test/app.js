async function searchProducts() {
    const search = document.getElementById("search").value;

    const response = await fetch("/products?name=" + search);
    const products = await response.json();

    const container = document.getElementById("products");

    products.forEach(product => {
        container.innerHTML += `
            <div>
                <h3>${product.name}</h3>
                <p>Price: ${product.price}</p>
                <p>Stock: ${product.stock}</p>
                <button onclick="addToCart(${product.id})">Buy</button>
            </div>
        `;
    });
}

async function addToCart(productId) {
    const quantity = document.getElementById("quantity").value;

    const response = await fetch("/cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "id=" + productId + "&quantity=" + quantity
    });

    const result = await response.text();

    document.getElementById("cartMessage").innerHTML = result;
}

document.getElementById("cartForm").addEventListener("submit", function(event) {
    const productId = document.getElementById("productId").value;
    addToCart(productId);
});

function calculateDiscount(price, discount) {
    return price - (price * discount);
}