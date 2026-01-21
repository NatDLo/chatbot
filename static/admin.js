// This file contains JavaScript code for managing embeddings in the admin interface.
document.getElementById("emb-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const text = document.getElementById("text").value.trim();
    const meta = document.getElementById("meta").value;

    let metaObj;
    try {
        metaObj = meta ? JSON.parse(meta) : undefined;
    } catch (err) {
        alert("Meta debe ser un JSON válido");
        return;
    }

    const payload = { text: text, meta: metaObj };

    try {
        const res = await fetch("/admin/embeddings/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === "ok") {
            alert(`Embedding creado con ID ${data.id}`);
            document.getElementById("text").value = "";
            document.getElementById("meta").value = "";
            cargarEmbeddings();
        } else {
            alert("Error creando embedding");
        }
    } catch (err) {
        console.error(err);
        alert("Error conectando con el servidor");
    }
});

async function cargarEmbeddings() {
    try {
        const res = await fetch("/admin/embeddings/list");
        const embeddings = await res.json();
        const ul = document.getElementById("emb-list");
        ul.innerHTML = "";
        embeddings.forEach(e => {
            const li = document.createElement("li");
            li.textContent = `${e.id}: ${e.text} ${e.meta ? JSON.stringify(e.meta) : ""}`;
            ul.appendChild(li);
        });
    } catch (err) {
        console.error(err);
        alert("Error cargando embeddings");
    }
}

document.getElementById("refresh").addEventListener("click", cargarEmbeddings);
window.addEventListener("load", cargarEmbeddings);
