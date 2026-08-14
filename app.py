from flask import Flask, render_template, redirect

app = Flask(__name__)

carrinho = []


produtos = [
    {
        "id": 1,
        "nome": "Camiseta",
        "preco": 50.00,
        "imagem": "camiseta.jpg"
    },
    {
        "id": 2,
        "nome": "Calça Jeans",
        "preco": 120.00,
        "imagem": "calca.jpg"
    },
    {
        "id": 3,
        "nome": "Moletom",
        "preco": 90.00,
        "imagem": "moletom.jpg"
    }
]


@app.route("/")
def inicio():
    return render_template("index.html", produtos=produtos)


@app.route("/comprar/<int:id>")
def comprar(id):

    for produto in produtos:

        if produto["id"] == id:

            encontrado = False

            for item in carrinho:

                if item["id"] == id:

                    item["quantidade"] += 1
                    encontrado = True
                    break

            if not encontrado:

                novo_item = produto.copy()
                novo_item["quantidade"] = 1

                carrinho.append(novo_item)

            break

    return redirect("/")


@app.route("/carrinho")
def ver_carrinho():

    total = 0

    for produto in carrinho:

        total += produto["preco"] * produto["quantidade"]

    return render_template(
        "carrinho.html",
        carrinho=carrinho,
        total=total
    )


if __name__ == "__main__":
    app.run(debug=True)